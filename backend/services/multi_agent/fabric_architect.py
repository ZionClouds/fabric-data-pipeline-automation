"""
Fabric Architect Agent

Designs the optimal pipeline architecture using Microsoft Fabric components.
The Solution Designer of the pipeline architect team.
"""

from typing import Dict, Any, List, Optional
import logging

from .base_agent import BaseAgent, AgentResponse
from .state_manager import PipelineState

logger = logging.getLogger(__name__)


# Component decision matrix
COMPONENT_MATRIX = {
    "Copy Activity": {
        "use_when": [
            "No transformations needed",
            "Simple data movement",
            "Bronze layer ingestion",
            "Bulk data loading",
        ],
        "avoid_when": [
            "Complex transformations needed",
            "PII masking required",
            "Data quality checks needed",
        ],
        "strengths": ["Simple", "Fast", "Low compute cost", "Reliable"],
        "max_recommended_tables": 50,
    },
    "Dataflow Gen2": {
        "use_when": [
            "Light transformations (filter, rename, type cast)",
            "PII detection and masking",
            "Visual debugging helpful",
            "Silver layer processing",
            "Non-technical team needs to maintain",
        ],
        "avoid_when": [
            "Very large datasets (>100GB per run)",
            "Complex Python/Spark logic",
            "Custom ML models",
        ],
        "strengths": ["Visual design", "Built-in transforms", "PII detection", "Easy maintenance"],
        "max_recommended_volume_gb": 100,
    },
    "Notebook": {
        "use_when": [
            "Complex transformations",
            "Large datasets (>100GB)",
            "Custom Python/PySpark logic",
            "Gold layer aggregations",
            "Data quality frameworks (Great Expectations)",
            "Machine learning preprocessing",
        ],
        "avoid_when": [
            "Simple copies with no logic",
            "Team lacks Python skills",
        ],
        "strengths": ["Flexible", "Powerful", "Scalable", "Custom logic", "ML integration"],
    },
    "Mirroring": {
        "use_when": [
            "SQL Server or Azure SQL source",
            "Real-time CDC needed",
            "Continuous sync required",
            "Minimal latency requirements",
        ],
        "avoid_when": [
            "Non-SQL sources",
            "One-time migration",
            "Complex transformations at source",
        ],
        "strengths": ["Real-time", "Automatic CDC", "Low latency", "No pipeline needed"],
        "supported_sources": ["sql_server", "azure_sql"],
    },
    "Eventstream": {
        "use_when": [
            "Real-time streaming data",
            "Event-driven architecture",
            "IoT data ingestion",
        ],
        "avoid_when": [
            "Batch processing",
            "Traditional databases",
        ],
        "strengths": ["Real-time", "Event processing", "Low latency"],
    },
}

# Architecture patterns
ARCHITECTURE_PATTERNS = {
    "simple_copy": {
        "description": "Direct copy from source to destination",
        "layers": ["landing"],
        "components": {"landing": "Copy Activity"},
        "use_when": ["One-time migration", "No transforms", "Small data (<10GB)", "Simple use case"],
    },
    "medallion_bronze": {
        "description": "Raw data ingestion to Bronze layer only",
        "layers": ["bronze"],
        "components": {"bronze": "Copy Activity"},
        "use_when": ["Need raw data preservation", "Transforms done elsewhere", "Data lake pattern"],
    },
    "medallion_silver": {
        "description": "Bronze to Silver (cleaned data)",
        "layers": ["bronze", "silver"],
        "components": {"bronze": "Copy Activity", "silver": "Dataflow Gen2"},
        "use_when": ["Need data cleaning", "PII masking needed", "Medium complexity"],
    },
    "medallion_full": {
        "description": "Complete Bronze → Silver → Gold architecture",
        "layers": ["bronze", "silver", "gold"],
        "components": {"bronze": "Copy Activity", "silver": "Dataflow Gen2", "gold": "Notebook"},
        "use_when": ["Analytics use case", "Need aggregations", "Power BI destination", "Enterprise pattern"],
    },
    "medallion_notebook": {
        "description": "Medallion with Notebooks for all transforms",
        "layers": ["bronze", "silver", "gold"],
        "components": {"bronze": "Copy Activity", "silver": "Notebook", "gold": "Notebook"},
        "use_when": ["Large data (>100GB)", "Complex transforms", "ML preprocessing", "Custom logic"],
    },
}


