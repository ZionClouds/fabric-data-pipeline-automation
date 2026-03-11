"""
Base Agent Class

All specialized agents inherit from this base class.
Provides common functionality for AI interaction and state management.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
import json

from .state_manager import PipelineState

logger = logging.getLogger(__name__)


class AgentResponse:
    """Standard response format from agents"""

    def __init__(
        self,
        message: str,
        questions: Optional[List[str]] = None,
        insights: Optional[Dict[str, Any]] = None,
        recommendations: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        state_updates: Optional[Dict[str, Any]] = None,
        next_agent: Optional[str] = None,
        is_complete: bool = False,
    ):
        self.message = message
        self.questions = questions or []
        self.insights = insights or {}
        self.recommendations = recommendations or []
        self.warnings = warnings or []
        self.state_updates = state_updates or {}
        self.next_agent = next_agent
        self.is_complete = is_complete

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "questions": self.questions,
            "insights": self.insights,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "state_updates": self.state_updates,
            "next_agent": self.next_agent,
            "is_complete": self.is_complete,
        }


class BaseAgent(ABC):
    """
    Base class for all pipeline architect agents.

    Each agent has:
    - A specific role and expertise
    - Required information checklist
    - Thinking rules for inferences
    - Methods to process user messages
    """

    def __init__(self, name: str, role: str, ai_service=None):
        self.name = name
        self.role = role
        self.ai_service = ai_service
        self.logger = logging.getLogger(f"agent.{name}")

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt defining agent's expertise and behavior"""
        pass

    @property
    @abstractmethod
    def required_info(self) -> List[str]:
        """List of information this agent needs to do its job"""
        pass

    @property
    @abstractmethod
    def thinking_rules(self) -> Dict[str, Any]:
        """Rules for making inferences from user input"""
        pass

    @abstractmethod
    async def process(self, state: PipelineState, user_message: str) -> AgentResponse:
        """Process user message and return response"""
        pass

    def get_missing_info(self, state: PipelineState) -> List[str]:
        """Determine what information is still needed"""
        missing = []
        for info in self.required_info:
            if not self._has_info(state, info):
                missing.append(info)
        return missing

    def _has_info(self, state: PipelineState, info_key: str) -> bool:
        """Check if specific information exists in state"""
        # Map info keys to state attributes
        info_map = {
            "source_type": lambda s: s.source.type is not None,
            "source_location": lambda s: s.source.location is not None,
            "source_objects": lambda s: len(s.source.objects) > 0,
            "source_volume": lambda s: s.source.volume_gb is not None,
            "use_case": lambda s: s.business.use_case is not None,
            "consumers": lambda s: len(s.business.consumers) > 0,
            "frequency": lambda s: s.operations.frequency is not None,
            "destination_type": lambda s: s.destination.type is not None,
            "pii_status": lambda s: s.transformations.pii_handling is not None,
        }

        checker = info_map.get(info_key)
        if checker:
            return checker(state)
        return False

    def apply_thinking_rules(self, state: PipelineState, message: str) -> Dict[str, Any]:
        """Apply thinking rules to infer information"""
        inferences = {}
        message_lower = message.lower()

        for trigger, inference in self.thinking_rules.items():
            if trigger.lower() in message_lower:
                inferences[trigger] = inference
                self.logger.info(f"Inference triggered by '{trigger}': {inference}")

        return inferences

    def format_context_for_ai(self, state: PipelineState) -> str:
        """Format current state as context for AI"""
        context_parts = [
            "## Current Pipeline State",
            f"Stage: {state.stage.value}",
            "",
            "### Known Information:",
        ]

        # Add source info
        if state.source.type:
            context_parts.append(f"- Source: {state.source.type} ({state.source.location or 'location unknown'})")
        if state.source.objects:
            context_parts.append(f"- Objects: {', '.join(state.source.objects[:5])}{'...' if len(state.source.objects) > 5 else ''}")
        if state.source.volume_gb:
            context_parts.append(f"- Volume: ~{state.source.volume_gb}GB")

        # Add business context
        if state.business.use_case:
            context_parts.append(f"- Use case: {state.business.use_case}")
        if state.business.consumers:
            context_parts.append(f"- Consumers: {', '.join(state.business.consumers)}")
        if state.business.pii_likely:
            context_parts.append("- PII: Likely present in data")

        # Add operational info
        if state.operations.frequency:
            context_parts.append(f"- Frequency: {state.operations.frequency}")

        # Add missing info
        missing = state.get_missing_requirements()
        if missing:
            context_parts.append("")
            context_parts.append("### Still Needed:")
            for item in missing:
                context_parts.append(f"- {item.replace('_', ' ').title()}")

        return "\n".join(context_parts)

    async def call_ai(self, messages: List[Dict[str, str]], context: str = "") -> str:
        """Call the AI service with messages"""
        if not self.ai_service:
            raise ValueError("AI service not configured for this agent")

        # Add system prompt
        full_messages = [
            {"role": "system", "content": self.system_prompt + "\n\n" + context}
        ] + messages

        try:
            response = await self.ai_service.chat(
                messages=full_messages,
                context=None
            )
            return response.get("content", "")
        except Exception as e:
            self.logger.error(f"AI call failed: {e}")
            raise

    def generate_smart_question(self, missing_info: List[str], state: PipelineState) -> str:
        """Generate intelligent questions based on what's missing and what we know"""
        if not missing_info:
            return ""

        # Group related questions
        questions = []

        # Prioritize questions based on what we know
        if "source_type" in missing_info:
            questions.append("What type of data source are you working with? (e.g., PostgreSQL, SQL Server, Azure Blob, SharePoint)")

        elif "source_location" in missing_info and state.source.type:
            questions.append(f"Is your {state.source.type} database hosted in the cloud or on-premise?")

        elif "source_objects" in missing_info and state.source.type:
            if state.source.type in ["postgresql", "sql_server", "mysql", "oracle"]:
                questions.append("Which tables do you want to migrate? (all tables, or list specific ones)")
            elif state.source.type == "blob_storage":
                questions.append("Which container and folder path contains your files?")
            elif state.source.type == "sharepoint":
                questions.append("Which SharePoint site and list do you want to sync?")

        elif "use_case" in missing_info:
            questions.append("What will this data be used for? (e.g., Power BI dashboards, machine learning, application data)")

        elif "frequency" in missing_info:
            questions.append("Is this a one-time migration or do you need ongoing sync? If ongoing, how often?")

        elif "destination_type" in missing_info:
            questions.append("Where should the data be stored - Lakehouse Tables or Files?")

        # Combine up to 2-3 related questions
        if len(questions) > 3:
            questions = questions[:3]

        return " ".join(questions)
