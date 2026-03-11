"""
Transform Expert Agent

Designs transformation logic, data quality rules, and medallion layer processing.
The Data Engineer of the pipeline architect team.
"""

from typing import Dict, Any, List
import logging

from .base_agent import BaseAgent, AgentResponse
from .state_manager import PipelineState

logger = logging.getLogger(__name__)


# Transformation catalog
TRANSFORMATION_CATALOG = {
    "cleaning": {
        "deduplication": {
            "description": "Remove duplicate records",
            "implementation": "Dataflow or Notebook",
            "pyspark": "df.dropDuplicates(['key_columns'])",
            "dataflow": "Remove Duplicates transform",
        },
        "null_handling": {
            "description": "Handle null/missing values",
            "options": ["drop_rows", "fill_default", "fill_previous", "fill_average"],
            "pyspark": "df.fillna() or df.dropna()",
            "dataflow": "Replace Values transform",
        },
        "type_conversion": {
            "description": "Convert data types",
            "pyspark": "df.withColumn('col', col('col').cast('type'))",
            "dataflow": "Change Type transform",
        },
        "trim_whitespace": {
            "description": "Remove leading/trailing whitespace",
            "pyspark": "df.withColumn('col', trim(col('col')))",
            "dataflow": "Trim transform",
        },
        "standardize_case": {
            "description": "Standardize text case (upper/lower)",
            "pyspark": "df.withColumn('col', upper(col('col')))",
            "dataflow": "Upper/Lower case transform",
        },
    },
    "pii_handling": {
        "detection": {
            "description": "Detect PII columns automatically",
            "detectable": ["email", "phone", "ssn", "credit_card", "address", "name", "ip_address"],
            "implementation": "Dataflow Gen2 with Presidio or custom Notebook",
        },
        "mask_redact": {
            "description": "Replace with placeholder",
            "example": "john@email.com → [REDACTED]",
            "pyspark": "regexp_replace(col, pattern, '[REDACTED]')",
        },
        "mask_partial": {
            "description": "Partial masking",
            "example": "john@email.com → j***@***.com",
            "pyspark": "Custom UDF for partial masking",
        },
        "mask_hash": {
            "description": "One-way hash (SHA256)",
            "example": "john@email.com → a1b2c3d4...",
            "pyspark": "sha2(col('column'), 256)",
        },
        "mask_fake": {
            "description": "Replace with fake but realistic data",
            "example": "John Doe → Jane Smith",
            "pyspark": "Faker library integration",
        },
    },
    "enrichment": {
        "lookup_join": {
            "description": "Join with reference/dimension data",
            "pyspark": "df.join(ref_df, 'key')",
            "dataflow": "Lookup or Join transform",
        },
        "derived_column": {
            "description": "Calculate new columns from existing",
            "pyspark": "df.withColumn('new', expr)",
            "dataflow": "Derived Column transform",
        },
        "date_parsing": {
            "description": "Parse and format dates",
            "pyspark": "to_date(col, 'format')",
            "dataflow": "Date parsing transforms",
        },
    },
    "aggregation": {
        "group_by": {
            "description": "Group and aggregate data",
            "pyspark": "df.groupBy('cols').agg(sum('x'), count('y'))",
            "dataflow": "Aggregate transform",
        },
        "window_functions": {
            "description": "Rolling aggregations, rankings",
            "pyspark": "Window.partitionBy().orderBy()",
        },
        "pivot": {
            "description": "Pivot rows to columns",
            "pyspark": "df.groupBy().pivot().agg()",
            "dataflow": "Pivot transform",
        },
    },
}

# PII column patterns
PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}",
    "ssn": r"\d{3}-\d{2}-\d{4}",
    "credit_card": r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}",
    "ip_address": r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
}

# Common PII column names
PII_COLUMN_NAMES = [
    "email", "mail", "e_mail",
    "phone", "telephone", "mobile", "cell",
    "ssn", "social_security", "tax_id",
    "credit_card", "card_number", "cc_number",
    "address", "street", "city", "zip", "postal",
    "first_name", "last_name", "full_name", "name",
    "dob", "date_of_birth", "birthday",
    "ip", "ip_address",
]


