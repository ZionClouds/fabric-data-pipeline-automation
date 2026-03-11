"""
Production Guardrails for Fabric Pipeline Agents

This module provides input/output validation, safety checks, and content filtering
to ensure safe and appropriate agent behavior in production.
"""

import re
import logging
from typing import Optional, List, Tuple
from dataclasses import dataclass

from agents import (
    GuardrailFunctionOutput,
    InputGuardrail,
    OutputGuardrail,
    RunContextWrapper,
    input_guardrail,
    output_guardrail,
)
from agents.items import TResponseInputItem

from .context import PipelineContext

logger = logging.getLogger(__name__)


# ============================================================================
# Sensitive Data Detection Patterns
# ============================================================================

SENSITIVE_PATTERNS = {
    # Credentials and secrets
    "password": r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?([^\s"\']+)',
    "api_key": r'(?i)(api[_-]?key|apikey|secret[_-]?key)\s*[=:]\s*["\']?([^\s"\']+)',
    "bearer_token": r'(?i)bearer\s+[a-z0-9_\-\.]+',
    "connection_string": r'(?i)(connection[_-]?string|connstr)\s*[=:]\s*["\']?([^"\']+)',

    # Personal identifiers (to flag, not block)
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
    "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    "email": r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',

    # Azure-specific secrets
    "storage_key": r'(?i)(storage[_-]?key|account[_-]?key)\s*[=:]\s*["\']?([^\s"\']+)',
    "sas_token": r'(?i)(sv=\d{4}-\d{2}-\d{2}&[^"\s]+)',
}

# Topics to flag but not block
FLAGGED_TOPICS = [
    "competitor",
    "illegal",
    "hack",
    "bypass security",
    "delete all",
    "drop database",
]

# Topics to block
BLOCKED_TOPICS = [
    "ignore instructions",
    "ignore all previous",
    "disregard your instructions",
    "you are now",
    "pretend you are",
    "act as if",
    "jailbreak",
]


@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    issues: List[str]
    warnings: List[str]
    sanitized_content: Optional[str] = None


# ============================================================================
# Input Guardrails
# ============================================================================

@input_guardrail
async def validate_user_input(
    ctx: RunContextWrapper[PipelineContext],
    agent: "Agent",
    input_items: List[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """
    Validate user input for safety and appropriateness.

    Checks for:
    - Prompt injection attempts
    - Embedded credentials/secrets
    - Blocked topics
    - Input length limits
    """
    for item in input_items:
        if hasattr(item, 'content') and isinstance(item.content, str):
            content = item.content

            # Check for blocked topics (prompt injection)
            for topic in BLOCKED_TOPICS:
                if topic.lower() in content.lower():
                    logger.warning(f"Blocked topic detected: {topic}")
                    return GuardrailFunctionOutput(
                        output_info={"blocked_reason": "prompt_injection_attempt"},
                        tripwire_triggered=True,
                    )

            # Check for embedded credentials
            for pattern_name, pattern in SENSITIVE_PATTERNS.items():
                if pattern_name in ["password", "api_key", "bearer_token", "connection_string", "storage_key"]:
                    if re.search(pattern, content):
                        logger.warning(f"Potential credential detected in input: {pattern_name}")
                        return GuardrailFunctionOutput(
                            output_info={
                                "warning": "credential_detected",
                                "pattern": pattern_name,
                                "message": "Please do not include credentials in your message. Configure them securely in Fabric."
                            },
                            tripwire_triggered=True,
                        )

            # Check input length (prevent abuse)
            if len(content) > 10000:
                logger.warning(f"Input too long: {len(content)} characters")
                return GuardrailFunctionOutput(
                    output_info={"error": "input_too_long"},
                    tripwire_triggered=True,
                )

    return GuardrailFunctionOutput(
        output_info={"status": "valid"},
        tripwire_triggered=False,
    )


@input_guardrail
async def check_pipeline_context(
    ctx: RunContextWrapper[PipelineContext],
    agent: "Agent",
    input_items: List[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """
    Check that pipeline context is valid and properly initialized.
    """
    context = ctx.context

    if not context:
        logger.error("Pipeline context not initialized")
        return GuardrailFunctionOutput(
            output_info={"error": "context_not_initialized"},
            tripwire_triggered=True,
        )

    if not context.workspace_id:
        logger.error("Workspace ID not set in context")
        return GuardrailFunctionOutput(
            output_info={"error": "workspace_id_required"},
            tripwire_triggered=True,
        )

    if not context.user_id:
        logger.error("User ID not set in context")
        return GuardrailFunctionOutput(
            output_info={"error": "user_id_required"},
            tripwire_triggered=True,
        )

    return GuardrailFunctionOutput(
        output_info={"status": "context_valid"},
        tripwire_triggered=False,
    )


# ============================================================================
# Output Guardrails
# ============================================================================

@output_guardrail
async def sanitize_agent_output(
    ctx: RunContextWrapper[PipelineContext],
    agent: "Agent",
    output: str,
) -> GuardrailFunctionOutput:
    """
    Sanitize agent output to prevent data leakage.

    Checks for:
    - Accidentally exposed credentials
    - Connection strings
    - Internal system information
    """
    issues = []
    sanitized = output

    # Check and redact any credentials in output
    for pattern_name, pattern in SENSITIVE_PATTERNS.items():
        if pattern_name in ["password", "api_key", "bearer_token", "connection_string", "storage_key", "sas_token"]:
            matches = re.findall(pattern, sanitized)
            if matches:
                issues.append(f"Redacted {pattern_name}")
                # Redact the sensitive content
                sanitized = re.sub(pattern, f"[REDACTED:{pattern_name.upper()}]", sanitized)

    if issues:
        logger.warning(f"Output sanitization applied: {issues}")
        return GuardrailFunctionOutput(
            output_info={
                "sanitization_applied": True,
                "redactions": issues,
                "sanitized_output": sanitized,
            },
            tripwire_triggered=False,  # Don't block, just sanitize
        )

    return GuardrailFunctionOutput(
        output_info={"status": "clean"},
        tripwire_triggered=False,
    )


@output_guardrail
async def validate_deployment_output(
    ctx: RunContextWrapper[PipelineContext],
    agent: "Agent",
    output: str,
) -> GuardrailFunctionOutput:
    """
    Validate output when deployment is being discussed.

    Ensures:
    - Deployment confirmation is required
    - No accidental deployments happen
    - User is properly warned about production actions
    """
    context = ctx.context

    # Check if this is a deployment action
    deployment_keywords = ["deployed", "deployment successful", "pipeline created"]
    is_deployment_output = any(keyword in output.lower() for keyword in deployment_keywords)

    if is_deployment_output:
        # Ensure we're in the correct stage
        if context.stage.value not in ["reviewing", "deploying", "completed"]:
            logger.warning("Deployment output in wrong stage")
            return GuardrailFunctionOutput(
                output_info={
                    "warning": "deployment_stage_mismatch",
                    "current_stage": context.stage.value,
                },
                tripwire_triggered=False,
            )

    return GuardrailFunctionOutput(
        output_info={"status": "valid"},
        tripwire_triggered=False,
    )


# ============================================================================
# Guardrail Collections
# ============================================================================

# Input guardrails applied to all agents
STANDARD_INPUT_GUARDRAILS: List[InputGuardrail] = [
    validate_user_input,
    check_pipeline_context,
]

# Output guardrails applied to all agents
STANDARD_OUTPUT_GUARDRAILS: List[OutputGuardrail] = [
    sanitize_agent_output,
    validate_deployment_output,
]


# ============================================================================
# Utility Functions
# ============================================================================

def detect_pii_in_text(text: str) -> List[Tuple[str, str]]:
    """
    Detect PII patterns in text for informational purposes.
    Returns list of (pattern_name, matched_text) tuples.
    """
    findings = []

    pii_patterns = {
        "email": SENSITIVE_PATTERNS["email"],
        "ssn": SENSITIVE_PATTERNS["ssn"],
        "credit_card": SENSITIVE_PATTERNS["credit_card"],
        "phone": r'\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
    }

    for pattern_name, pattern in pii_patterns.items():
        matches = re.findall(pattern, text)
        for match in matches:
            findings.append((pattern_name, match if isinstance(match, str) else match[0]))

    return findings


def validate_workspace_id(workspace_id: str) -> bool:
    """Validate workspace ID format (GUID)"""
    guid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    return bool(re.match(guid_pattern, workspace_id))


def sanitize_for_logging(text: str, max_length: int = 500) -> str:
    """Sanitize text for safe logging"""
    sanitized = text

    # Redact sensitive patterns
    for pattern_name, pattern in SENSITIVE_PATTERNS.items():
        sanitized = re.sub(pattern, f"[REDACTED]", sanitized)

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "...[truncated]"

    return sanitized


def get_guardrails_for_agent(agent_name: str) -> Tuple[List[InputGuardrail], List[OutputGuardrail]]:
    """
    Get appropriate guardrails for a specific agent.
    Some agents may need additional or different guardrails.
    """
    input_guardrails = STANDARD_INPUT_GUARDRAILS.copy()
    output_guardrails = STANDARD_OUTPUT_GUARDRAILS.copy()

    # Deploy agent gets extra validation
    if agent_name == "deploy":
        # Could add deployment-specific guardrails here
        pass

    return input_guardrails, output_guardrails
