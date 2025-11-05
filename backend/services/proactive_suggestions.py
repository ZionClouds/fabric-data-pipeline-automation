"""
Proactive Suggestions Service

Provides intelligent, proactive suggestions during pipeline building.
Searches for latest best practices and optimization opportunities.
"""

import logging
from typing import Dict, Any, List, Optional
from services.azure_ai_agent_service import AzureAIAgentService
import config

logger = logging.getLogger(__name__)


class ProactiveSuggestionService:
    """
    Service for generating proactive suggestions during pipeline building
    """

    def __init__(self):
        # We'll use the existing agent service for searches
        self.agent_service = None  # Will be injected

    async def check_for_latest_updates(
        self,
        source: str,
        destination: str,
        agent_service: AzureAIAgentService
    ) -> Dict[str, Any]:
        """
        Proactively search for latest updates and best practices

        Args:
            source: Source system type (e.g., "SQL Server")
            destination: Destination system type (e.g., "Lakehouse")
            agent_service: Initialized agent service with Bing Grounding

        Returns:
            Dictionary with suggestions and latest updates
        """
        logger.info(f"Searching for latest best practices: {source} → {destination}")

        try:
            # Craft a proactive search query
            search_query = f"""Search for the LATEST Microsoft Fabric best practices for {source} to {destination} pipelines.

Focus on:
1. Latest connector updates and features (2024-2025)
2. Performance optimizations
3. Cost-saving recommendations
4. Deprecated patterns to avoid
5. New capabilities that improve this use case

Provide specific, actionable recommendations with:
- What changed and when
- Performance/cost impact (with numbers if available)
- Source documentation URLs

Be concise and prioritize the most impactful recommendations."""

            # Use the agent to search
            response = await agent_service.chat(
                messages=[{
                    "role": "user",
                    "content": search_query
                }]
            )

            return {
                "success": True,
                "source": source,
                "destination": destination,
                "recommendations": response.get("content", ""),
                "bing_search_used": response.get("bing_grounding_used", False),
                "search_query": search_query
            }

        except Exception as e:
            logger.error(f"Error searching for best practices: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "recommendations": None
            }

    async def pre_deployment_check(
        self,
        pipeline_config: Dict[str, Any],
        agent_service: AzureAIAgentService
    ) -> Dict[str, Any]:
        """
        Perform comprehensive pre-deployment optimization check

        Args:
            pipeline_config: Current pipeline configuration
            agent_service: Initialized agent service

        Returns:
            Dictionary with optimization suggestions
        """
        logger.info("Performing pre-deployment optimization check")

        try:
            # Extract pipeline details
            source = pipeline_config.get("source", {}).get("type", "Unknown")
            destination = pipeline_config.get("destination", {}).get("type", "Unknown")
            activities = pipeline_config.get("activities", [])

            # Create a detailed analysis prompt
            analysis_prompt = f"""⏸️ PRE-DEPLOYMENT OPTIMIZATION CHECK

I'm about to deploy a pipeline with these specifications:

SOURCE: {source}
DESTINATION: {destination}
ACTIVITIES: {len(activities)} activities
CONFIGURATION:
{self._format_pipeline_config(pipeline_config)}

Please perform a comprehensive optimization check:

1. Search for the LATEST best practices for this type of pipeline (2024-2025)
2. Identify any potential optimizations I'm missing
3. Check for deprecated patterns or better alternatives
4. Suggest performance improvements
5. Recommend cost optimizations
6. Validate against current Fabric best practices

For each recommendation, provide:
- ⚠️ Priority level (Critical/Important/Nice-to-have)
- 📊 Expected impact (performance/cost/reliability)
- 🔗 Source documentation
- ✅ How to implement

Be specific and actionable. Focus on the most impactful improvements."""

            # Get optimization recommendations
            response = await agent_service.chat(
                messages=[{
                    "role": "user",
                    "content": analysis_prompt
                }]
            )

            return {
                "success": True,
                "pipeline_config": pipeline_config,
                "optimization_recommendations": response.get("content", ""),
                "bing_search_used": response.get("bing_grounding_used", False),
                "ready_to_deploy": True  # User can still deploy, but with recommendations
            }

        except Exception as e:
            logger.error(f"Error in pre-deployment check: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "ready_to_deploy": True  # Don't block deployment on errors
            }

    def _format_pipeline_config(self, config: Dict[str, Any]) -> str:
        """
        Format pipeline config for readability
        """
        parts = []

        if config.get("pipeline_name"):
            parts.append(f"Name: {config['pipeline_name']}")

        if config.get("schedule"):
            parts.append(f"Schedule: {config['schedule']}")

        if config.get("activities"):
            parts.append(f"Activities: {', '.join([a.get('type', 'Unknown') for a in config['activities']])}")

        return "\n".join(parts) if parts else "Basic pipeline configuration"

    async def suggest_component_alternative(
        self,
        current_component: str,
        use_case: str,
        agent_service: AzureAIAgentService
    ) -> Dict[str, Any]:
        """
        Suggest alternative components based on latest best practices

        Args:
            current_component: Current component user is considering (e.g., "Copy Activity")
            use_case: The use case (e.g., "SQL to Lakehouse")
            agent_service: Initialized agent service

        Returns:
            Alternative suggestions with rationale
        """
        logger.info(f"Checking for alternatives to {current_component} for {use_case}")

        try:
            search_prompt = f"""The user is about to use {current_component} for {use_case}.

Search for:
1. Is {current_component} still the recommended approach in 2024-2025?
2. Are there better alternatives for this use case?
3. What are the latest Microsoft Fabric recommendations?

If there's a better alternative:
- Explain what changed and when
- Provide performance/cost comparison
- Give specific implementation guidance
- Include source URLs

If {current_component} is still optimal:
- Confirm it's the right choice
- Suggest any configuration optimizations
- Mention any recent improvements to this component

Be specific and cite latest documentation."""

            response = await agent_service.chat(
                messages=[{
                    "role": "user",
                    "content": search_prompt
                }]
            )

            return {
                "success": True,
                "current_component": current_component,
                "use_case": use_case,
                "recommendation": response.get("content", ""),
                "bing_search_used": response.get("bing_grounding_used", False)
            }

        except Exception as e:
            logger.error(f"Error checking component alternatives: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Global proactive suggestion service
proactive_service = ProactiveSuggestionService()
