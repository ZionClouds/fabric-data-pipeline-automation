"""
Source Analyst Agent

Deep expertise on source systems, connection methods, and extraction strategies.
The Data Detective of the pipeline architect team.
"""

from typing import Dict, Any, List
import logging

from .base_agent import BaseAgent, AgentResponse
from .state_manager import PipelineState

logger = logging.getLogger(__name__)


# Source system knowledge base
SOURCE_KNOWLEDGE = {
    "postgresql": {
        "display_name": "PostgreSQL",
        "cloud_connection": "direct",
        "onprem_connection": "gateway_required",
        "default_port": 5432,
        "cdc_options": ["logical_replication", "triggers", "timestamp_column"],
        "bulk_extract": "COPY command or pg_dump",
        "fabric_connector": "PostgreSQL connector",
        "considerations": [
            "Consider using a read replica for large extractions",
            "Connection pooling recommended for parallel loads",
            "Schema changes need monitoring",
        ],
        "best_practices": [
            "Use COPY command for bulk extraction (faster than SELECT)",
            "Add indexes on timestamp columns for incremental loads",
            "Consider logical replication for near real-time CDC",
        ],
    },
    "sql_server": {
        "display_name": "SQL Server",
        "cloud_connection": "direct",
        "onprem_connection": "gateway_required",
        "default_port": 1433,
        "cdc_options": ["change_tracking", "cdc", "temporal_tables"],
        "fabric_native": "Mirroring available",
        "fabric_connector": "SQL Server connector",
        "considerations": [
            "Fabric Mirroring provides real-time CDC (recommended)",
            "Snapshot isolation prevents blocking during reads",
            "Check index usage for optimal extraction queries",
        ],
        "best_practices": [
            "Enable Change Tracking for efficient incremental loads",
            "Use READ_COMMITTED_SNAPSHOT for non-blocking reads",
            "Consider Mirroring for real-time requirements",
        ],
    },
    "mysql": {
        "display_name": "MySQL",
        "cloud_connection": "direct",
        "onprem_connection": "gateway_required",
        "default_port": 3306,
        "cdc_options": ["binlog", "timestamp_column"],
        "fabric_connector": "MySQL connector",
        "considerations": [
            "Binary log replication available for CDC",
            "InnoDB tables recommended for consistent reads",
        ],
    },
    "oracle": {
        "display_name": "Oracle",
        "cloud_connection": "direct",
        "onprem_connection": "gateway_required",
        "default_port": 1521,
        "cdc_options": ["logminer", "streams", "goldengate"],
        "fabric_connector": "Oracle connector",
        "considerations": [
            "LogMiner can be used for basic CDC",
            "GoldenGate recommended for enterprise CDC",
            "Consider partitioning for large tables",
        ],
    },
    "blob_storage": {
        "display_name": "Azure Blob Storage",
        "cloud_connection": "direct",
        "auth_options": ["account_key", "sas_token", "managed_identity", "service_principal"],
        "fabric_native": "Shortcut available",
        "patterns": ["wildcard_files", "folder_partition"],
        "formats": ["csv", "parquet", "json", "avro", "delta"],
        "considerations": [
            "OneLake shortcuts provide direct access without copying",
            "Parquet format recommended for analytics",
            "Partition by date for efficient incremental loads",
        ],
        "best_practices": [
            "Use shortcuts instead of copying where possible",
            "Prefer Parquet or Delta format over CSV",
            "Organize files with Hive-style partitioning (year=/month=/day=)",
        ],
    },
    "adls": {
        "display_name": "Azure Data Lake Storage Gen2",
        "cloud_connection": "direct",
        "auth_options": ["account_key", "managed_identity", "service_principal"],
        "fabric_native": "Shortcut available",
        "considerations": [
            "Hierarchical namespace provides better performance",
            "ACLs available for fine-grained access control",
        ],
    },
    "sharepoint": {
        "display_name": "SharePoint",
        "cloud_connection": "direct",
        "auth_options": ["service_principal", "user_auth"],
        "objects": ["lists", "document_libraries", "sites"],
        "limitations": [
            "API throttling may affect large extractions",
            "5000 item threshold for list views",
            "Document metadata extraction has limitations",
        ],
        "considerations": [
            "Use pagination for large lists",
            "Delta sync requires tracking change tokens",
            "Consider extracting to Blob first for large datasets",
        ],
    },
    "rest_api": {
        "display_name": "REST API",
        "auth_options": ["api_key", "oauth2", "bearer_token", "basic_auth"],
        "patterns": ["pagination", "rate_limiting", "retry"],
        "considerations": [
            "Handle rate limiting with exponential backoff",
            "Implement proper pagination handling",
            "Consider response caching for repeated calls",
        ],
    },
}