class TransformExpertAgent(BaseAgent):
    """
    Transform Expert Agent - Data transformation specialist.

    Responsibilities:
    - Design transformation logic
    - Plan PII detection and masking
    - Define data quality rules
    - Specify medallion layer transformations
    """

    def __init__(self, ai_service=None):
        super().__init__(
            name="transform_expert",
            role="Data Engineer",
            ai_service=ai_service
        )
        self.catalog = TRANSFORMATION_CATALOG

    @property
    def system_prompt(self) -> str:
        return """You are the Transform Expert Agent - a Data Engineering specialist.

## YOUR EXPERTISE
You have deep knowledge of:
- Data transformation patterns
- PII/PHI detection and masking
- Data quality rules and validation
- Medallion architecture transformations
- PySpark and Dataflow Gen2 implementations

## YOUR ROLE
Design transformation logic for each layer:
1. Bronze: Minimal (schema enforcement only)
2. Silver: Cleaning, deduplication, PII masking
3. Gold: Business aggregations, KPIs

## PII DETECTION
Look for columns like: email, phone, ssn, address, name, dob
Recommend masking strategies based on use case.

## OUTPUT FORMAT
Provide transformation specifications for each layer with code examples."""

    @property
    def required_info(self) -> List[str]:
        return [
            "use_case",
            "pii_status",
        ]

    @property
    def thinking_rules(self) -> Dict[str, Any]:
        return {
            "customer": {"check_pii": True, "columns": ["email", "phone", "address"]},
            "employee": {"check_pii": True, "columns": ["ssn", "salary", "address"]},
            "patient": {"check_pii": True, "compliance": "HIPAA"},
            "analytics": {"needs_aggregation": True},
            "power bi": {"needs_aggregation": True, "optimize_queries": True},
        }

    async def process(self, state: PipelineState, user_message: str) -> AgentResponse:
        """Design transformation logic"""

        # Analyze transformation needs
        transforms = self._analyze_transforms(state)

        # PII analysis
        pii_analysis = self._analyze_pii(state)

        # Layer-specific transforms
        layer_transforms = self._design_layer_transforms(state, transforms, pii_analysis)

        # Update state
        state.transformations.needed = len(transforms) > 0 or pii_analysis["pii_detected"]
        state.transformations.cleaning = transforms.get("cleaning", [])
        state.transformations.pii_handling = pii_analysis.get("recommended_action")
        state.transformations.pii_columns = pii_analysis.get("likely_columns", [])

        if state.business.use_case == "analytics":
            state.transformations.aggregations = ["daily_summaries", "kpis"]

        # Build insights
        insights = {
            "transforms_needed": state.transformations.needed,
            "pii_detected": pii_analysis["pii_detected"],
            "pii_columns": pii_analysis.get("likely_columns", []),
            "layer_transforms": layer_transforms,
        }

        recommendations = self._get_recommendations(state, pii_analysis)
        warnings = self._get_warnings(state, pii_analysis)

        # Format message
        message = self._format_transforms(state, layer_transforms, pii_analysis, recommendations)

        return AgentResponse(
            message=message,
            insights=insights,
            recommendations=recommendations,
            warnings=warnings,
            state_updates={"transformations": layer_transforms},
            is_complete=True,
        )

    def _analyze_transforms(self, state: PipelineState) -> Dict[str, List[str]]:
        """Analyze what transformations are needed"""

        transforms = {
            "cleaning": [],
            "enrichment": [],
            "aggregation": [],
        }

        # Standard cleaning for any data movement
        transforms["cleaning"].append("deduplication")
        transforms["cleaning"].append("null_handling")
        transforms["cleaning"].append("type_conversion")

        # Analytics use case needs aggregations
        if state.business.use_case == "analytics":
            transforms["aggregation"].append("group_by")
            transforms["aggregation"].append("summary_stats")

        # ML use case needs feature engineering
        if state.business.use_case == "ml":
            transforms["enrichment"].append("derived_column")
            transforms["enrichment"].append("feature_scaling")

        return transforms

    def _analyze_pii(self, state: PipelineState) -> Dict[str, Any]:
        """Analyze PII requirements"""

        pii_analysis = {
            "pii_detected": state.business.pii_likely,
            "likely_columns": [],
            "recommended_action": None,
            "masking_type": None,
        }

        if state.business.pii_likely:
            # Infer likely PII columns based on use case
            if "customer" in str(state.business.use_case).lower():
                pii_analysis["likely_columns"] = ["email", "phone", "address", "name"]
            elif "employee" in str(state.business.use_case).lower():
                pii_analysis["likely_columns"] = ["ssn", "salary", "address", "phone"]
            else:
                pii_analysis["likely_columns"] = ["email", "phone", "name"]

            # Recommend masking based on use case
            if state.business.use_case == "analytics":
                pii_analysis["recommended_action"] = "mask"
                pii_analysis["masking_type"] = "partial"  # Analytics needs some context
            elif state.business.use_case == "ml":
                pii_analysis["recommended_action"] = "hash"
                pii_analysis["masking_type"] = "hash"  # ML needs consistency
            else:
                pii_analysis["recommended_action"] = "mask"
                pii_analysis["masking_type"] = "redact"

        return pii_analysis

    def _design_layer_transforms(
        self,
        state: PipelineState,
        transforms: Dict,
        pii_analysis: Dict
    ) -> Dict[str, List[Dict]]:
        """Design transforms for each medallion layer"""

        layer_transforms = {}

        # Bronze layer - minimal transforms
        layer_transforms["bronze"] = [
            {
                "name": "Schema Enforcement",
                "description": "Enforce expected schema and data types",
                "implementation": "Automatic during Copy Activity",
            }
        ]

        # Silver layer - cleaning and PII
        silver_transforms = [
            {
                "name": "Deduplication",
                "description": "Remove duplicate records based on key columns",
                "implementation": "Dataflow Gen2 or Notebook",
                "pyspark": "df.dropDuplicates(['id'])",
            },
            {
                "name": "Null Handling",
                "description": "Handle null values appropriately",
                "implementation": "Dataflow Gen2 or Notebook",
                "pyspark": "df.fillna({'column': 'default'})",
            },
            {
                "name": "Type Standardization",
                "description": "Ensure consistent data types",
                "implementation": "Dataflow Gen2 or Notebook",
            },
        ]

        # Add PII masking if needed
        if pii_analysis["pii_detected"]:
            silver_transforms.append({
                "name": "PII Masking",
                "description": f"Mask PII columns: {', '.join(pii_analysis['likely_columns'])}",
                "masking_type": pii_analysis["masking_type"],
                "implementation": "Dataflow Gen2 (built-in) or Notebook with Presidio",
                "columns": pii_analysis["likely_columns"],
            })

        layer_transforms["silver"] = silver_transforms

        # Gold layer - aggregations (if analytics use case)
        if state.business.use_case in ["analytics", "ml"]:
            gold_transforms = [
                {
                    "name": "Business Aggregations",
                    "description": "Calculate business metrics and KPIs",
                    "implementation": "Notebook (PySpark)",
                    "pyspark": "df.groupBy('date', 'category').agg(sum('amount'), count('id'))",
                },
                {
                    "name": "Query Optimization",
                    "description": "Optimize table for Power BI queries",
                    "implementation": "Delta table optimization",
                    "pyspark": "df.write.format('delta').partitionBy('date').save()",
                },
            ]
            layer_transforms["gold"] = gold_transforms

        return layer_transforms

    def _get_recommendations(self, state: PipelineState, pii_analysis: Dict) -> List[str]:
        """Get transformation recommendations"""

        recommendations = []

        if pii_analysis["pii_detected"]:
            if pii_analysis["masking_type"] == "partial":
                recommendations.append("Partial masking preserves data utility for analytics while protecting identity")
            elif pii_analysis["masking_type"] == "hash":
                recommendations.append("Hashing maintains referential integrity for joins while anonymizing data")

        if state.business.use_case == "analytics":
            recommendations.append("Pre-aggregate common query patterns in Gold layer for faster Power BI performance")

        recommendations.append("Use Delta format for all layers to enable time travel and ACID transactions")

        return recommendations

    def _get_warnings(self, state: PipelineState, pii_analysis: Dict) -> List[str]:
        """Get transformation warnings"""

        warnings = []

        if pii_analysis["pii_detected"]:
            warnings.append("PII detected - ensure compliance with data protection regulations (GDPR, CCPA)")

        if state.source.volume_gb and state.source.volume_gb > 100:
            warnings.append("Large volume - consider incremental processing to reduce runtime")

        return warnings

    def _format_transforms(
        self,
        state: PipelineState,
        layer_transforms: Dict,
        pii_analysis: Dict,
        recommendations: List[str]
    ) -> str:
        """Format transformation design as readable message"""

        parts = ["## Transformation Design\n"]

        # PII Summary
        if pii_analysis["pii_detected"]:
            parts.append("### PII Handling")
            parts.append(f"- **Status**: PII likely present")
            parts.append(f"- **Columns**: {', '.join(pii_analysis['likely_columns'])}")
            parts.append(f"- **Action**: {pii_analysis['recommended_action'].title()} using {pii_analysis['masking_type']} method")
            parts.append("")

        # Layer transforms
        for layer, transforms in layer_transforms.items():
            parts.append(f"### {layer.title()} Layer Transforms")
            for transform in transforms:
                parts.append(f"\n**{transform['name']}**")
                parts.append(f"- {transform['description']}")
                parts.append(f"- Implementation: {transform['implementation']}")
                if "pyspark" in transform:
                    parts.append(f"- Code: `{transform['pyspark']}`")

        # Recommendations
        if recommendations:
            parts.append("\n### Recommendations")
            for rec in recommendations:
                parts.append(f"- {rec}")

        return "\n".join(parts)
