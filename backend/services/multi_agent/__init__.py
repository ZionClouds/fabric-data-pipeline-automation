"""
Multi-Agent Pipeline Architect System

A multi-agent AI system for designing and deploying Microsoft Fabric data pipelines.
The system uses specialized agents coordinated by an orchestrator to understand
user requirements, design optimal architectures, and generate deployment packages.

Agents:
- Orchestrator: Coordinates all agents and manages conversation flow
- Discovery Agent: Understands the "why" - business context and requirements
- Source Analyst: Expert on source systems, connections, and extraction strategies
- Fabric Architect: Designs optimal pipeline architecture using Fabric components
- Transform Expert: Plans data transformations, PII handling, and quality rules
- Deploy Agent: Generates pipeline definitions and deployment packages
"""

from .orchestrator import OrchestratorAgent
from .state_manager import PipelineState, PipelineStage, state_manager
from .base_agent import BaseAgent, AgentResponse

__all__ = [
    "OrchestratorAgent",
    "PipelineState",
    "PipelineStage",
    "state_manager",
    "BaseAgent",
    "AgentResponse",
]
