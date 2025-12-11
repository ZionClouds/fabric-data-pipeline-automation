"""
Deployment Service for AI Pipeline

Orchestrates the full deployment workflow:
1. Validates configuration
2. Creates necessary resources (connections, environments)
3. Generates notebook (if PII/transformations needed)
4. Generates pipeline
5. Creates schedule (if enabled)
6. Deploys to Fabric
"""

from __future__ import annotations
import logging
import base64
import json
from typing import Optional, Dict, Any

from services.ai_pipeline.models import (
    PipelineConfig,
    DeployResponse,
)
from services.ai_pipeline.notebook_generator import NotebookGenerator
from services.ai_pipeline.pipeline_generator import PipelineGenerator
from services.ai_pipeline.resource_manager import ResourceManager

logger = logging.getLogger(__name__)


class DeploymentService:
    """
    Orchestrates the complete deployment of AI-generated pipelines.

    This service coordinates:
    - Resource Manager (connections, environments, lakehouses)
    - Notebook Generator (PII detection notebooks)
    - Pipeline Generator (Fabric pipeline JSON)
    """

    def __init__(self, access_token: str):
        """
        Initialize the deployment service.

        Args:
            access_token: Bearer token for Fabric API authentication
        """
        self.access_token = access_token
        self.resource_manager = ResourceManager(access_token)
        self.notebook_generator = NotebookGenerator()
        self.pipeline_generator = PipelineGenerator()

    async def deploy(self, config: PipelineConfig) -> DeployResponse:
        """
        Deploy a complete pipeline based on configuration.

        Args:
            config: Complete pipeline configuration

        Returns:
            DeployResponse with deployment status and details
        """
        try:
            logger.info(f"Starting deployment for pipeline: {config.pipeline_name}")

            # Step 1: Validate workspace access
            workspace_valid = await self.resource_manager.validate_workspace_access(
                config.workspace_id
            )
            if not workspace_valid:
                return DeployResponse(
                    success=False,
                    message="Cannot access the specified workspace. Please check permissions."
                )

            # Step 2: Get or create connection for source
            connection = await self._setup_connection(config)
            if connection:
                config.connection_id = connection.get("id")

            # Step 3: Get default lakehouse
            lakehouse = await self.resource_manager.get_default_lakehouse(
                config.workspace_id
            )
            if lakehouse:
                config.lakehouse_id = lakehouse.get("id")

            # Step 4: Create environment if PII detection is needed
            notebook_id = None
            if config.pii.enabled:
                environment = await self.resource_manager.get_or_create_presidio_environment(
                    config.workspace_id
                )
                if environment:
                    config.environment_id = environment.get("id")

                # Generate and deploy notebook
                notebook_id = await self._deploy_notebook(config)
                config.notebook_id = notebook_id

            # Step 5: Generate pipeline definition
            pipeline_definition = self.pipeline_generator.generate_pipeline(
                config,
                notebook_id=notebook_id
            )

            # Validate pipeline
            validation_errors = self.pipeline_generator.validate_pipeline(pipeline_definition)
            if validation_errors:
                return DeployResponse(
                    success=False,
                    message=f"Pipeline validation failed: {', '.join(validation_errors)}"
                )

            # Step 6: Deploy pipeline to Fabric
            pipeline = await self.resource_manager.create_pipeline(
                config.workspace_id,
                config.pipeline_name,
                pipeline_definition
            )
            pipeline_id = pipeline.get("id")

            # Step 7: Create schedule if enabled
            if config.schedule.enabled:
                schedule_config = self.pipeline_generator.generate_schedule(config)
                if schedule_config:
                    await self.resource_manager.create_schedule(
                        config.workspace_id,
                        pipeline_id,
                        schedule_config
                    )

            # Generate Fabric portal URL
            fabric_url = self.resource_manager.get_fabric_portal_url(
                config.workspace_id,
                "pipeline",
                pipeline_id
            )

            logger.info(f"Deployment completed successfully: {pipeline_id}")

            return DeployResponse(
                success=True,
                pipeline_id=pipeline_id,
                pipeline_name=config.pipeline_name,
                notebook_id=notebook_id,
                message=self._generate_success_message(config, pipeline_id, notebook_id),
                fabric_url=fabric_url
            )

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return DeployResponse(
                success=False,
                message=f"Deployment failed: {str(e)}"
            )

    async def _setup_connection(self, config: PipelineConfig) -> Optional[Dict[str, Any]]:
        """Set up connection for source data."""
        try:
            if not config.source.storage_account:
                logger.warning("No storage account specified, skipping connection setup")
                return None

            connection = await self.resource_manager.get_or_create_blob_connection(
                config.workspace_id,
                config.source.storage_account,
                config.source.container or "data"
            )

            return connection

        except Exception as e:
            logger.error(f"Error setting up connection: {e}")
            return None

    async def _deploy_notebook(self, config: PipelineConfig) -> Optional[str]:
        """Generate and deploy notebook for PII detection."""
        try:
            # Generate notebook content
            notebook_content = self.notebook_generator.generate_notebook(config)

            # Convert to ipynb format
            ipynb_json = self._create_ipynb_json(notebook_content, config)

            # Encode as base64
            notebook_base64 = base64.b64encode(
                json.dumps(ipynb_json).encode()
            ).decode()

            # Create notebook in Fabric
            notebook_name = f"{config.pipeline_name}_Notebook"
            notebook = await self.resource_manager.create_notebook(
                config.workspace_id,
                notebook_name,
                notebook_base64,
                environment_id=config.environment_id
            )

            return notebook.get("id")

        except Exception as e:
            logger.error(f"Error deploying notebook: {e}")
            return None

    def _create_ipynb_json(
        self,
        notebook_content: str,
        config: PipelineConfig
    ) -> Dict[str, Any]:
        """
        Create Jupyter notebook JSON structure.

        Args:
            notebook_content: Python code content
            config: Pipeline configuration

        Returns:
            Jupyter notebook JSON structure
        """
        return {
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.10"
                },
                "trident": {
                    "lakehouse": {
                        "default_lakehouse": config.lakehouse_id,
                        "default_lakehouse_name": "DefaultLakehouse"
                    }
                }
            },
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        f"# {config.pipeline_name} - Data Processing Notebook\n",
                        "\n",
                        "Auto-generated notebook for data processing with PII detection.\n",
                        "\n",
                        "**Features:**\n",
                        f"- PII Detection: {'Enabled' if config.pii.enabled else 'Disabled'}\n",
                        f"- Masking Type: {config.pii.masking_type or 'N/A'}\n",
                        f"- Source: {config.source.folder_path or 'data'}\n",
                        f"- Destination: {config.destination.table_name or 'output_table'}\n"
                    ]
                },
                {
                    "cell_type": "code",
                    "metadata": {},
                    "source": notebook_content.split('\n'),
                    "execution_count": None,
                    "outputs": []
                }
            ]
        }

    def _generate_success_message(
        self,
        config: PipelineConfig,
        pipeline_id: str,
        notebook_id: Optional[str]
    ) -> str:
        """Generate success message with deployment details."""
        message_parts = [
            f"🎉 Pipeline '{config.pipeline_name}' deployed successfully!",
            "",
            "**Deployed Resources:**",
            f"- Pipeline ID: {pipeline_id}"
        ]

        if notebook_id:
            message_parts.append(f"- Notebook ID: {notebook_id}")

        if config.lakehouse_id:
            message_parts.append(f"- Lakehouse ID: {config.lakehouse_id}")

        if config.environment_id:
            message_parts.append(f"- Environment ID: {config.environment_id}")

        message_parts.extend([
            "",
            "**Configuration Summary:**",
            f"- Source: {config.source.storage_account}/{config.source.container}/{config.source.folder_path or '*'}",
            f"- File Format: {config.source.file_format.value if config.source.file_format else 'auto-detect'}",
            f"- Destination: {config.destination.target.value}/{config.destination.table_name or 'output'}",
        ])

        if config.pii.enabled:
            message_parts.append(f"- PII Masking: {config.pii.masking_type or 'redact'}")

        if config.schedule.enabled:
            message_parts.append(f"- Schedule: {config.schedule.frequency} at {config.schedule.time or '02:00'} {config.schedule.timezone}")

        return "\n".join(message_parts)

    # =========================================================================
    # PREVIEW METHODS
    # =========================================================================

    def preview_pipeline(self, config: PipelineConfig) -> Dict[str, Any]:
        """
        Generate a preview of the pipeline without deploying.

        Args:
            config: Pipeline configuration

        Returns:
            Pipeline definition and validation results
        """
        pipeline_definition = self.pipeline_generator.generate_pipeline(config)
        validation_errors = self.pipeline_generator.validate_pipeline(pipeline_definition)

        return {
            "pipeline": pipeline_definition,
            "validation_errors": validation_errors,
            "is_valid": len(validation_errors) == 0
        }

    def preview_notebook(self, config: PipelineConfig) -> Dict[str, Any]:
        """
        Generate a preview of the notebook code without deploying.

        Args:
            config: Pipeline configuration

        Returns:
            Notebook structure with name, content, and base64 encoded content
        """
        return self.notebook_generator.generate_notebook(config)

    def preview_schedule(self, config: PipelineConfig) -> Dict[str, Any]:
        """
        Generate a preview of the schedule configuration.

        Args:
            config: Pipeline configuration

        Returns:
            Schedule configuration
        """
        return self.pipeline_generator.generate_schedule(config)

    # =========================================================================
    # VALIDATION METHODS
    # =========================================================================

    async def validate_config(self, config: PipelineConfig) -> Dict[str, Any]:
        """
        Validate pipeline configuration before deployment.

        Args:
            config: Pipeline configuration to validate

        Returns:
            Validation results with errors and warnings
        """
        errors = []
        warnings = []

        # Required fields
        if not config.workspace_id:
            errors.append("Workspace ID is required")

        if not config.pipeline_name:
            errors.append("Pipeline name is required")

        # Source validation
        if not config.source.storage_account:
            errors.append("Source storage account is required")

        if not config.source.container:
            warnings.append("Container not specified, will use default")

        # PII validation
        if config.pii.enabled and not config.pii.masking_type:
            warnings.append("PII enabled but no masking type specified, will use 'redact'")

        # Destination validation
        if not config.destination.table_name:
            warnings.append("Destination table name not specified, will use 'output_table'")

        # Workspace access
        if config.workspace_id:
            workspace_valid = await self.resource_manager.validate_workspace_access(
                config.workspace_id
            )
            if not workspace_valid:
                errors.append("Cannot access the specified workspace")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
