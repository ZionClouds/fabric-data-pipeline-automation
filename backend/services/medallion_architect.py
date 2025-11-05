"""
Medallion Architecture Specialist

Enhanced support for building Bronze/Silver/Gold (Medallion) architectures in Fabric.
Provides stage-by-stage guidance with latest best practices.
"""

import logging
from typing import Dict, Any, List
from services.azure_ai_agent_service import AzureAIAgentService

logger = logging.getLogger(__name__)


class MedallionArchitectService:
    """
    Specialized service for Medallion Architecture guidance
    """

    def __init__(self):
        self.layers = {
            "bronze": {
                "purpose": "Raw data ingestion (as-is from source)",
                "technologies": ["Data Pipeline", "Copy Activity", "Dataflow Gen2"],
                "best_practices": [
                    "Preserve source data exactly as-is",
                    "Add metadata (ingestion timestamp, source system)",
                    "Use Delta format for ACID transactions",
                    "Partition by ingestion date"
                ]
            },
            "silver": {
                "purpose": "Cleansed, validated, deduplicated data",
                "technologies": ["Dataflow Gen2", "Notebooks", "Spark"],
                "best_practices": [
                    "Data quality checks",
                    "Schema validation",
                    "Deduplication",
                    "Type conversions",
                    "PII masking if needed"
                ]
            },
            "gold": {
                "purpose": "Business-level aggregates, ready for consumption",
                "technologies": ["Dataflow Gen2", "Notebooks", "Power BI"],
                "best_practices": [
                    "Business-level aggregations",
                    "Star schema for reporting",
                    "Direct Lake for Power BI",
                    "Optimized for query performance"
                ]
            }
        }

    async def get_medallion_guidance(
        self,
        source: str,
        data_volume: str,
        frequency: str,
        business_use_case: str,
        agent_service: AzureAIAgentService
    ) -> Dict[str, Any]:
        """
        Get comprehensive medallion architecture guidance with latest best practices

        Args:
            source: Source system (e.g., "SQL Server" or "SharePoint")
            data_volume: Data size (e.g., "50GB")
            frequency: Update frequency (e.g., "daily")
            business_use_case: What the data is used for (e.g., "sales analytics")
            agent_service: Initialized agent service for Bing searches

        Returns:
            Complete medallion architecture plan with latest recommendations
        """
        logger.info(f"Generating medallion architecture for {source}")

        # Let the AI agent decide on storage through Bing search
        prompt = f"""I need to build a complete MEDALLION ARCHITECTURE (Bronze → Silver → Gold) in Microsoft Fabric.

REQUIREMENTS:
• Source: {source}
• Data Volume: {data_volume}
• Update Frequency: {frequency}
• Business Use Case: {business_use_case}

⚠️ CRITICAL FIRST STEP - SEARCH FOR STORAGE BEST PRACTICES:
Before providing recommendations, search Bing for:
"Microsoft Fabric medallion architecture {source} storage best practices 2024 2025"

Based on your search, YOU MUST DECIDE:
1. Is {source} a file-based source (SharePoint, files, FTP, etc.) or structured source (SQL Server, databases, APIs)?
2. What storage should be used for each layer?
   - File-based sources typically use: Bronze=ADLS Gen2 (preserve files), Silver=Lakehouse, Gold=Lakehouse
   - Structured sources typically use: Bronze=Lakehouse, Silver=Lakehouse, Gold=Lakehouse
   - BUT search for the LATEST recommendations - these may have changed!

## 🎯 YOUR TASK:
Search and provide a complete medallion architecture plan with:

## 🥉 BRONZE LAYER (Raw Ingestion)
1. **STORAGE DECISION**: ADLS Gen2 or Lakehouse? (search for latest guidance)
2. **WHY**: Explain your storage choice based on {source} characteristics
3. Recommended ingestion method for {source}
4. Latest connector features/optimizations
5. File format recommendations
6. Partitioning strategy
7. Metadata to capture

## 🥈 SILVER LAYER (Cleansed Data)
1. **STORAGE DECISION**: What storage? (typically Lakehouse for Delta tables)
2. **WHY**: Explain the choice
3. Best transformation approach (Dataflow Gen2 vs Notebooks)
4. Data quality patterns
5. Deduplication strategies
6. Schema evolution handling
7. Performance optimizations for {data_volume}
8. How to read from Bronze and write to Silver (consider storage types)

## 🥇 GOLD LAYER (Business Ready)
1. **STORAGE DECISION**: What storage? (typically Lakehouse for Direct Lake)
2. **WHY**: Explain the choice
3. Aggregation patterns for {business_use_case}
4. Power BI integration (Direct Lake setup)
5. Optimization for query performance
6. Materialized views vs computed columns

## 📊 OVERALL ARCHITECTURE
1. Complete data flow with storage types (Source → Bronze Storage → Silver Storage → Gold Storage → Power BI)
2. Pipeline orchestration approach
3. Error handling and monitoring
4. Cost optimization tips (compare storage costs)
5. Incremental processing strategy for {frequency} updates
6. Data movement strategy between storage types (if different)

For each layer, provide:
- ✅ Recommended approach
- 💾 STORAGE TYPE and WHY
- 📊 Expected performance/cost impact
- 🔗 Source documentation URLs
- ⚠️ Common pitfalls to avoid

IMPORTANT: Base your storage decisions on LATEST 2024-2025 best practices from Bing search, not assumptions!"""

        try:
            # Let the AI agent search and decide on storage
            response = await agent_service.chat(
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse and structure the response
            return {
                "success": True,
                "architecture_plan": response.get("content", ""),
                "bing_search_used": response.get("bing_grounding_used", False),
                "source": source,
                "data_volume": data_volume,
                "frequency": frequency,
                "layers": self.layers
            }

        except Exception as e:
            logger.error(f"Error generating medallion guidance: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_layer_sequence(self) -> List[str]:
        """
        Get the recommended build sequence for medallion architecture
        """
        return [
            "bronze",  # Build Bronze first - raw data foundation
            "silver",  # Then Silver - cleansed data
            "gold"     # Finally Gold - business aggregates
        ]

    def get_pipeline_template(
        self,
        layer: str,
        source: str,
        destination: str
    ) -> Dict[str, Any]:
        """
        Get a generic template pipeline configuration for a specific layer

        NOTE: This provides a basic template. The AI agent will provide specific
        storage recommendations through Bing search in the architecture plan.

        Args:
            layer: "bronze", "silver", or "gold"
            source: Source system or previous layer
            destination: Destination (lakehouse, warehouse, or ADLS Gen2)

        Returns:
            Generic pipeline template configuration
        """
        templates = {
            "bronze": {
                "pipeline_name": f"Bronze_Ingest_from_{source}",
                "activities": [
                    {
                        "type": "Copy Activity",
                        "name": "Ingest_Raw_Data",
                        "description": "Ingest data as-is from source (storage type determined by AI agent recommendations)",
                        "settings": {
                            "destination": "As recommended by AI agent (ADLS Gen2 for files, Lakehouse for structured)",
                            "format": "As recommended by AI agent",
                            "mode": "As recommended (Incremental/Full)",
                            "metadata": ["ingestion_timestamp", "source_system"],
                            "partition": "As recommended by AI agent"
                        }
                    }
                ],
                "schedule": "Based on source type and frequency requirements",
                "error_handling": "Retry 3 times, then alert"
            },
            "silver": {
                "pipeline_name": f"Silver_Cleanse_from_Bronze",
                "activities": [
                    {
                        "type": "Dataflow Gen2",
                        "name": "Cleanse_and_Validate",
                        "description": "Apply data quality rules and transformations",
                        "transformations": [
                            "Read from Bronze layer (format depends on storage type)",
                            "Remove duplicates",
                            "Validate schemas",
                            "Handle nulls",
                            "Type conversions",
                            "Business rule validations"
                        ],
                        "settings": {
                            "destination": "Lakehouse (Delta tables)",
                            "format": "Delta",
                            "merge_mode": "SCD Type 2 or Upsert (as needed)",
                            "partition": "date"
                        }
                    }
                ],
                "schedule": "After Bronze completion",
                "dependencies": ["Bronze pipeline"]
            },
            "gold": {
                "pipeline_name": f"Gold_Aggregate_from_Silver",
                "activities": [
                    {
                        "type": "Dataflow Gen2 or Notebook",
                        "name": "Create_Business_Aggregates",
                        "description": "Build business-ready datasets",
                        "aggregations": [
                            "Daily sales by region",
                            "Customer lifetime value",
                            "Product performance metrics",
                            "Trend analysis"
                        ],
                        "settings": {
                            "format": "Delta",
                            "optimization": "Direct Lake enabled",
                            "indexing": "For common filters",
                            "caching": "Materialized views for expensive queries"
                        }
                    }
                ],
                "schedule": "After Silver completion",
                "dependencies": ["Silver pipeline"],
                "consumers": ["Power BI", "Reports", "APIs"]
            }
        }

        return templates.get(layer, {})


# Global medallion architect service
medallion_service = MedallionArchitectService()