class SourceAnalystAgent(BaseAgent):
    """
    Source Analyst Agent - Expert on source systems.

    Responsibilities:
    - Analyze source system requirements
    - Identify connection needs (gateway, auth)
    - Recommend extraction strategies
    - Flag potential issues and blockers
    """

    def __init__(self, ai_service=None):
        super().__init__(
            name="source_analyst",
            role="Source System Expert",
            ai_service=ai_service
        )
        self.knowledge = SOURCE_KNOWLEDGE

    @property
    def system_prompt(self) -> str:
        return """You are the Source Analyst Agent - an expert on data source systems.

## YOUR EXPERTISE
You have deep knowledge of:
- Database systems: PostgreSQL, SQL Server, MySQL, Oracle
- Cloud storage: Azure Blob, ADLS, S3
- SaaS sources: SharePoint, Salesforce, REST APIs
- Connection methods, authentication, and gateways
- CDC (Change Data Capture) strategies
- Extraction optimization

## YOUR ROLE
Analyze the source system and provide:
1. Connection requirements (gateway, auth type)
2. Extraction strategy recommendations
3. Potential blockers or issues
4. Best practices for this source type

## OUTPUT FORMAT
Provide structured analysis:
- CONNECTION: What's needed to connect
- EXTRACTION: How to efficiently extract data
- CDC: Options for incremental/change detection
- WARNINGS: Any blockers or concerns
- RECOMMENDATIONS: Best practices"""

    @property
    def required_info(self) -> List[str]:
        return [
            "source_type",
            "source_location",
        ]

    @property
    def thinking_rules(self) -> Dict[str, Any]:
        return {
            "on-premise": {"gateway_required": True},
            "on premise": {"gateway_required": True},
            "large": {"consider_partitioning": True},
            "100gb": {"large_volume": True},
            "real-time": {"consider_cdc": True},
            "daily": {"incremental_recommended": True},
        }

    async def process(self, state: PipelineState, user_message: str) -> AgentResponse:
        """Analyze source system and provide recommendations"""

        source_type = state.source.type
        if not source_type:
            return AgentResponse(
                message="I need to know the source system type to provide analysis.",
                is_complete=False,
            )

        # Get source knowledge
        source_info = self.knowledge.get(source_type, {})

        # Build analysis
        insights = self._analyze_source(state, source_info)
        recommendations = self._get_recommendations(state, source_info)
        warnings = self._get_warnings(state, source_info)

        # Update state with findings
        state_updates = {}

        # Check gateway requirement
        if state.source.location == "on_premise":
            if not state.source.gateway_available:
                warnings.append("On-Premises Data Gateway required but not confirmed")
                state_updates["gateway_required"] = True

        # Set connection info
        if source_info.get("default_port"):
            if not state.source.port:
                state.source.port = source_info["default_port"]

        # Generate message
        message = self._format_analysis(state, source_info, insights, recommendations, warnings)

        return AgentResponse(
            message=message,
            insights=insights,
            recommendations=recommendations,
            warnings=warnings,
            state_updates=state_updates,
            is_complete=True,
        )

    def _analyze_source(self, state: PipelineState, source_info: Dict) -> Dict[str, Any]:
        """Analyze source and return insights"""

        insights = {
            "source_type": state.source.type,
            "display_name": source_info.get("display_name", state.source.type),
            "location": state.source.location,
        }

        # Connection type
        if state.source.location == "on_premise":
            insights["connection_method"] = "On-Premises Data Gateway"
            insights["gateway_required"] = True
        else:
            insights["connection_method"] = "Direct cloud connection"
            insights["gateway_required"] = False

        # CDC options
        if "cdc_options" in source_info:
            insights["cdc_options"] = source_info["cdc_options"]

        # Fabric native options
        if "fabric_native" in source_info:
            insights["fabric_native"] = source_info["fabric_native"]

        # Volume considerations
        if state.source.volume_gb:
            if state.source.volume_gb > 100:
                insights["volume_category"] = "large"
                insights["partitioning_recommended"] = True
            elif state.source.volume_gb > 10:
                insights["volume_category"] = "medium"
            else:
                insights["volume_category"] = "small"

        return insights

    def _get_recommendations(self, state: PipelineState, source_info: Dict) -> List[str]:
        """Get recommendations for this source"""

        recommendations = []

        # Add source-specific best practices
        if "best_practices" in source_info:
            recommendations.extend(source_info["best_practices"][:2])  # Top 2

        # Volume-based recommendations
        if state.source.volume_gb and state.source.volume_gb > 50:
            recommendations.append("Consider partitioning extraction for large volume")

        # Frequency-based recommendations
        if state.operations.frequency in ["daily", "hourly"]:
            if "cdc_options" in source_info:
                recommendations.append(f"Use {source_info['cdc_options'][0]} for efficient incremental loads")

        # Fabric native options
        if source_info.get("fabric_native"):
            recommendations.append(f"Consider: {source_info['fabric_native']}")

        return recommendations

    def _get_warnings(self, state: PipelineState, source_info: Dict) -> List[str]:
        """Get warnings and blockers"""

        warnings = []

        # Gateway warning
        if state.source.location == "on_premise":
            warnings.append("On-Premises Data Gateway must be installed and configured")

        # Limitations
        if "limitations" in source_info:
            warnings.extend(source_info["limitations"][:2])  # Top 2

        # Volume warnings
        if state.source.volume_gb and state.source.volume_gb > 500:
            warnings.append("Very large volume - extraction may take significant time")

        return warnings

    def _format_analysis(
        self,
        state: PipelineState,
        source_info: Dict,
        insights: Dict,
        recommendations: List[str],
        warnings: List[str]
    ) -> str:
        """Format analysis as readable message"""

        parts = [f"## Source Analysis: {insights.get('display_name', state.source.type)}\n"]

        # Connection
        parts.append("### Connection Requirements")
        parts.append(f"- **Method**: {insights.get('connection_method', 'Standard connector')}")
        if insights.get("gateway_required"):
            parts.append("- **Gateway**: Required (on-premises source)")
        if source_info.get("auth_options"):
            parts.append(f"- **Auth Options**: {', '.join(source_info['auth_options'])}")

        # Extraction strategy
        parts.append("\n### Extraction Strategy")
        if state.operations.frequency == "manual":
            parts.append("- **Type**: One-time full extraction")
        else:
            parts.append(f"- **Type**: Incremental ({state.operations.frequency})")
            if insights.get("cdc_options"):
                parts.append(f"- **CDC Options**: {', '.join(insights['cdc_options'])}")

        # Recommendations
        if recommendations:
            parts.append("\n### Recommendations")
            for rec in recommendations:
                parts.append(f"- {rec}")

        # Warnings
        if warnings:
            parts.append("\n### Important Notes")
            for warning in warnings:
                parts.append(f"- {warning}")

        return "\n".join(parts)
