"""
Conversation Context Service

Tracks what the user is building during the conversation to enable
proactive suggestions and intelligent optimizations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re


class ConversationContext:
    """
    Tracks conversation context for proactive pipeline building
    """

    def __init__(self):
        self.context = {
            "pipeline_intent": None,  # "copy", "transform", "real-time", etc.
            "source": {
                "type": None,  # "SQL Server", "Oracle", "Salesforce", etc.
                "details": {}
            },
            "destination": {
                "type": None,  # "Lakehouse", "Warehouse", "KQL Database", etc.
                "details": {}
            },
            "requirements": {
                "frequency": None,  # "hourly", "daily", "real-time", etc.
                "volume": None,  # "small", "medium", "large", "> 100GB", etc.
                "transformations": [],
                "business_use_case": None
            },
            "current_stage": "initial",  # "initial", "gathering_requirements", "suggesting", "building", "ready_to_deploy"
            "suggestions_made": [],
            "user_preferences": {},
            "conversation_history": [],
            "pending_confirmation": None,  # Action waiting for confirmation: "create_shortcut", etc.
            "confirmation_data": {},  # Data needed to execute the pending action
            "shortcuts": {  # Information about OneLake shortcuts
                "bronze_path": None,  # e.g., "Files/bronze"
                "silver_path": None,  # e.g., "Files/silver"
                "lakehouse_id": None,
                "lakehouse_name": None,
                "storage_account": None
            }
        }

    def extract_intent_from_message(self, message: str) -> Dict[str, Any]:
        """
        Extract pipeline building intent from user message

        Returns detected entities and intent
        """
        message_lower = message.lower()
        extracted = {
            "intent_detected": False,
            "source_detected": None,
            "destination_detected": None,
            "keywords": []
        }

        # Detect pipeline building intent
        pipeline_keywords = [
            "pipeline", "copy", "move", "transfer", "ingest", "load",
            "extract", "migrate", "sync", "import", "export"
        ]

        for keyword in pipeline_keywords:
            if keyword in message_lower:
                extracted["intent_detected"] = True
                extracted["keywords"].append(keyword)
                break

        # Detect source systems
        source_systems = {
            "sql server": "SQL Server",
            "oracle": "Oracle",
            "mysql": "MySQL",
            "postgresql": "PostgreSQL",
            "salesforce": "Salesforce",
            "dynamics": "Dynamics 365",
            "rest api": "REST API",
            "api": "REST API",
            "csv": "CSV Files",
            "excel": "Excel",
            "blob": "Azure Blob Storage",
            "azure blob": "Azure Blob Storage",
            "s3": "AWS S3",
            "adls": "ADLS Gen2",
            "cosmosdb": "Cosmos DB",
            "snowflake": "Snowflake",
            "databricks": "Databricks"
        }

        for keyword, system in source_systems.items():
            if keyword in message_lower:
                extracted["source_detected"] = system
                break

        # Detect destination systems
        destination_systems = {
            "lakehouse": "Lakehouse",
            "warehouse": "Warehouse",
            "data warehouse": "Warehouse",
            "kql database": "KQL Database",
            "kql": "KQL Database",
            "eventhouse": "Eventhouse",
            "onelake": "OneLake",
            "power bi": "Power BI Dataset",
            "dataset": "Power BI Dataset"
        }

        for keyword, system in destination_systems.items():
            if keyword in message_lower:
                extracted["destination_detected"] = system
                break

        # Detect frequency
        frequency_patterns = {
            "real-time": ["real-time", "realtime", "streaming", "continuous"],
            "hourly": ["hourly", "every hour", "per hour"],
            "daily": ["daily", "every day", "once a day", "nightly"],
            "weekly": ["weekly", "every week"],
            "monthly": ["monthly", "every month"]
        }

        for freq, patterns in frequency_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    extracted["frequency"] = freq
                    break

        return extracted

    def update_context(self, user_message: str, agent_response: str = None):
        """
        Update context based on conversation
        """
        # Extract information from user message
        extracted = self.extract_intent_from_message(user_message)

        # Update context
        if extracted["intent_detected"]:
            self.context["pipeline_intent"] = "building_pipeline"

        if extracted["source_detected"]:
            self.context["source"]["type"] = extracted["source_detected"]

        if extracted["destination_detected"]:
            self.context["destination"]["type"] = extracted["destination_detected"]

        if "frequency" in extracted:
            self.context["requirements"]["frequency"] = extracted["frequency"]

        # Add to conversation history
        self.context["conversation_history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_message": user_message,
            "agent_response": agent_response,
            "extracted": extracted
        })

        # Update stage
        if self.context["source"]["type"] and self.context["destination"]["type"]:
            self.context["current_stage"] = "suggesting"
        elif extracted["intent_detected"]:
            self.context["current_stage"] = "gathering_requirements"

    def get_summary(self) -> str:
        """
        Get a summary of what the user is trying to build
        """
        parts = []

        if self.context["source"]["type"]:
            parts.append(f"Source: {self.context['source']['type']}")

        if self.context["destination"]["type"]:
            parts.append(f"Destination: {self.context['destination']['type']}")

        if self.context["requirements"]["frequency"]:
            parts.append(f"Frequency: {self.context['requirements']['frequency']}")

        if self.context["requirements"]["volume"]:
            parts.append(f"Volume: {self.context['requirements']['volume']}")

        return " | ".join(parts) if parts else "No pipeline context yet"

    def should_search_for_best_practices(self) -> Optional[str]:
        """
        Determine if we should proactively search for best practices

        Returns search query if we should search, None otherwise
        """
        source = self.context["source"]["type"]
        destination = self.context["destination"]["type"]

        # If we know source and destination, search for best practices
        if source and destination:
            return f"Microsoft Fabric {source} to {destination} best practices 2025"

        # If we know source, search for latest connector info
        elif source:
            return f"Microsoft Fabric {source} connector latest updates 2025"

        # If we know destination, search for optimization patterns
        elif destination:
            return f"Microsoft Fabric {destination} optimization patterns 2025"

        return None

    def get_context_for_agent(self) -> str:
        """
        Format context as additional system message for the agent
        """
        if not self.context["source"]["type"] and not self.context["destination"]["type"] and not self.has_shortcuts():
            return ""

        context_msg = "\n\n## 📋 CURRENT PIPELINE CONTEXT\n"
        context_msg += f"User is building: {self.get_summary()}\n"

        if self.context["current_stage"] == "suggesting":
            context_msg += "\n⚡ ACTION: Proactively search for best practices and suggest optimizations!\n"

        # Add shortcut information if available
        if self.has_shortcuts():
            context_msg += "\n\n## 🔗 LAKEHOUSE SHORTCUTS AVAILABLE\n"
            context_msg += f"Lakehouse: {self.context['shortcuts']['lakehouse_name']}\n"
            if self.context['shortcuts']['bronze_path']:
                context_msg += f"  • Bronze data: {self.context['shortcuts']['bronze_path']}\n"
            if self.context['shortcuts']['silver_path']:
                context_msg += f"  • Silver data: {self.context['shortcuts']['silver_path']}\n"
            context_msg += f"Storage Account: {self.context['shortcuts']['storage_account']}\n"
            context_msg += "\n⚠️ IMPORTANT: When generating pipelines, use these lakehouse paths directly.\n"
            context_msg += "DO NOT create blob storage connections. Use LakehouseFiles as source type.\n"

        return context_msg

    def is_ready_for_deployment(self) -> bool:
        """
        Check if user has provided enough information to build the pipeline
        """
        return (
            self.context["source"]["type"] is not None and
            self.context["destination"]["type"] is not None
        )

    def add_suggestion(self, suggestion: Dict[str, Any]):
        """
        Track suggestions made to the user
        """
        self.context["suggestions_made"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "suggestion": suggestion
        })

    def set_pending_confirmation(self, action: str, data: Dict[str, Any]):
        """
        Set a pending action that needs user confirmation

        Args:
            action: Action type (e.g., "create_shortcut")
            data: Data needed to execute the action
        """
        self.context["pending_confirmation"] = action
        self.context["confirmation_data"] = data

    def get_pending_confirmation(self) -> Optional[Dict[str, Any]]:
        """
        Get pending confirmation details

        Returns:
            Dict with 'action' and 'data' or None if no pending confirmation
        """
        if self.context["pending_confirmation"]:
            return {
                "action": self.context["pending_confirmation"],
                "data": self.context["confirmation_data"]
            }
        return None

    def clear_pending_confirmation(self):
        """
        Clear pending confirmation after user responds
        """
        self.context["pending_confirmation"] = None
        self.context["confirmation_data"] = {}

    def is_user_confirming(self, message: str) -> bool:
        """
        Check if user message is confirming the pending action

        Returns:
            True if user is saying yes/confirmed, False otherwise
        """
        message_lower = message.lower().strip()

        # Positive confirmations
        positive = ["yes", "yeah", "yep", "sure", "ok", "okay", "proceed", "go ahead",
                    "confirm", "confirmed", "do it", "please", "👍", "✓", "✅"]

        return any(word in message_lower for word in positive)

    def set_shortcuts(self, shortcuts_info: Dict[str, Any]):
        """
        Store shortcut information in context

        Args:
            shortcuts_info: Dict containing shortcut details
                - lakehouse_name: Name of lakehouse
                - lakehouse_id: ID of lakehouse
                - storage_account: Storage account name
                - shortcuts: List of shortcuts with name, container, path
        """
        self.context["shortcuts"]["lakehouse_name"] = shortcuts_info.get("lakehouse_name")
        self.context["shortcuts"]["lakehouse_id"] = shortcuts_info.get("lakehouse_id")
        self.context["shortcuts"]["storage_account"] = shortcuts_info.get("storage_account")

        # Extract bronze and silver paths from shortcuts list
        for shortcut in shortcuts_info.get("shortcuts", []):
            if "bronze" in shortcut.get("name", "").lower():
                self.context["shortcuts"]["bronze_path"] = shortcut.get("path", "Files/bronze")
            elif "silver" in shortcut.get("name", "").lower():
                self.context["shortcuts"]["silver_path"] = shortcut.get("path", "Files/silver")

    def has_shortcuts(self) -> bool:
        """
        Check if shortcut information is available

        Returns:
            True if shortcuts are configured, False otherwise
        """
        return (
            self.context["shortcuts"]["bronze_path"] is not None or
            self.context["shortcuts"]["silver_path"] is not None
        )

    def get_shortcuts(self) -> Dict[str, Any]:
        """
        Get shortcut information

        Returns:
            Dict with shortcut details
        """
        return self.context["shortcuts"]


class ConversationContextManager:
    """
    Manages conversation contexts for multiple users/sessions
    """

    def __init__(self):
        self.contexts: Dict[str, ConversationContext] = {}

    def get_context(self, session_id: str) -> ConversationContext:
        """
        Get or create conversation context for a session
        """
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext()

        return self.contexts[session_id]

    def clear_context(self, session_id: str):
        """
        Clear conversation context for a session
        """
        if session_id in self.contexts:
            del self.contexts[session_id]


# Global context manager
context_manager = ConversationContextManager()
