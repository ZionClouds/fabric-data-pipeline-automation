"""
Discovery Agent

The Business Analyst of the pipeline architect team.
Understands the WHY before diving into technical details.
"""

from typing import Dict, Any, List
import logging

from .base_agent import BaseAgent, AgentResponse
from .state_manager import PipelineState

logger = logging.getLogger(__name__)


class DiscoveryAgent(BaseAgent):
    """
    Discovery Agent - Understands business context and use case.

    Responsibilities:
    - Understand what the user is trying to achieve
    - Identify the business use case
    - Detect potential concerns (PII, compliance, scale)
    - Ask strategic questions, not just data collection
    """

    def __init__(self, ai_service=None):
        super().__init__(
            name="discovery",
            role="Business Analyst",
            ai_service=ai_service
        )

    @property
    def system_prompt(self) -> str:
        return """You are the Discovery Agent - a Business Analyst for data pipeline design.

## YOUR ROLE
You understand the BUSINESS CONTEXT before technical details. You ask WHY, not just WHAT.

## YOUR THINKING PROCESS
Before responding, THINK about:
1. What is the user trying to ACHIEVE? (not just what data they have)
2. Who will USE this data? (the end consumers matter for design)
3. What PROBLEMS might arise? (PII, scale, compliance)
4. What are they NOT telling me that I should ask?

## CONVERSATION STYLE
- Be warm and professional, like a senior consultant
- Ask ONE focused question at a time (maybe 2 if related)
- Acknowledge what you understood before asking more
- Make intelligent inferences and confirm them

## SMART INFERENCES
Make these inferences from user's words:
- "customer data" / "employee data" / "patient data" → PII likely, suggest masking
- "Power BI" / "dashboard" / "report" → Analytics use case, needs aggregated layer
- "machine learning" / "ML" / "data science" → Needs feature engineering
- "migrate" / "one-time" → Different from ongoing sync
- "real-time" → Streaming architecture needed
- "on-premise" → Gateway will be required

## WHAT YOU NEED TO LEARN
1. Source system type (but ask about use case first!)
2. Business purpose / use case
3. Who consumes the data
4. Data sensitivity (PII/PHI)
5. Frequency needs
6. Scale/volume

## EXAMPLE GOOD RESPONSES

User: "I need to move data from PostgreSQL to Fabric"
You: "I'll help you build that pipeline! Before we dive into the technical details, what will this data be used for once it's in Fabric? (For example: Power BI dashboards, data science, or as a data lake for multiple uses)"

User: "We have customer orders that need to go to Power BI"
You: "Got it - customer order data for Power BI dashboards. Since this involves customer data, I want to make sure we handle it properly:
1. Does this include personal information like names, emails, or addresses? (I'll plan for PII protection if so)
2. How often does this data change - are we looking at daily updates or real-time?"

## OUTPUT FORMAT
Always respond conversationally. After gathering enough info, summarize what you learned.
DO NOT output JSON or technical specifications - that's for other agents."""

    @property
    def required_info(self) -> List[str]:
        return [
            "source_type",
            "use_case",
            "consumers",
            "frequency",
        ]

    @property
    def thinking_rules(self) -> Dict[str, Any]:
        return {
            "customer": {"pii_likely": True, "suggest": "PII masking"},
            "employee": {"pii_likely": True, "suggest": "PII masking", "compliance": "HR policies"},
            "patient": {"pii_likely": True, "compliance": "HIPAA"},
            "personal": {"pii_likely": True},
            "power bi": {"use_case": "analytics", "needs": "aggregated_layer"},
            "dashboard": {"use_case": "analytics", "needs": "aggregated_layer"},
            "report": {"use_case": "analytics"},
            "machine learning": {"use_case": "ml", "needs": "feature_engineering"},
            "ml model": {"use_case": "ml", "needs": "feature_engineering"},
            "data science": {"use_case": "ml", "consumers": ["data_scientists"]},
            "real-time": {"architecture": "streaming", "component": "eventstream"},
            "realtime": {"architecture": "streaming", "component": "eventstream"},
            "migrate": {"frequency": "one_time"},
            "migration": {"frequency": "one_time"},
            "one-time": {"frequency": "one_time"},
            "daily": {"frequency": "daily"},
            "hourly": {"frequency": "hourly"},
            "on-premise": {"location": "on_premise", "needs": "gateway"},
            "on premise": {"location": "on_premise", "needs": "gateway"},
        }

    async def process(self, state: PipelineState, user_message: str) -> AgentResponse:
        """Process user message and gather business context"""

        # Apply thinking rules to extract inferences
        inferences = self.apply_thinking_rules(state, user_message)

        # Update state based on inferences
        state_updates = {}
        for trigger, inference in inferences.items():
            if "pii_likely" in inference:
                state.business.pii_likely = True
                state_updates["pii_likely"] = True

            if "use_case" in inference:
                state.business.use_case = inference["use_case"]
                state_updates["use_case"] = inference["use_case"]

            if "frequency" in inference:
                state.operations.frequency = inference["frequency"]
                state_updates["frequency"] = inference["frequency"]

            if "location" in inference:
                state.source.location = inference["location"]
                state_updates["location"] = inference["location"]

        # Also update state from direct message parsing
        state.update_from_message(user_message)

        # Determine what we still need
        missing = self.get_missing_info(state)

        # Build insights from what we learned
        insights = {
            "source_detected": state.source.type,
            "use_case_detected": state.business.use_case,
            "pii_likely": state.business.pii_likely,
            "location": state.source.location,
            "frequency": state.operations.frequency,
            "inferences_made": list(inferences.keys()),
        }

        # Generate recommendations based on what we know
        recommendations = []
        warnings = []

        if state.business.pii_likely:
            recommendations.append("PII masking should be added to protect sensitive data")

        if state.source.location == "on_premise":
            warnings.append("On-premises data gateway will be required")

        if state.business.use_case == "analytics":
            recommendations.append("Medallion architecture recommended for analytics use case")

        # Determine if we have enough info to move forward
        is_complete = len(missing) == 0 or (
            state.source.type is not None and
            state.business.use_case is not None and
            state.operations.frequency is not None
        )

        # Generate response
        if is_complete:
            message = self._generate_summary(state, recommendations, warnings)
            next_agent = "orchestrator"  # Ready for specialist analysis
        else:
            message = await self._generate_question(state, missing, user_message)
            next_agent = None  # Stay in discovery

        return AgentResponse(
            message=message,
            questions=missing if not is_complete else [],
            insights=insights,
            recommendations=recommendations,
            warnings=warnings,
            state_updates=state_updates,
            next_agent=next_agent,
            is_complete=is_complete,
        )

    async def _generate_question(self, state: PipelineState, missing: List[str], user_message: str) -> str:
        """Generate intelligent follow-up question"""

        # Build context for AI
        context = self.format_context_for_ai(state)

        # Create prompt for AI
        messages = [
            {
                "role": "user",
                "content": f"""The user said: "{user_message}"

{context}

Based on what I know and what's missing, generate a natural, conversational response that:
1. Acknowledges what I understood from their message
2. Asks ONE focused question about the most important missing information
3. If I detected PII likelihood, mentions I'll plan for data protection

Missing information: {', '.join(missing)}

Respond conversationally, not as a list."""
            }
        ]

        if self.ai_service:
            try:
                response = await self.call_ai(messages, context)
                return response
            except Exception as e:
                logger.error(f"AI call failed: {e}")

        # Fallback to template-based question
        return self.generate_smart_question(missing, state)

    def _generate_summary(self, state: PipelineState, recommendations: List[str], warnings: List[str]) -> str:
        """Generate summary of gathered requirements"""

        summary_parts = ["Great! I have a good understanding of your requirements:\n"]

        # Source
        if state.source.type:
            loc = f" ({state.source.location})" if state.source.location else ""
            summary_parts.append(f"**Source**: {state.source.type.replace('_', ' ').title()}{loc}")

        # Use case
        if state.business.use_case:
            summary_parts.append(f"**Use Case**: {state.business.use_case.replace('_', ' ').title()}")

        # Consumers
        if state.business.consumers:
            summary_parts.append(f"**Data Consumers**: {', '.join(state.business.consumers)}")

        # Frequency
        if state.operations.frequency:
            freq_display = state.operations.frequency.replace('_', ' ').title()
            if state.operations.frequency == "manual":
                freq_display = "One-time migration"
            summary_parts.append(f"**Frequency**: {freq_display}")

        # PII
        if state.business.pii_likely:
            summary_parts.append("**Data Sensitivity**: Contains personal data (PII protection planned)")

        # Warnings
        if warnings:
            summary_parts.append("\n**Important Notes:**")
            for warning in warnings:
                summary_parts.append(f"- {warning}")

        # Recommendations preview
        if recommendations:
            summary_parts.append("\n**Initial Recommendations:**")
            for rec in recommendations:
                summary_parts.append(f"- {rec}")

        summary_parts.append("\nLet me analyze this further and design the optimal pipeline architecture...")

        return "\n".join(summary_parts)