class FabricArchitectAgent(BaseAgent):
    """
    Fabric Architect Agent - Designs pipeline architecture.

    Responsibilities:
    - Select appropriate Fabric components
    - Design medallion layer architecture
    - Create pipeline activity structure
    - Optimize for performance and cost
    """

    def __init__(self, ai_service=None):
        super().__init__(
            name="fabric_architect",
            role="Solution Architect",
            ai_service=ai_service
        )
        self.components = COMPONENT_MATRIX
        self.patterns = ARCHITECTURE_PATTERNS

    @property
    def system_prompt(self) -> str:
        return """You are the Fabric Architect Agent - an expert on Microsoft Fabric architecture.

## YOUR EXPERTISE
You have deep knowledge of:
- Fabric Pipeline components: Copy Activity, Dataflow Gen2, Notebooks
- Medallion architecture: Bronze, Silver, Gold layers
- Real-time: Mirroring, Eventstream, KQL Database
- Performance optimization and cost efficiency
- Integration patterns and best practices

## YOUR ROLE
Design the optimal pipeline architecture by:
1. Selecting the right components for each layer
2. Designing the data flow between components
3. Considering performance, cost, and maintainability
4. Providing clear architecture diagrams

## DECISION CRITERIA
- Copy Activity: Simple copy, no transforms, Bronze layer
- Dataflow Gen2: Light transforms, PII masking, visual design
- Notebook: Complex logic, large data, ML, Gold aggregations
- Mirroring: Real-time SQL Server sync
- Eventstream: Streaming data

## OUTPUT FORMAT
Provide clear architecture design with components, flow, and reasoning."""

    @property
    def required_info(self) -> List[str]:
        return [
            "source_type",
            "use_case",
            "frequency",
        ]

    @property
    def thinking_rules(self) -> Dict[str, Any]:
        return {
            "power bi": {"pattern": "medallion_full", "needs_gold": True},
            "analytics": {"pattern": "medallion_full", "needs_gold": True},
            "one-time": {"pattern": "simple_copy"},
            "migrate": {"pattern": "simple_copy"},
            "real-time": {"consider": "mirroring_or_eventstream"},
            "pii": {"silver_component": "Dataflow Gen2"},
            "large": {"prefer_notebooks": True},
            "100gb": {"prefer_notebooks": True},
        }

    async def process(self, state: PipelineState, user_message: str) -> AgentResponse:
        """Design pipeline architecture"""

        # Determine best pattern
        pattern_name, pattern = self._select_pattern(state)

        # Select components for each layer
        components = self._select_components(state, pattern)

        # Build architecture design
        architecture = self._build_architecture(state, pattern_name, pattern, components)

        # Generate activity structure
        activities = self._generate_activities(state, architecture)

        # Update state
        state.architecture.pattern = pattern_name
        state.architecture.layers = pattern["layers"]
        state.architecture.components = components
        state.architecture.activities = activities

        # Build insights
        insights = {
            "selected_pattern": pattern_name,
            "pattern_description": pattern["description"],
            "layers": pattern["layers"],
            "components": components,
            "activity_count": len(activities),
        }

        # Recommendations
        recommendations = self._get_recommendations(state, architecture)

        # Warnings
        warnings = self._get_warnings(state, architecture)

        # Generate message
        message = self._format_architecture(state, architecture, recommendations, warnings)

        return AgentResponse(
            message=message,
            insights=insights,
            recommendations=recommendations,
            warnings=warnings,
            state_updates={"architecture": architecture},
            is_complete=True,
        )

    def _select_pattern(self, state: PipelineState) -> tuple:
        """Select the best architecture pattern"""

        # Default to medallion_full for analytics
        if state.business.use_case == "analytics":
            return "medallion_full", self.patterns["medallion_full"]

        # ML use case needs notebooks
        if state.business.use_case == "ml":
            return "medallion_notebook", self.patterns["medallion_notebook"]

        # One-time migration
        if state.operations.frequency == "manual":
            # Check if transforms needed
            if state.transformations.needed or state.business.pii_likely:
                return "medallion_silver", self.patterns["medallion_silver"]
            return "simple_copy", self.patterns["simple_copy"]

        # Large volume
        if state.source.volume_gb and state.source.volume_gb > 100:
            return "medallion_notebook", self.patterns["medallion_notebook"]

        # Default for recurring with transforms
        if state.transformations.needed:
            return "medallion_full", self.patterns["medallion_full"]

        # Default
        return "medallion_silver", self.patterns["medallion_silver"]

    def _select_components(self, state: PipelineState, pattern: Dict) -> Dict[str, str]:
        """Select specific components for each layer"""

        components = dict(pattern.get("components", {}))

        # Override based on requirements
        if state.source.volume_gb and state.source.volume_gb > 100:
            # Large volume - prefer notebooks
            if "silver" in components:
                components["silver"] = "Notebook"
            if "gold" in components:
                components["gold"] = "Notebook"

        elif state.business.pii_likely:
            # PII - Dataflow Gen2 has built-in PII detection
            if "silver" in components:
                components["silver"] = "Dataflow Gen2"

        return components

    def _build_architecture(
        self,
        state: PipelineState,
        pattern_name: str,
        pattern: Dict,
        components: Dict[str, str]
    ) -> Dict[str, Any]:
        """Build complete architecture specification"""

        architecture = {
            "pattern": pattern_name,
            "description": pattern["description"],
            "layers": [],
        }

        # Build each layer
        for layer in pattern["layers"]:
            layer_spec = {
                "name": layer,
                "component": components.get(layer, "Copy Activity"),
                "purpose": self._get_layer_purpose(layer),
                "tables": [],  # Will be populated with actual tables
            }

            # Add table naming
            if layer == "bronze":
                layer_spec["naming"] = "{source}_{table}_raw"
            elif layer == "silver":
                layer_spec["naming"] = "{domain}_{entity}_clean"
            elif layer == "gold":
                layer_spec["naming"] = "{domain}_{metric}_agg"

            architecture["layers"].append(layer_spec)

        return architecture

    def _get_layer_purpose(self, layer: str) -> str:
        """Get purpose description for each layer"""
        purposes = {
            "landing": "Temporary staging area for incoming data",
            "bronze": "Raw data exactly as received from source",
            "silver": "Cleaned, deduplicated, validated data",
            "gold": "Business-ready aggregated data for analytics",
        }
        return purposes.get(layer, "Data processing layer")

    def _generate_activities(self, state: PipelineState, architecture: Dict) -> List[Dict]:
        """Generate pipeline activities"""

        activities = []
        previous_layer = None

        for layer in architecture["layers"]:
            layer_name = layer["name"]
            component = layer["component"]

            # Determine activity type
            if component == "Copy Activity":
                activity = self._create_copy_activity(state, layer_name, previous_layer)
            elif component == "Dataflow Gen2":
                activity = self._create_dataflow_activity(state, layer_name, previous_layer)
            elif component == "Notebook":
                activity = self._create_notebook_activity(state, layer_name, previous_layer)
            else:
                activity = {"name": f"{layer_name}_activity", "type": component}

            activity["layer"] = layer_name
            activity["depends_on"] = [f"{previous_layer}_activity"] if previous_layer else []
            activities.append(activity)

            previous_layer = layer_name

        return activities

    def _create_copy_activity(self, state: PipelineState, layer: str, depends_on: Optional[str]) -> Dict:
        """Create Copy Activity specification"""

        # Determine if we need ForEach for multiple tables
        table_count = len(state.source.objects) if state.source.objects else 15  # Estimate

        if table_count > 1:
            return {
                "name": f"{layer}_copy",
                "type": "ForEach",
                "description": f"Copy data to {layer} layer",
                "items": "@pipeline().parameters.tables",
                "parallel_count": min(table_count, 10),
                "inner_activity": {
                    "name": "Copy_Table",
                    "type": "Copy",
                    "source": {
                        "type": f"{state.source.type}Source",
                        "query": "@concat('SELECT * FROM ', item().schema, '.', item().table)",
                    },
                    "sink": {
                        "type": "LakehouseTableSink",
                        "table_name": f"@concat('{layer}_', item().table)",
                    },
                },
            }
        else:
            return {
                "name": f"{layer}_copy",
                "type": "Copy",
                "description": f"Copy data to {layer} layer",
                "source": {"type": f"{state.source.type}Source"},
                "sink": {"type": "LakehouseTableSink"},
            }

    def _create_dataflow_activity(self, state: PipelineState, layer: str, depends_on: Optional[str]) -> Dict:
        """Create Dataflow Gen2 activity specification"""

        transforms = []

        # Add standard transforms for silver layer
        if layer == "silver":
            transforms.append("Remove duplicates")
            transforms.append("Handle null values")
            transforms.append("Standardize data types")

            if state.business.pii_likely:
                transforms.append("Detect and mask PII columns")

        return {
            "name": f"{layer}_dataflow",
            "type": "Dataflow Gen2",
            "description": f"Transform data for {layer} layer",
            "transforms": transforms,
        }

    def _create_notebook_activity(self, state: PipelineState, layer: str, depends_on: Optional[str]) -> Dict:
        """Create Notebook activity specification"""

        purpose = ""
        if layer == "silver":
            purpose = "Data cleaning and transformation"
        elif layer == "gold":
            purpose = "Business aggregations and KPIs"

        return {
            "name": f"{layer}_notebook",
            "type": "TridentNotebook",
            "description": f"{purpose} for {layer} layer",
            "notebook_name": f"nb_{layer}_processing",
        }

    def _get_recommendations(self, state: PipelineState, architecture: Dict) -> List[str]:
        """Get architecture recommendations"""

        recommendations = []

        pattern = architecture.get("pattern", "")

        if pattern == "medallion_full":
            recommendations.append("Medallion architecture provides data lineage and reprocessing capability")

        if state.operations.frequency == "daily":
            recommendations.append("Schedule pipeline during off-peak hours for optimal performance")

        if any(l["component"] == "Dataflow Gen2" for l in architecture.get("layers", [])):
            recommendations.append("Dataflow Gen2 provides visual debugging - useful for troubleshooting")

        if state.business.use_case == "analytics":
            recommendations.append("Gold layer will be optimized for Power BI DirectQuery")

        return recommendations

    def _get_warnings(self, state: PipelineState, architecture: Dict) -> List[str]:
        """Get architecture warnings"""

        warnings = []

        if state.source.location == "on_premise":
            warnings.append("Ensure On-Premises Data Gateway is configured before deployment")

        if state.source.volume_gb and state.source.volume_gb > 500:
            warnings.append("Large data volume - initial load may take several hours")

        return warnings

    def _format_architecture(
        self,
        state: PipelineState,
        architecture: Dict,
        recommendations: List[str],
        warnings: List[str]
    ) -> str:
        """Format architecture as readable message"""

        parts = [f"## Pipeline Architecture: {architecture['pattern'].replace('_', ' ').title()}\n"]
        parts.append(f"*{architecture['description']}*\n")

        # Visual diagram
        parts.append("### Architecture Diagram")
        diagram = self._generate_diagram(architecture)
        parts.append(f"```\n{diagram}\n```\n")

        # Layer details
        parts.append("### Layer Details")
        for layer in architecture["layers"]:
            parts.append(f"\n**{layer['name'].title()} Layer** ({layer['component']})")
            parts.append(f"- Purpose: {layer['purpose']}")
            parts.append(f"- Naming: `{layer['naming']}`")

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

    def _generate_diagram(self, architecture: Dict) -> str:
        """Generate ASCII architecture diagram"""

        layers = architecture.get("layers", [])
        if not layers:
            return "No layers defined"

        # Build diagram
        boxes = []
        for layer in layers:
            box = f"[{layer['name'].upper()}]\n{layer['component']}"
            boxes.append(box)

        # Simple horizontal flow
        return " --> ".join([f"[{l['name'].upper()}]" for l in layers])
