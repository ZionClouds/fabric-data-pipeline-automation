"""
Orchestrator Agent

The Chief Pipeline Architect that coordinates all specialist agents.
Manages the conversation flow and synthesizes insights from all agents.
"""

from typing import Dict, Any, List, Optional
import logging
import asyncio

from .base_agent import AgentResponse
from .state_manager import PipelineState, PipelineStage, state_manager
from .discovery_agent import DiscoveryAgent
from .source_analyst import SourceAnalystAgent
from .fabric_architect import FabricArchitectAgent
from .transform_expert import TransformExpertAgent
from .deploy_agent import DeployAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    Orchestrator Agent - Coordinates all specialist agents.

    Responsibilities:
    - Manage conversation state and flow
    - Decide which agent(s) to call
    - Synthesize insights from multiple agents
    - Present unified responses to user
    - Handle user confirmations and decisions
    """

    def __init__(self, ai_service=None, fabric_service=None):
        self.ai_service = ai_service
        self.fabric_service = fabric_service

        # Initialize specialist agents
        self.discovery = DiscoveryAgent(ai_service)
        self.source_analyst = SourceAnalystAgent(ai_service)
        self.fabric_architect = FabricArchitectAgent(ai_service)
        self.transform_expert = TransformExpertAgent(ai_service)
        self.deploy = DeployAgent(ai_service, fabric_service)

        self.logger = logging.getLogger("orchestrator")

    async def process_message(
        self,
        workspace_id: str,
        user_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message through the multi-agent system.

        Returns a response dict with:
        - message: The response to show the user
        - stage: Current pipeline stage
        - state_summary: Summary of collected requirements
        - ready_to_deploy: Whether we have everything needed
        """

        # Get or create state for this session
        state = state_manager.get_state(workspace_id, user_id)

        # Add message to conversation history
        state.conversation_history.append({"role": "user", "content": message})

        # Update state from message
        state.update_from_message(message)

        self.logger.info(f"Processing message. Stage: {state.stage}, Summary: {state.get_summary()}")

        # Decide what to do based on current stage
        response = await self._route_message(state, message)

        # Add response to history
        state.conversation_history.append({"role": "assistant", "content": response["message"]})

        return response

    async def _route_message(self, state: PipelineState, message: str) -> Dict[str, Any]:
        """Route message to appropriate agent(s) based on stage"""

        message_lower = message.lower()

        # Check for user confirmations/decisions
        if self._is_confirmation(message_lower):
            return await self._handle_confirmation(state, message)

        if self._is_modification_request(message_lower):
            return await self._handle_modification(state, message)

        # Route based on stage
        if state.stage == PipelineStage.INITIAL:
            return await self._handle_initial(state, message)

        elif state.stage == PipelineStage.DISCOVERY:
            return await self._handle_discovery(state, message)

        elif state.stage == PipelineStage.ANALYZING:
            return await self._handle_analyzing(state, message)

        elif state.stage == PipelineStage.DESIGNING:
            return await self._handle_designing(state, message)

        elif state.stage == PipelineStage.REVIEWING:
            return await self._handle_reviewing(state, message)

        elif state.stage == PipelineStage.DEPLOYING:
            return await self._handle_deploying(state, message)

        else:
            return await self._handle_initial(state, message)

    async def _handle_initial(self, state: PipelineState, message: str) -> Dict[str, Any]:
        """Handle initial message - start with Discovery"""

        state.stage = PipelineStage.DISCOVERY

        # Call Discovery Agent
        response = await self.discovery.process(state, message)

        # Check if Discovery has enough info
        if response.is_complete:
            # Move to analyzing phase
            state.stage = PipelineStage.ANALYZING
            return await self._run_specialist_analysis(state)
        else:
            return self._format_response(state, response.message)

    async def _handle_discovery(self, state: PipelineState, message: str) -> Dict[str, Any]:
        """Continue discovery phase"""

        response = await self.discovery.process(state, message)

        if response.is_complete:
            state.stage = PipelineStage.ANALYZING
            return await self._run_specialist_analysis(state)
        else:
            return self._format_response(state, response.message)

    async def _run_specialist_analysis(self, state: PipelineState) -> Dict[str, Any]:
        """Run all specialist agents in parallel for analysis"""

        self.logger.info("Running specialist analysis in parallel...")

        # Run specialists in parallel
        source_task = self.source_analyst.process(state, "")
        architect_task = self.fabric_architect.process(state, "")
        transform_task = self.transform_expert.process(state, "")

        results = await asyncio.gather(
            source_task,
            architect_task,
            transform_task,
            return_exceptions=True
        )

        # Collect insights
        source_result = results[0] if not isinstance(results[0], Exception) else None
        architect_result = results[1] if not isinstance(results[1], Exception) else None
        transform_result = results[2] if not isinstance(results[2], Exception) else None

        # Store insights
        state.agent_insights = {
            "source_analyst": source_result.insights if source_result else {},
            "fabric_architect": architect_result.insights if architect_result else {},
            "transform_expert": transform_result.insights if transform_result else {},
        }

        # Move to designing stage
        state.stage = PipelineStage.DESIGNING

        # Synthesize and present design
        return await self._present_design(state, source_result, architect_result, transform_result)

    async def _present_design(
        self,
        state: PipelineState,
        source_result: Optional[AgentResponse],
        architect_result: Optional[AgentResponse],
        transform_result: Optional[AgentResponse]
    ) -> Dict[str, Any]:
        """Synthesize specialist insights and present unified design"""

        # Collect all warnings
        all_warnings = []
        if source_result and source_result.warnings:
            all_warnings.extend(source_result.warnings)
        if architect_result and architect_result.warnings:
            all_warnings.extend(architect_result.warnings)
        if transform_result and transform_result.warnings:
            all_warnings.extend(transform_result.warnings)

        # Collect all recommendations
        all_recommendations = []
        if source_result and source_result.recommendations:
            all_recommendations.extend(source_result.recommendations[:2])
        if architect_result and architect_result.recommendations:
            all_recommendations.extend(architect_result.recommendations[:2])
        if transform_result and transform_result.recommendations:
            all_recommendations.extend(transform_result.recommendations[:2])

        # Build unified design message
        message = self._build_design_message(
            state,
            source_result,
            architect_result,
            transform_result,
            all_warnings,
            all_recommendations
        )

        state.stage = PipelineStage.REVIEWING

        return self._format_response(
            state,
            message,
            ready_to_deploy=len([w for w in all_warnings if "required" in w.lower() or "must" in w.lower()]) == 0
        )

    def _build_design_message(
        self,
        state: PipelineState,
        source_result: Optional[AgentResponse],
        architect_result: Optional[AgentResponse],
        transform_result: Optional[AgentResponse],
        warnings: List[str],
        recommendations: List[str]
    ) -> str:
        """Build unified design presentation"""

        parts = ["## Pipeline Design Summary\n"]

        # Prerequisites/Warnings first
        blockers = [w for w in warnings if "gateway" in w.lower() or "required" in w.lower()]
        if blockers:
            parts.append("### Prerequisites Required")
            for blocker in blockers:
                parts.append(f"- ⚠️ {blocker}")
            parts.append("")

        # Source summary
        parts.append("### Source Configuration")
        parts.append(f"- **Type**: {state.source.type or 'Unknown'}")
        parts.append(f"- **Location**: {state.source.location or 'Unknown'}")
        if state.source.volume_gb:
            parts.append(f"- **Volume**: ~{state.source.volume_gb}GB")
        parts.append("")

        # Architecture
        if architect_result:
            parts.append("### Pipeline Architecture")
            parts.append(f"**Pattern**: {state.architecture.pattern or 'Medallion'}")
            parts.append("")

            # Visual diagram
            layers = state.architecture.layers or []
            if layers:
                diagram_parts = []
                for layer in layers:
                    if isinstance(layer, dict):
                        name = layer.get("name", "").upper()
                        comp = layer.get("component", "")
                    else:
                        name = layer.upper()
                        comp = state.architecture.components.get(layer, "")
                    diagram_parts.append(f"[{name}]\n{comp}")

                parts.append("```")
                parts.append(" → ".join([f"[{l.upper() if isinstance(l, str) else l.get('name', '').upper()}]" for l in layers]))
                parts.append("```")
                parts.append("")

        # Transformations
        if transform_result and state.transformations.needed:
            parts.append("### Data Transformations")
            if state.business.pii_likely:
                parts.append(f"- **PII Handling**: {state.transformations.pii_handling or 'Masking'} on columns: {', '.join(state.transformations.pii_columns or ['auto-detected'])}")
            if state.transformations.cleaning:
                parts.append(f"- **Cleaning**: {', '.join(state.transformations.cleaning[:3])}")
            parts.append("")

        # Schedule
        parts.append("### Schedule")
        freq = state.operations.frequency or "manual"
        if freq == "manual":
            parts.append("- **Type**: One-time execution")
        else:
            parts.append(f"- **Type**: Recurring ({freq})")
            if state.operations.schedule_time:
                parts.append(f"- **Time**: {state.operations.schedule_time}")
        parts.append("")

        # Recommendations
        if recommendations:
            parts.append("### Recommendations")
            for rec in recommendations[:4]:  # Limit to top 4
                parts.append(f"- {rec}")
            parts.append("")

        # Call to action
        parts.append("---")
        if blockers:
            parts.append("⚠️ **Please resolve the prerequisites above before deployment.**")
            parts.append("\nOnce resolved, say **'proceed'** or **'deploy'** to continue.")
        else:
            parts.append("✅ **Ready to deploy!**")
            parts.append("\nSay **'proceed'**, **'deploy'**, or **'yes'** to deploy this pipeline.")
            parts.append("Or tell me what you'd like to change.")

        return "\n".join(parts)

    async def _handle_analyzing(self, state: PipelineState, message: str) -> Dict[str, Any]:
        """Handle messages during analysis phase"""
        # Re-run analysis with any new information
        return await self._run_specialist_analysis(state)

    async def _handle_designing(self, state: PipelineState, message: str) -> Dict[str, Any]:
        """Handle messages during design phase"""
        # User might be providing additional info
        state.update_from_message(message)
        return await self._run_specialist_analysis(state)

    async def _handle_reviewing(self, state: PipelineState, message: str) -> Dict[str, Any]:
        """Handle messages during review phase"""

        if self._is_confirmation(message.lower()):
            return await self._handle_confirmation(state, message)

        # User wants changes
        return await self._handle_modification(state, message)

    async def _handle_deploying(self, state: PipelineState, message: str) -> Dict[str, Any]:
        """Handle deployment phase"""

        deploy_response = await self.deploy.process(state, message)

        state.stage = PipelineStage.COMPLETED

        return self._format_response(
            state,
            deploy_response.message,
            ready_to_deploy=True,
            pipeline_config=state.to_dict()
        )

    async def _handle_confirmation(self, state: PipelineState, message: str) -> Dict[str, Any]:
        """Handle user confirmation to proceed"""

        self.logger.info("User confirmed - preparing deployment")

        state.stage = PipelineStage.DEPLOYING

        # Get deployment package
        deploy_response = await self.deploy.process(state, message)

        return self._format_response(
            state,
            deploy_response.message,
            ready_to_deploy=True,
            pipeline_config=state.to_dict()
        )

    async def _handle_modification(self, state: PipelineState, message: str) -> Dict[str, Any]:
        """Handle modification request"""

        # Update state with new info
        state.update_from_message(message)

        # Re-run discovery to understand what changed
        discovery_response = await self.discovery.process(state, message)

        if discovery_response.is_complete:
            # Re-run specialist analysis
            return await self._run_specialist_analysis(state)
        else:
            return self._format_response(state, discovery_response.message)

    def _is_confirmation(self, message: str) -> bool:
        """Check if message is a confirmation"""
        confirmations = ["yes", "proceed", "deploy", "continue", "go ahead", "do it", "confirm", "ok", "okay"]
        return any(conf in message for conf in confirmations)

    def _is_modification_request(self, message: str) -> bool:
        """Check if message is asking to modify the design"""
        modifications = ["change", "modify", "update", "different", "instead", "rather", "actually", "no,"]
        return any(mod in message for mod in modifications)

    def _format_response(
        self,
        state: PipelineState,
        message: str,
        ready_to_deploy: bool = False,
        pipeline_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Format standardized response"""

        return {
            "message": message,
            "stage": state.stage.value,
            "state_summary": state.get_summary(),
            "ready_to_deploy": ready_to_deploy,
            "pipeline_config": pipeline_config or state.to_dict() if ready_to_deploy else None,
        }

    def reset_session(self, workspace_id: str, user_id: str) -> None:
        """Reset the session state"""
        state_manager.clear_state(workspace_id, user_id)
        self.logger.info(f"Session reset for {user_id} in workspace {workspace_id}")
