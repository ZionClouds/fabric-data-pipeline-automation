"""
Pipeline Context for OpenAI Agents SDK - Production Ready

This module defines the context that flows through all agents during pipeline design.
Optimized for production with proper serialization, validation, and state management.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from enum import Enum
import json
import logging
from datetime import datetime

if TYPE_CHECKING:
    from services.fabric_api_service import FabricAPIService

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
    type: Optional[str] = None
    location: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    objects: List[str] = field(default_factory=list)
    volume_gb: Optional[float] = None
    schema: Dict[str, Any] = field(default_factory=dict)
    change_pattern: Optional[str] = None
    gateway_available: Optional[bool] = None
    gateway_id: Optional[str] = None
    connection_string: Optional[str] = None

    def is_complete(self) -> bool:
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
    use_case: Optional[str] = None
    consumers: List[str] = field(default_factory=list)
    sla_hours: Optional[int] = None
    criticality: Optional[str] = None
    deadline: Optional[str] = None
    pii_likely: bool = False
    compliance_requirements: List[str] = field(default_factory=list)

    def is_complete(self) -> bool:
        return self.use_case is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "use_case": self.use_case,
            "consumers": self.consumers,
            "sla_hours": self.sla_hours,
            "criticality": self.criticality,
            "pii_likely": self.pii_likely,
            "compliance_requirements": self.compliance_requirements,
        }


@dataclass
class TransformationNeeds:
    """Transformation requirements"""
    needed: Optional[bool] = None
    cleaning: List[str] = field(default_factory=list)
    enrichment: List[str] = field(default_factory=list)
    aggregations: List[str] = field(default_factory=list)
    pii_handling: Optional[str] = None
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
    type: Optional[str] = None
    lakehouse_id: Optional[str] = None
    lakehouse_name: Optional[str] = None
    warehouse_id: Optional[str] = None
    warehouse_name: Optional[str] = None
    naming_convention: Optional[str] = None
    partition_by: Optional[str] = None
    file_format: Optional[str] = "delta"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "lakehouse_id": self.lakehouse_id,
            "lakehouse_name": self.lakehouse_name,
            "warehouse_name": self.warehouse_name,
            "naming_convention": self.naming_convention,
            "file_format": self.file_format,
        }


@dataclass
class OperationalConfig:
    """Operational and scheduling configuration"""
    frequency: Optional[str] = None
    schedule_time: Optional[str] = None
    timezone: Optional[str] = "UTC"
    error_handling: Optional[str] = "retry"
    retry_count: int = 3
    dependencies: List[str] = field(default_factory=list)
    notifications: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frequency": self.frequency,
            "schedule_time": self.schedule_time,
            "timezone": self.timezone,
            "error_handling": self.error_handling,
            "retry_count": self.retry_count,
        }


@dataclass
class ArchitectureDesign:
    """Designed pipeline architecture"""
    pattern: Optional[str] = None
    layers: List[str] = field(default_factory=list)
    components: Dict[str, str] = field(default_factory=dict)
    activities: List[Dict[str, Any]] = field(default_factory=list)
    notebooks: List[Dict[str, Any]] = field(default_factory=list)
    connections_needed: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    pipeline_json: Optional[Dict[str, Any]] = None

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


@dataclass
class PipelineContext:
    """
    Main context for pipeline design agents - Production Ready.
    This flows through all agents via the SDK's context mechanism.
    """
    workspace_id: str
    user_id: str
    lakehouse_name: Optional[str] = None
    lakehouse_id: Optional[str] = None
    warehouse_name: Optional[str] = None

    # Pipeline state
    stage: PipelineStage = PipelineStage.INITIAL

    # Requirements sections
    source: SourceInfo = field(default_factory=SourceInfo)
    business: BusinessContext = field(default_factory=BusinessContext)
    transformations: TransformationNeeds = field(default_factory=TransformationNeeds)
    destination: DestinationConfig = field(default_factory=DestinationConfig)
    operations: OperationalConfig = field(default_factory=OperationalConfig)
    architecture: ArchitectureDesign = field(default_factory=ArchitectureDesign)

    # Conversation tracking
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    agent_insights: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # External services (not serialized)
    _fabric_service: Optional[Any] = field(default=None, repr=False)

    @property
    def fabric_service(self):
        return self._fabric_service

    @fabric_service.setter
    def fabric_service(self, value):
        self._fabric_service = value

    def update_from_message(self, message: str) -> Dict[str, Any]:
        """Extract and update context from user message. Returns extracted info."""
        import re
        message_lower = message.lower()
        extracted = {}

        # Source type detection
        source_keywords = {
            "postgresql": "postgresql", "postgres": "postgresql",
            "sql server": "sql_server", "sqlserver": "sql_server", "mssql": "sql_server",
            "mysql": "mysql", "oracle": "oracle",
            "blob": "blob_storage", "azure blob": "blob_storage",
            "adls": "adls_gen2", "data lake": "adls_gen2",
            "sharepoint": "sharepoint",
            "dataverse": "rest_api",
            "rest api": "rest_api", "api": "rest_api",
            "snowflake": "snowflake", "databricks": "databricks",
            "cosmos": "cosmosdb", "cosmosdb": "cosmosdb",
        }
        for keyword, source_type in source_keywords.items():
            if keyword in message_lower:
                self.source.type = source_type
                extracted["source_type"] = source_type
                break

        # Location detection
        if any(x in message_lower for x in ["on-premise", "on premise", "onprem", "local server"]):
            self.source.location = "on_premise"
            extracted["location"] = "on_premise"
        elif any(x in message_lower for x in ["cloud", "azure", "aws", "gcp", "hosted"]):
            self.source.location = "cloud"
            extracted["location"] = "cloud"

        # Use case detection
        use_case_map = {
            "power bi": ("analytics", ["power_bi"]),
            "dashboard": ("analytics", ["power_bi"]),
            "report": ("analytics", ["power_bi"]),
            "machine learning": ("ml", ["data_scientists"]),
            "ml model": ("ml", ["data_scientists"]),
            "data science": ("ml", ["data_scientists"]),
            "archive": ("archive", []),
            "backup": ("archive", []),
            "real-time": ("operational", ["applications"]),
            "operational": ("operational", ["applications"]),
        }
        for keyword, (use_case, consumers) in use_case_map.items():
            if keyword in message_lower:
                self.business.use_case = use_case
                self.business.consumers.extend([c for c in consumers if c not in self.business.consumers])
                extracted["use_case"] = use_case
                break

        # PII detection (with negation awareness)
        # First check for explicit negations like "no pii", "no personal", "not pii"
        negation_pii_patterns = ["no pii", "no phi", "not pii", "no personal", "without pii", "no sensitive"]
        explicitly_no_pii = any(neg in message_lower for neg in negation_pii_patterns)

        if not explicitly_no_pii:
            pii_keywords = ["customer", "employee", "patient", "user data", "personal",
                           "email", "phone", "address", "ssn", "credit card", "hipaa", "gdpr", "pii", "phi"]
            for keyword in pii_keywords:
                if keyword in message_lower:
                    self.business.pii_likely = True
                    extracted["pii_likely"] = True
                    break

        # Frequency detection
        frequency_map = {
            "real-time": "realtime", "realtime": "realtime", "streaming": "realtime",
            "hourly": "hourly", "every hour": "hourly",
            "daily": "daily", "every day": "daily",
            "weekly": "weekly", "every week": "weekly",
            "one-time": "manual", "one time": "manual", "once": "manual",
            "migrate": "manual", "migration": "manual",
        }
        for keyword, frequency in frequency_map.items():
            if keyword in message_lower:
                self.operations.frequency = frequency
                extracted["frequency"] = frequency
                break

        # Volume detection
        volume_match = re.search(r'(\d+(?:\.\d+)?)\s*(gb|tb|mb)', message_lower)
        if volume_match:
            volume = float(volume_match.group(1))
            unit = volume_match.group(2)
            if unit == "tb":
                volume *= 1000
            elif unit == "mb":
                volume /= 1000
            self.source.volume_gb = volume
            extracted["volume_gb"] = volume

        # Table count detection
        table_match = re.search(r'(\d+)\s*tables?', message_lower)
        if table_match:
            extracted["table_count"] = int(table_match.group(1))

        # URL detection (for REST API, Dataverse, etc.)
        url_match = re.search(r'https?://[^\s,]+', message)  # Use original case
        if url_match:
            url = url_match.group(0).rstrip('.,;)')
            self.source.host = url
            extracted["source_url"] = url

        # Table/entity name detection (e.g., "table name: buyer", "table: users")
        table_name_match = re.search(r'table\s*(?:name)?[:\s]+(\w+)', message_lower)
        if table_name_match:
            table_name = table_name_match.group(1)
            if table_name not in ['name', 'is', 'the', 'a']:
                if table_name not in self.source.objects:
                    self.source.objects.append(table_name)
                extracted["table_name"] = table_name

        self.updated_at = datetime.utcnow().isoformat()
        return extracted

    def has_minimum_requirements(self) -> bool:
        """Check if we have enough info to start designing"""
        return self.source.type is not None and self.business.use_case is not None

    def has_complete_requirements(self) -> bool:
        """Check if we have all info needed to deploy"""
        return (
            self.source.is_complete() and
            self.business.is_complete() and
            self.destination.type is not None and
            self.operations.frequency is not None and
            self.architecture.pattern is not None
        )

    def get_missing_requirements(self) -> List[str]:
        """Get list of missing required information"""
        missing = []
        if not self.source.type:
            missing.append("source_type")
        if not self.source.location:
            missing.append("source_location")
        if not self.business.use_case:
            missing.append("use_case")
        if not self.destination.type:
            missing.append("destination_type")
        if not self.operations.frequency:
            missing.append("frequency")
        return missing

    def get_summary(self) -> str:
        """Get human-readable summary"""
        parts = []
        if self.source.type:
            loc = f" ({self.source.location})" if self.source.location else ""
            parts.append(f"Source: {self.source.type}{loc}")
        if self.source.volume_gb:
            parts.append(f"Volume: ~{self.source.volume_gb}GB")
        if self.business.use_case:
            parts.append(f"Use case: {self.business.use_case}")
        if self.business.pii_likely:
            parts.append("PII: Yes")
        if self.operations.frequency:
            parts.append(f"Frequency: {self.operations.frequency}")
        if self.architecture.pattern:
            parts.append(f"Pattern: {self.architecture.pattern}")
        return " | ".join(parts) if parts else "No information gathered yet"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "lakehouse_name": self.lakehouse_name,
            "warehouse_name": self.warehouse_name,
            "stage": self.stage.value,
            "source": self.source.to_dict(),
            "business": self.business.to_dict(),
            "transformations": self.transformations.to_dict(),
            "destination": self.destination.to_dict(),
            "operations": self.operations.to_dict(),
            "architecture": self.architecture.to_dict(),
            "summary": self.get_summary(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def get_context_for_prompt(self) -> str:
        """Get formatted context for agent prompts"""
        lines = [
            "## Current Pipeline Requirements",
            f"**Stage:** {self.stage.value}",
            f"**Workspace:** {self.workspace_id}",
            ""
        ]

        if self.source.type:
            lines.append("### Source System")
            lines.append(f"- Type: {self.source.type}")
            if self.source.location:
                lines.append(f"- Location: {self.source.location}")
            if self.source.database:
                lines.append(f"- Database: {self.source.database}")
            if self.source.volume_gb:
                lines.append(f"- Estimated Volume: {self.source.volume_gb}GB")
            lines.append("")

        if self.business.use_case:
            lines.append("### Business Context")
            lines.append(f"- Use Case: {self.business.use_case}")
            if self.business.consumers:
                lines.append(f"- Consumers: {', '.join(self.business.consumers)}")
            if self.business.pii_likely:
                lines.append("- PII/Sensitive Data: Likely present")
            lines.append("")

        if self.operations.frequency:
            lines.append("### Operational Requirements")
            lines.append(f"- Frequency: {self.operations.frequency}")
            lines.append("")

        if self.architecture.pattern:
            lines.append("### Architecture Design")
            lines.append(f"- Pattern: {self.architecture.pattern}")
            if self.architecture.layers:
                lines.append(f"- Layers: {' -> '.join(self.architecture.layers)}")
            lines.append("")

        missing = self.get_missing_requirements()
        if missing:
            lines.append("### Still Needed")
            for item in missing:
                lines.append(f"- {item.replace('_', ' ').title()}")

        return "\n".join(lines)


class ContextManager:
    """Manages pipeline contexts across sessions - Production Ready"""

    def __init__(self):
        self._contexts: Dict[str, PipelineContext] = {}
        self._lock = None  # For async safety if needed

    def _get_key(self, workspace_id: str, user_id: str) -> str:
        return f"{user_id}_{workspace_id}"

    def get_context(
        self,
        workspace_id: str,
        user_id: str,
        lakehouse_name: Optional[str] = None,
        lakehouse_id: Optional[str] = None,
        warehouse_name: Optional[str] = None,
        fabric_service: Optional[Any] = None,
    ) -> PipelineContext:
        """Get or create context for a user/workspace"""
        key = self._get_key(workspace_id, user_id)

        if key not in self._contexts:
            self._contexts[key] = PipelineContext(
                workspace_id=workspace_id,
                user_id=user_id,
                lakehouse_name=lakehouse_name,
                lakehouse_id=lakehouse_id,
                warehouse_name=warehouse_name,
            )
            logger.info(f"Created new pipeline context for {key}")

        ctx = self._contexts[key]

        # Update mutable fields
        if lakehouse_name:
            ctx.lakehouse_name = lakehouse_name
            ctx.destination.lakehouse_name = lakehouse_name
        if lakehouse_id:
            ctx.lakehouse_id = lakehouse_id
        if warehouse_name:
            ctx.warehouse_name = warehouse_name
            ctx.destination.warehouse_name = warehouse_name
        if fabric_service:
            ctx._fabric_service = fabric_service

        return ctx

    def clear_context(self, workspace_id: str, user_id: str) -> bool:
        """Clear context for a user/workspace"""
        key = self._get_key(workspace_id, user_id)
        if key in self._contexts:
            del self._contexts[key]
            logger.info(f"Cleared pipeline context for {key}")
            return True
        return False

    def has_context(self, workspace_id: str, user_id: str) -> bool:
        return self._get_key(workspace_id, user_id) in self._contexts

    def get_all_contexts(self) -> Dict[str, PipelineContext]:
        """Get all active contexts (for monitoring)"""
        return self._contexts.copy()


# Global singleton
context_manager = ContextManager()
