"""
Pipeline Requirements State Manager

Tracks all information needed to build a complete data pipeline.
Each agent reads from and writes to this shared state.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    """Pipeline design stages"""
    INITIAL = "initial"
    DISCOVERY = "discovery"
    ANALYZING = "analyzing"
    DESIGNING = "designing"
    REVIEWING = "reviewing"
    DEPLOYING = "deploying"
    COMPLETED = "completed"


@dataclass
class SourceInfo:
    """Source system information"""
    type: Optional[str] = None  # postgresql, sql_server, blob, sharepoint, rest_api
    location: Optional[str] = None  # cloud, on_premise
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    objects: List[str] = field(default_factory=list)  # tables, files, endpoints
    volume_gb: Optional[float] = None
    schema: Dict[str, Any] = field(default_factory=dict)
    change_pattern: Optional[str] = None  # static, insert_only, updates, deletes
    gateway_available: Optional[bool] = None
    gateway_id: Optional[str] = None

    def is_complete(self) -> bool:
        """Check if we have minimum required source info"""
        return all([self.type, self.location])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "location": self.location,
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "objects": self.objects,
            "volume_gb": self.volume_gb,
            "change_pattern": self.change_pattern,
            "gateway_available": self.gateway_available,
        }


@dataclass
class BusinessContext:
    """Business context and use case"""
    use_case: Optional[str] = None  # analytics, ml, operational, archive
    consumers: List[str] = field(default_factory=list)  # power_bi, data_scientists, applications
    sla_hours: Optional[int] = None
    criticality: Optional[str] = None  # poc, development, production
    deadline: Optional[str] = None
    pii_likely: bool = False
    compliance_requirements: List[str] = field(default_factory=list)

    def is_complete(self) -> bool:
        """Check if we have minimum required business context"""
        return self.use_case is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "use_case": self.use_case,
            "consumers": self.consumers,
            "sla_hours": self.sla_hours,
            "criticality": self.criticality,
            "pii_likely": self.pii_likely,
        }


@dataclass
class TransformationNeeds:
    """Transformation requirements"""
    needed: Optional[bool] = None
    cleaning: List[str] = field(default_factory=list)  # dedupe, null_handling, format_fixes
    enrichment: List[str] = field(default_factory=list)  # joins, lookups
    aggregations: List[str] = field(default_factory=list)  # sums, counts, averages
    pii_handling: Optional[str] = None  # none, detect, mask, encrypt
    pii_columns: List[str] = field(default_factory=list)
    custom_logic: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "needed": self.needed,
            "cleaning": self.cleaning,
            "enrichment": self.enrichment,
            "aggregations": self.aggregations,
            "pii_handling": self.pii_handling,
            "pii_columns": self.pii_columns,
        }


@dataclass
class DestinationConfig:
    """Destination configuration"""
    type: Optional[str] = None  # lakehouse_tables, lakehouse_files, warehouse
    lakehouse_id: Optional[str] = None
    lakehouse_name: Optional[str] = None
    warehouse_id: Optional[str] = None
    naming_convention: Optional[str] = None  # same_as_source, custom
    partition_by: Optional[str] = None
    file_format: Optional[str] = None  # delta, parquet, csv

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "lakehouse_id": self.lakehouse_id,
            "lakehouse_name": self.lakehouse_name,
            "naming_convention": self.naming_convention,
            "file_format": self.file_format,
        }


@dataclass
class OperationalConfig:
    """Operational and scheduling configuration"""
    frequency: Optional[str] = None  # manual, hourly, daily, weekly, realtime
    schedule_time: Optional[str] = None
    timezone: Optional[str] = "UTC"
    error_handling: Optional[str] = None  # retry, alert, skip
    retry_count: int = 3
    dependencies: List[str] = field(default_factory=list)
    notifications: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frequency": self.frequency,
            "schedule_time": self.schedule_time,
            "timezone": self.timezone,
            "error_handling": self.error_handling,
        }


@dataclass
class ArchitectureDesign:
    """Designed pipeline architecture"""
    pattern: Optional[str] = None  # simple_copy, medallion_bronze, medallion_full, streaming
    layers: List[str] = field(default_factory=list)  # bronze, silver, gold
    components: Dict[str, str] = field(default_factory=dict)  # layer -> component type
    activities: List[Dict[str, Any]] = field(default_factory=list)
    notebooks: List[Dict[str, Any]] = field(default_factory=list)
    connections_needed: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": self.pattern,
            "layers": self.layers,
            "components": self.components,
            "activities": self.activities,
            "notebooks": self.notebooks,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
        }


class PipelineState:
    """
    Main state container for pipeline requirements.
    Used by all agents to read and write information.
    """

    def __init__(self, workspace_id: str, user_id: str):
        self.workspace_id = workspace_id
        self.user_id = user_id
        self.stage = PipelineStage.INITIAL

        # Requirements sections
        self.source = SourceInfo()
        self.business = BusinessContext()
        self.transformations = TransformationNeeds()
        self.destination = DestinationConfig()
        self.operations = OperationalConfig()
        self.architecture = ArchitectureDesign()

        # Conversation tracking
        self.conversation_history: List[Dict[str, str]] = []
        self.agent_insights: Dict[str, Any] = {}
        self.questions_asked: List[str] = []
        self.user_confirmations: List[str] = []

    def update_from_message(self, message: str) -> None:
        """Extract and update state from user message"""
        message_lower = message.lower()

        # Source type detection
        source_keywords = {
            "postgresql": "postgresql",
            "postgres": "postgresql",
            "sql server": "sql_server",
            "sqlserver": "sql_server",
            "mysql": "mysql",
            "oracle": "oracle",
            "blob": "blob_storage",
            "azure blob": "blob_storage",
            "sharepoint": "sharepoint",
            "rest api": "rest_api",
            "api": "rest_api",
        }
        for keyword, source_type in source_keywords.items():
            if keyword in message_lower:
                self.source.type = source_type
                break

        # Location detection
        if "on-premise" in message_lower or "on premise" in message_lower or "onprem" in message_lower:
            self.source.location = "on_premise"
        elif "cloud" in message_lower or "azure" in message_lower or "aws" in message_lower:
            self.source.location = "cloud"

        # Use case detection
        use_case_keywords = {
            "power bi": ("analytics", ["power_bi"]),
            "dashboard": ("analytics", ["power_bi"]),
            "report": ("analytics", ["power_bi"]),
            "machine learning": ("ml", ["data_scientists"]),
            "ml": ("ml", ["data_scientists"]),
            "data science": ("ml", ["data_scientists"]),
            "archive": ("archive", []),
            "backup": ("archive", []),
        }
        for keyword, (use_case, consumers) in use_case_keywords.items():
            if keyword in message_lower:
                self.business.use_case = use_case
                self.business.consumers.extend(consumers)
                break

        # PII detection hints
        pii_keywords = ["customer", "employee", "patient", "user", "personal", "email", "phone", "address", "ssn", "credit card"]
        for keyword in pii_keywords:
            if keyword in message_lower:
                self.business.pii_likely = True
                break

        # Frequency detection
        frequency_keywords = {
            "real-time": "realtime",
            "realtime": "realtime",
            "hourly": "hourly",
            "daily": "daily",
            "weekly": "weekly",
            "one-time": "manual",
            "one time": "manual",
            "once": "manual",
            "migrate": "manual",
            "migration": "manual",
        }
        for keyword, frequency in frequency_keywords.items():
            if keyword in message_lower:
                self.operations.frequency = frequency
                break

        # Volume detection (look for numbers with GB/TB)
        import re
        volume_match = re.search(r'(\d+)\s*(gb|tb)', message_lower)
        if volume_match:
            volume = float(volume_match.group(1))
            unit = volume_match.group(2)
            if unit == "tb":
                volume *= 1000
            self.source.volume_gb = volume

        # Table count detection
        table_match = re.search(r'(\d+)\s*tables?', message_lower)
        if table_match:
            # We know there are tables, but not their names yet
            pass

    def has_minimum_requirements(self) -> bool:
        """Check if we have enough info to start designing"""
        return (
            self.source.type is not None and
            self.business.use_case is not None
        )

    def has_complete_requirements(self) -> bool:
        """Check if we have all info needed to deploy"""
        return (
            self.source.is_complete() and
            self.business.is_complete() and
            self.destination.type is not None and
            self.operations.frequency is not None
        )

    def get_missing_requirements(self) -> List[str]:
        """Get list of missing required information"""
        missing = []

        if not self.source.type:
            missing.append("source_type")
        if not self.source.location:
            missing.append("source_location")
        if not self.source.objects:
            missing.append("source_objects")
        if not self.business.use_case:
            missing.append("use_case")
        if not self.destination.type:
            missing.append("destination_type")
        if not self.operations.frequency:
            missing.append("frequency")

        return missing

    def get_summary(self) -> str:
        """Get human-readable summary of current state"""
        parts = []

        if self.source.type:
            loc = f" ({self.source.location})" if self.source.location else ""
            parts.append(f"Source: {self.source.type}{loc}")

        if self.source.objects:
            parts.append(f"Objects: {len(self.source.objects)} items")
        elif self.source.volume_gb:
            parts.append(f"Volume: ~{self.source.volume_gb}GB")

        if self.business.use_case:
            parts.append(f"Use case: {self.business.use_case}")

        if self.business.pii_likely:
            parts.append("PII: Likely present")

        if self.operations.frequency:
            parts.append(f"Frequency: {self.operations.frequency}")

        if self.architecture.pattern:
            parts.append(f"Architecture: {self.architecture.pattern}")

        return " | ".join(parts) if parts else "No information gathered yet"

    def to_dict(self) -> Dict[str, Any]:
        """Convert entire state to dictionary"""
        return {
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "stage": self.stage.value,
            "source": self.source.to_dict(),
            "business": self.business.to_dict(),
            "transformations": self.transformations.to_dict(),
            "destination": self.destination.to_dict(),
            "operations": self.operations.to_dict(),
            "architecture": self.architecture.to_dict(),
            "summary": self.get_summary(),
        }

    def to_json(self) -> str:
        """Convert state to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class StateManager:
    """
    Manages pipeline states across multiple sessions.
    Each user/workspace combination has its own state.
    """

    def __init__(self):
        self._states: Dict[str, PipelineState] = {}

    def get_state(self, workspace_id: str, user_id: str) -> PipelineState:
        """Get or create state for a user/workspace"""
        key = f"{user_id}_{workspace_id}"
        if key not in self._states:
            self._states[key] = PipelineState(workspace_id, user_id)
            logger.info(f"Created new pipeline state for {key}")
        return self._states[key]

    def clear_state(self, workspace_id: str, user_id: str) -> None:
        """Clear state for a user/workspace"""
        key = f"{user_id}_{workspace_id}"
        if key in self._states:
            del self._states[key]
            logger.info(f"Cleared pipeline state for {key}")

    def has_state(self, workspace_id: str, user_id: str) -> bool:
        """Check if state exists for a user/workspace"""
        key = f"{user_id}_{workspace_id}"
        return key in self._states


# Global state manager instance
state_manager = StateManager()
