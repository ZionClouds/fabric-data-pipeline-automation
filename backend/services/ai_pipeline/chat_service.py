"""
AI Chat Service for Pipeline Generation

Handles multi-turn conversations with users to gather pipeline requirements.
Uses Azure OpenAI for natural language understanding and response generation.
"""

from __future__ import annotations
import os
import json
import logging
from typing import Optional, Dict, Any, List, Tuple

# Try to import Azure OpenAI, fall back to standard OpenAI
try:
    from openai import AsyncAzureOpenAI
    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    AZURE_OPENAI_AVAILABLE = False

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from services.ai_pipeline.models import (
    ChatRequest,
    ChatResponse,
    ConversationContext,
    ConversationMessage,
    ConversationState,
    PipelineConfig,
    SourceConfig,
    PIIConfig,
    TransformationConfig,
    TransformationStep,
    DestinationConfig,
    ScheduleConfig,
    UseCaseAnalysis,
    IdentifiedActivity,
    MaskingType,
    FileFormat,
    DestinationType,
    TransformationType,
)

logger = logging.getLogger(__name__)


class AIChatService:
    """
    AI-powered chat service for gathering pipeline requirements.

    Handles multi-turn conversations to:
    1. Understand user's use case
    2. Identify required activities
    3. Gather source, transformation, PII, destination, and schedule details
    4. Generate pipeline configuration
    """

    def __init__(
        self,
        session_id: str,
        workspace_id: str,
        workspace_name: str,
        azure_endpoint: Optional[str] = None,
        azure_api_key: Optional[str] = None,
        azure_deployment: Optional[str] = None,
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize the chat service.

        Args:
            session_id: Unique session identifier
            workspace_id: Selected Fabric workspace ID
            workspace_name: Selected Fabric workspace name
            azure_endpoint: Azure OpenAI endpoint (optional, uses settings if not provided)
            azure_api_key: Azure OpenAI API key (optional, uses settings if not provided)
            azure_deployment: Azure OpenAI deployment name (optional, uses settings if not provided)
            openai_api_key: Standard OpenAI API key (fallback if Azure not available)
        """
        # Try to load from settings
        try:
            import settings
            self.azure_endpoint = azure_endpoint or settings.AZURE_OPENAI_ENDPOINT
            self.azure_api_key = azure_api_key or settings.AZURE_OPENAI_API_KEY
            self.azure_deployment = azure_deployment or settings.AZURE_OPENAI_DEPLOYMENT
            self.api_version = getattr(settings, 'AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
        except ImportError:
            self.azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
            self.azure_api_key = azure_api_key or os.getenv("AZURE_OPENAI_API_KEY")
            self.azure_deployment = azure_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-chat")
            self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        # Initialize client
        self.client = None
        self.use_azure = False

        if AZURE_OPENAI_AVAILABLE and self.azure_endpoint and self.azure_api_key:
            self.client = AsyncAzureOpenAI(
                api_version=self.api_version,
                azure_endpoint=self.azure_endpoint,
                api_key=self.azure_api_key
            )
            self.use_azure = True
            logger.info(f"Using Azure OpenAI with deployment: {self.azure_deployment}")
        elif OPENAI_AVAILABLE and self.openai_api_key:
            self.client = AsyncOpenAI(api_key=self.openai_api_key)
            logger.info("Using standard OpenAI")
        else:
            logger.warning("No OpenAI client available - will use rule-based responses")

        # Initialize context for this session
        self.context = ConversationContext(
            session_id=session_id,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            config=PipelineConfig(
                workspace_id=workspace_id,
                workspace_name=workspace_name
            )
        )

    # =========================================================================
    # MAIN CHAT HANDLER
    # =========================================================================

    async def process_message(self, message: str) -> ChatResponse:
        """
        Handle a chat message from the user.

        Args:
            message: User's message text

        Returns:
            ChatResponse with AI response and updated state
        """
        # Add user message to history
        self.context.messages.append(ConversationMessage(
            role="user",
            content=message
        ))

        # Process based on current state
        if self.context.state == ConversationState.INITIAL:
            response = await self._handle_initial_message(self.context, message)
        elif self.context.state == ConversationState.GATHERING_SOURCE:
            response = await self._handle_source_gathering(self.context, message)
        elif self.context.state == ConversationState.GATHERING_PII:
            response = await self._handle_pii_gathering(self.context, message)
        elif self.context.state == ConversationState.GATHERING_TRANSFORMATIONS:
            response = await self._handle_transformation_gathering(self.context, message)
        elif self.context.state == ConversationState.GATHERING_DESTINATION:
            response = await self._handle_destination_gathering(self.context, message)
        elif self.context.state == ConversationState.GATHERING_SCHEDULE:
            response = await self._handle_schedule_gathering(self.context, message)
        elif self.context.state == ConversationState.CONFIRMING:
            response = await self._handle_confirmation(self.context, message)
        else:
            response = await self._handle_general_message(self.context, message)

        # Add assistant message to history
        self.context.messages.append(ConversationMessage(
            role="assistant",
            content=response.message
        ))

        return response

    # =========================================================================
    # STATE HANDLERS
    # =========================================================================

    async def _handle_initial_message(
        self,
        context: ConversationContext,
        message: str
    ) -> ChatResponse:
        """Handle the initial user message - analyze use case."""

        # Analyze the use case using LLM
        analysis = await self._analyze_use_case(message)

        # Store analysis in context
        context.config.pipeline_description = analysis.description

        # Generate pipeline name from description
        context.config.pipeline_name = self._generate_pipeline_name(analysis.description)

        # Store the source type for later reference
        context.collected_fields.append(f"source_type:{analysis.use_case_type}")

        # Move to source gathering
        context.state = ConversationState.GATHERING_SOURCE

        # Build response
        activities_text = "\n".join([
            f"   {i+1}. {a.type} - {a.reason}"
            for i, a in enumerate(analysis.activities)
        ])

        # Determine source questions based on use case type
        message_lower = message.lower()
        if "sql" in message_lower or "database" in message_lower:
            source_questions = """**📦 SOURCE (Azure SQL Database)**
Please provide:
1. Server name? (e.g., myserver.database.windows.net)
2. Database name?
3. Table name(s) to transfer?"""
            options = None
        else:
            source_questions = """**📦 SOURCE (Blob Storage)**
Please provide:
1. Storage account name?
2. Container name?
3. Folder path? (e.g., sales/2024/)
4. File format? (CSV / Parquet / JSON)"""
            options = ["CSV", "Parquet", "JSON"]

        response_message = f"""I understand you want to create a data pipeline:

**Use Case:** {analysis.description}

**Activities I'll use:**
{activities_text}

Let me gather the required details.

{source_questions}"""

        return ChatResponse(
            session_id=context.session_id,
            message=response_message,
            state=context.state,
            config=context.config,
            options=options,
            is_complete=False
        )

    async def _handle_source_gathering(
        self,
        context: ConversationContext,
        message: str
    ) -> ChatResponse:
        """Handle source information gathering."""

        # Determine if this is SQL or blob source based on collected_fields
        is_sql_source = any(
            "source_type:database" in f or "source_type:sql" in f
            for f in context.collected_fields
        )

        # Parse source details from message
        source_info = await self._extract_source_info(message, context)

        # Update config based on source type
        if is_sql_source:
            # For SQL sources, map to our model
            if source_info.get("server_name") or source_info.get("storage_account"):
                server = source_info.get("server_name") or source_info.get("storage_account")
                context.config.source.storage_account = server
                context.collected_fields.append("server_name")
            if source_info.get("database_name") or source_info.get("container"):
                db = source_info.get("database_name") or source_info.get("container")
                context.config.source.container = db
                context.collected_fields.append("database_name")
            if source_info.get("table_name") or source_info.get("folder_path"):
                table = source_info.get("table_name") or source_info.get("folder_path")
                context.config.source.folder_path = table
                context.collected_fields.append("table_name")
            # SQL source doesn't need file format - set default
            if "file_format" not in context.collected_fields:
                context.config.source.file_format = FileFormat.PARQUET
                context.collected_fields.append("file_format")
        else:
            # Blob storage source
            if source_info.get("storage_account"):
                context.config.source.storage_account = source_info["storage_account"]
                context.collected_fields.append("storage_account")
            if source_info.get("container"):
                context.config.source.container = source_info["container"]
                context.collected_fields.append("container")
            if source_info.get("folder_path"):
                context.config.source.folder_path = source_info["folder_path"]
                context.collected_fields.append("folder_path")
            if source_info.get("file_format"):
                try:
                    context.config.source.file_format = FileFormat(source_info["file_format"].lower())
                except ValueError:
                    context.config.source.file_format = FileFormat.CSV
                context.collected_fields.append("file_format")

        # Check if we have all required source info
        if is_sql_source:
            required_source = ["server_name", "database_name", "table_name"]
            missing_questions = {
                "server_name": "What is the SQL server name? (e.g., myserver.database.windows.net)",
                "database_name": "What is the database name?",
                "table_name": "What table(s) do you want to transfer?"
            }
        else:
            required_source = ["storage_account", "container", "folder_path", "file_format"]
            missing_questions = {
                "storage_account": "What is the storage account name?",
                "container": "What is the container name?",
                "folder_path": "What is the folder path?",
                "file_format": "What is the file format? (CSV / Parquet / JSON)"
            }

        missing = [f for f in required_source if f not in context.collected_fields]

        if missing:
            # Ask for missing info
            questions = [missing_questions[f] for f in missing]

            return ChatResponse(
                session_id=context.session_id,
                message=f"I still need:\n" + "\n".join(f"- {q}" for q in questions),
                state=context.state,
                config=context.config,
                is_complete=False
            )

        # Move to PII gathering
        context.state = ConversationState.GATHERING_PII

        return ChatResponse(
            session_id=context.session_id,
            message="""Got the source details!

**🔒 SENSITIVE DATA**
Does this data contain PII/PHI (Personal/Health Information)?

Please choose:
- **Yes** - Data contains sensitive information
- **No** - No sensitive data""",
            state=context.state,
            config=context.config,
            options=["Yes", "No"],
            is_complete=False
        )

    async def _handle_pii_gathering(
        self,
        context: ConversationContext,
        message: str
    ) -> ChatResponse:
        """Handle PII/PHI configuration gathering."""

        message_lower = message.lower().strip()

        # Check if user said no to PII
        if message_lower in ["no", "n", "none", "no pii", "no sensitive data"]:
            context.config.pii.enabled = False
            context.state = ConversationState.GATHERING_TRANSFORMATIONS

            return ChatResponse(
                session_id=context.session_id,
                message="""No PII detection needed.

**🔄 TRANSFORMATIONS**
Do you need any transformations on this data?

Please describe what you need, or say "none":
- Filter rows (e.g., "only active customers")
- Select specific columns
- Rename columns
- Aggregate data
- Other transformations""",
                state=context.state,
                config=context.config,
                options=["None", "Filter", "Select columns", "Other"],
                is_complete=False
            )

        # User said yes to PII - check if masking type already provided
        if "masking_type" in context.collected_fields:
            # Already have masking type, move on
            context.state = ConversationState.GATHERING_TRANSFORMATIONS
            return await self._ask_transformations(context)

        # Check if masking type is in the message
        masking_keywords = {
            "redact": MaskingType.REDACT,
            "partial": MaskingType.PARTIAL,
            "fake": MaskingType.FAKE,
            "hash": MaskingType.HASH,
            "1": MaskingType.REDACT,
            "2": MaskingType.PARTIAL,
            "3": MaskingType.FAKE,
            "4": MaskingType.HASH,
        }

        for keyword, masking_type in masking_keywords.items():
            if keyword in message_lower:
                context.config.pii.enabled = True
                context.config.pii.masking_type = masking_type
                context.collected_fields.append("masking_type")
                context.state = ConversationState.GATHERING_TRANSFORMATIONS

                return ChatResponse(
                    session_id=context.session_id,
                    message=f"""PII detection enabled with **{masking_type.value}** masking.

At runtime, I'll:
1. Scan sample data to detect sensitive columns
2. Apply {masking_type.value} masking to all detected columns

**🔄 TRANSFORMATIONS**
Do you need any other transformations?

Please describe or say "none":
- Filter rows
- Select specific columns
- Other transformations""",
                    state=context.state,
                    config=context.config,
                    options=["None", "Filter", "Select columns", "Other"],
                    is_complete=False
                )

        # User said yes but didn't specify masking type
        if message_lower in ["yes", "y", "pii", "phi", "sensitive"]:
            context.config.pii.enabled = True

            return ChatResponse(
                session_id=context.session_id,
                message="""How would you like to mask the sensitive data?

1. **Redact** → `john@email.com` → `<EMAIL_ADDRESS>`
2. **Partial** → `john@email.com` → `j***@***.com`
3. **Fake** → `john@email.com` → `user_8x7k@masked.com`
4. **Hash** → `john@email.com` → `a1b2c3d4...`

Please choose (1-4 or name):""",
                state=context.state,
                config=context.config,
                options=["Redact", "Partial", "Fake", "Hash"],
                is_complete=False
            )

        # Couldn't understand, ask again
        return ChatResponse(
            session_id=context.session_id,
            message="Does this data contain PII/PHI? Please answer Yes or No.",
            state=context.state,
            config=context.config,
            options=["Yes", "No"],
            is_complete=False
        )

    async def _handle_transformation_gathering(
        self,
        context: ConversationContext,
        message: str
    ) -> ChatResponse:
        """Handle transformation requirements gathering."""

        message_lower = message.lower().strip()

        # Check if no transformations needed
        if message_lower in ["no", "n", "none", "no transformations", "skip"]:
            context.config.transformations.enabled = False
            context.state = ConversationState.GATHERING_DESTINATION

            return ChatResponse(
                session_id=context.session_id,
                message="""No additional transformations needed.

**📍 DESTINATION**
Where should the data be loaded?

1. **Files** - Load to Lakehouse Files section
2. **Tables** - Load to Lakehouse Tables (Delta)

Please choose:""",
                state=context.state,
                config=context.config,
                options=["Files", "Tables"],
                is_complete=False
            )

        # Parse transformations
        transformations = await self._extract_transformations(message)

        if transformations:
            context.config.transformations.enabled = True
            context.config.transformations.steps = transformations
            context.state = ConversationState.GATHERING_DESTINATION

            steps_text = "\n".join([
                f"   - {s.type.value}: {s.condition or s.columns or 'custom'}"
                for s in transformations
            ])

            return ChatResponse(
                session_id=context.session_id,
                message=f"""Got it! I'll apply these transformations:
{steps_text}

**📍 DESTINATION**
Where should the data be loaded?

1. **Files** - Load to Lakehouse Files section
2. **Tables** - Load to Lakehouse Tables (Delta)

Please choose:""",
                state=context.state,
                config=context.config,
                options=["Files", "Tables"],
                is_complete=False
            )

        # Couldn't parse, ask for clarification
        return ChatResponse(
            session_id=context.session_id,
            message="""Could you describe the transformations more specifically?

Examples:
- "Filter where status = 'active'"
- "Select only id, name, email columns"
- "No transformations needed"

What would you like?""",
            state=context.state,
            config=context.config,
            is_complete=False
        )

    async def _handle_destination_gathering(
        self,
        context: ConversationContext,
        message: str
    ) -> ChatResponse:
        """Handle destination configuration gathering."""

        message_lower = message.lower().strip()

        # Parse destination type
        if "file" in message_lower or message_lower == "1":
            context.config.destination.target = DestinationType.FILES
            context.state = ConversationState.GATHERING_SCHEDULE

            return ChatResponse(
                session_id=context.session_id,
                message="""Data will be loaded to Lakehouse **Files** section.

**⏰ SCHEDULE**
When should this pipeline run?

Please provide:
- Time (e.g., 2:00 AM)
- Timezone (e.g., UTC, EST, PST)

Example: "Daily at 2:00 AM UTC" """,
                state=context.state,
                config=context.config,
                is_complete=False
            )

        if "table" in message_lower or message_lower == "2":
            context.config.destination.target = DestinationType.TABLES

            # Check if table name provided
            table_name = await self._extract_table_name(message)
            if table_name:
                context.config.destination.table_name = table_name
                context.state = ConversationState.GATHERING_SCHEDULE

                return ChatResponse(
                    session_id=context.session_id,
                    message=f"""Data will be loaded to table: **{table_name}**

**⏰ SCHEDULE**
When should this pipeline run?

Please provide:
- Time (e.g., 2:00 AM)
- Timezone (e.g., UTC, EST, PST)

Example: "Daily at 2:00 AM UTC" """,
                    state=context.state,
                    config=context.config,
                    is_complete=False
                )
            else:
                return ChatResponse(
                    session_id=context.session_id,
                    message="What should the table be named?",
                    state=context.state,
                    config=context.config,
                    is_complete=False
                )

        # Check if just providing table name
        if context.config.destination.target == DestinationType.TABLES and not context.config.destination.table_name:
            context.config.destination.table_name = message.strip().replace(" ", "_")
            context.state = ConversationState.GATHERING_SCHEDULE

            return ChatResponse(
                session_id=context.session_id,
                message=f"""Table name set to: **{context.config.destination.table_name}**

**⏰ SCHEDULE**
When should this pipeline run?

Example: "Daily at 2:00 AM UTC" """,
                state=context.state,
                config=context.config,
                is_complete=False
            )

        return ChatResponse(
            session_id=context.session_id,
            message="Please choose: Files or Tables?",
            state=context.state,
            config=context.config,
            options=["Files", "Tables"],
            is_complete=False
        )

    async def _handle_schedule_gathering(
        self,
        context: ConversationContext,
        message: str
    ) -> ChatResponse:
        """Handle schedule configuration gathering."""

        # Parse schedule from message
        schedule = await self._extract_schedule(message)

        context.config.schedule.time = schedule.get("time", "02:00")
        context.config.schedule.timezone = schedule.get("timezone", "UTC")
        context.config.schedule.frequency = schedule.get("frequency", "daily")

        # Move to confirmation
        context.state = ConversationState.CONFIRMING

        # Build summary
        summary = self._build_pipeline_summary(context.config)

        return ChatResponse(
            session_id=context.session_id,
            message=f"""Perfect! Here's your pipeline summary:

{summary}

**Ready to deploy?**
- Type "deploy" or "yes" to create the pipeline
- Type "edit" to make changes
- Type "cancel" to start over""",
            state=context.state,
            config=context.config,
            options=["Deploy", "Edit", "Cancel"],
            is_complete=True
        )

    async def _handle_confirmation(
        self,
        context: ConversationContext,
        message: str
    ) -> ChatResponse:
        """Handle deployment confirmation."""

        message_lower = message.lower().strip()

        if message_lower in ["deploy", "yes", "y", "confirm", "create"]:
            context.state = ConversationState.DEPLOYING

            return ChatResponse(
                session_id=context.session_id,
                message="🚀 Starting deployment... This will create the pipeline, notebook, and configure the schedule.",
                state=context.state,
                config=context.config,
                is_complete=True
            )

        if message_lower in ["cancel", "no", "n", "start over"]:
            self.clear_session(context.session_id)

            return ChatResponse(
                session_id=context.session_id,
                message="Pipeline creation cancelled. Feel free to start over whenever you're ready!",
                state=ConversationState.INITIAL,
                config=None,
                is_complete=False
            )

        if message_lower in ["edit", "change", "modify"]:
            return ChatResponse(
                session_id=context.session_id,
                message="""What would you like to change?
- Source details
- PII/Masking settings
- Transformations
- Destination
- Schedule""",
                state=context.state,
                config=context.config,
                is_complete=False
            )

        return ChatResponse(
            session_id=context.session_id,
            message="Please type 'deploy' to create the pipeline, 'edit' to make changes, or 'cancel' to start over.",
            state=context.state,
            config=context.config,
            options=["Deploy", "Edit", "Cancel"],
            is_complete=True
        )

    async def _handle_general_message(
        self,
        context: ConversationContext,
        message: str
    ) -> ChatResponse:
        """Handle general messages that don't fit current state."""

        return ChatResponse(
            session_id=context.session_id,
            message="I'm not sure what you mean. Could you please clarify?",
            state=context.state,
            config=context.config,
            is_complete=False
        )

    # =========================================================================
    # LLM HELPER METHODS
    # =========================================================================

    async def _analyze_use_case(self, message: str) -> UseCaseAnalysis:
        """Analyze user's use case using LLM."""

        if not self.client:
            # Fallback without LLM
            return self._analyze_use_case_simple(message)

        system_prompt = """You are a data pipeline architect. Analyze the user's request and identify:
1. What type of data pipeline they need
2. What activities are required

Return JSON with this structure:
{
    "use_case_type": "blob_to_lakehouse_ingestion",
    "description": "Load data from Azure Blob Storage to Lakehouse",
    "activities": [
        {"type": "GetMetadata", "reason": "List files in source", "order": 1},
        {"type": "ForEach", "reason": "Process each file", "order": 2},
        {"type": "Copy", "reason": "Copy data to lakehouse", "order": 3}
    ],
    "needs_pii_detection": false,
    "needs_transformation": false,
    "needs_scheduling": true
}

Available activities: GetMetadata, ForEach, Copy, Notebook, IfCondition, SetVariable, Wait, Fail"""

        try:
            # Use Azure deployment name if using Azure OpenAI
            model = self.azure_deployment if self.use_azure else "gpt-4"

            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            return UseCaseAnalysis(
                use_case_type=result.get("use_case_type", "data_ingestion"),
                description=result.get("description", message),
                activities=[
                    IdentifiedActivity(**a) for a in result.get("activities", [])
                ],
                needs_pii_detection=result.get("needs_pii_detection", False),
                needs_transformation=result.get("needs_transformation", False),
                needs_scheduling=result.get("needs_scheduling", True)
            )
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return self._analyze_use_case_simple(message)

    def _analyze_use_case_simple(self, message: str) -> UseCaseAnalysis:
        """Simple rule-based use case analysis (fallback)."""

        message_lower = message.lower()

        # Detect source type and build appropriate activities
        activities = []
        use_case_type = "data_ingestion"
        description = message

        if "sql" in message_lower or "database" in message_lower:
            # Azure SQL or database source
            activities = [
                IdentifiedActivity(type="Copy", reason="Copy data from SQL database to OneLake", order=1),
            ]
            use_case_type = "database_to_lakehouse"
            if "azure sql" in message_lower:
                description = "Transfer data from Azure SQL Database to OneLake"
            else:
                description = "Transfer data from SQL database to OneLake"

        elif "blob" in message_lower or "storage" in message_lower:
            # Blob storage source
            activities = [
                IdentifiedActivity(type="GetMetadata", reason="List files in blob storage", order=1),
                IdentifiedActivity(type="ForEach", reason="Process each file", order=2),
                IdentifiedActivity(type="Copy", reason="Copy data to lakehouse", order=3),
            ]
            use_case_type = "blob_to_lakehouse"
            description = "Transfer files from Azure Blob Storage to OneLake"

        elif "sharepoint" in message_lower:
            activities = [
                IdentifiedActivity(type="Copy", reason="Copy data from SharePoint to OneLake", order=1),
            ]
            use_case_type = "sharepoint_to_lakehouse"
            description = "Transfer data from SharePoint to OneLake"

        else:
            activities = [
                IdentifiedActivity(type="Copy", reason="Copy data to destination", order=1),
            ]

        return UseCaseAnalysis(
            use_case_type=use_case_type,
            description=description,
            activities=activities,
            needs_pii_detection="pii" in message_lower or "phi" in message_lower or "sensitive" in message_lower,
            needs_transformation="transform" in message_lower or "filter" in message_lower,
            needs_scheduling="daily" in message_lower or "schedule" in message_lower or "hourly" in message_lower
        )

    async def _extract_source_info(
        self,
        message: str,
        context: ConversationContext
    ) -> Dict[str, str]:
        """Extract source information from user message."""

        if not self.client:
            return self._extract_source_info_simple(message)

        system_prompt = """Extract source configuration from the user's message.
Return JSON with any of these fields that you can identify:

For SQL Database sources:
{
    "server_name": "server.database.windows.net",
    "database_name": "database name",
    "table_name": "table name"
}

For Blob Storage sources:
{
    "storage_account": "account name",
    "container": "container name",
    "folder_path": "path/to/folder",
    "file_format": "csv|parquet|json"
}

Only include fields that are clearly specified. Return empty object if nothing found."""

        try:
            # Use Azure deployment name if using Azure OpenAI
            model = self.azure_deployment if self.use_azure else "gpt-4"

            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return self._extract_source_info_simple(message)

    def _extract_source_info_simple(self, message: str) -> Dict[str, str]:
        """Simple extraction of source info (fallback)."""

        result = {}
        message_lower = message.lower()
        words = message.split()

        # Check for SQL server patterns
        for word in words:
            clean_word = word.strip(".,!?;:")
            # SQL Server pattern
            if ".database.windows.net" in clean_word.lower():
                result["server_name"] = clean_word
            # Database name - look for common patterns
            elif clean_word.lower().endswith("db") or "database" in message_lower:
                if clean_word.lower() not in ["database", "sql", "azure"]:
                    result["database_name"] = clean_word

        # Look for table names - commonly mentioned after "table" keyword
        if "table" in message_lower:
            idx = message_lower.find("table")
            # Get words after "table"
            remaining = message[idx:].split()
            for w in remaining[1:3]:  # Check next 2 words
                clean = w.strip(".,!?;:")
                if clean and clean.lower() not in ["name", "is", "the", "called", "named", "to"]:
                    result["table_name"] = clean
                    break

        # Look for file format
        for fmt in ["csv", "parquet", "json", "delta", "avro"]:
            if fmt in message_lower:
                result["file_format"] = fmt
                break

        # Look for paths (containing /)
        for word in words:
            if "/" in word and not word.startswith("http"):
                result["folder_path"] = word.strip("/")

        return result

    async def _extract_transformations(self, message: str) -> List[TransformationStep]:
        """Extract transformation steps from user message."""

        transformations = []
        message_lower = message.lower()

        # Filter detection
        if "filter" in message_lower or "where" in message_lower or "only" in message_lower:
            # Extract condition
            condition = message  # Simplified - in production, use LLM
            transformations.append(TransformationStep(
                type=TransformationType.FILTER,
                condition=condition
            ))

        # Select detection
        if "select" in message_lower or "columns" in message_lower:
            transformations.append(TransformationStep(
                type=TransformationType.SELECT,
                columns=[]  # Would be extracted by LLM
            ))

        return transformations

    async def _extract_table_name(self, message: str) -> Optional[str]:
        """Extract table name from message."""

        # Simple extraction - look for quoted strings or specific patterns
        import re

        # Look for quoted strings
        quoted = re.findall(r'["\']([^"\']+)["\']', message)
        if quoted:
            return quoted[0].replace(" ", "_")

        # Look for "table_name" or "tablename" patterns
        words = message.split()
        for word in words:
            if "_" in word or (word.isalnum() and len(word) > 2):
                clean = word.strip(".,!?")
                if clean.lower() not in ["files", "tables", "table", "name", "the", "to"]:
                    return clean

        return None

    async def _extract_schedule(self, message: str) -> Dict[str, str]:
        """Extract schedule from message."""

        import re

        result = {
            "frequency": "daily",
            "time": "02:00",
            "timezone": "UTC"
        }

        message_lower = message.lower()

        # Extract time
        time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', message_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = time_match.group(2) or "00"
            ampm = time_match.group(3)

            if ampm == "pm" and hour < 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0

            result["time"] = f"{hour:02d}:{minute}"

        # Extract timezone
        timezones = ["utc", "est", "pst", "cst", "mst", "ist", "gmt"]
        for tz in timezones:
            if tz in message_lower:
                result["timezone"] = tz.upper()
                break

        # Extract frequency
        if "hourly" in message_lower:
            result["frequency"] = "hourly"
        elif "weekly" in message_lower:
            result["frequency"] = "weekly"
        elif "monthly" in message_lower:
            result["frequency"] = "monthly"

        return result

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _generate_pipeline_name(self, description: str) -> str:
        """Generate a pipeline name from description."""

        # Simple name generation
        words = description.split()[:4]
        name = "".join(w.capitalize() for w in words if w.isalnum())
        return f"{name}Pipeline" if name else "DataPipeline"

    def _build_pipeline_summary(self, config: PipelineConfig) -> str:
        """Build a human-readable pipeline summary."""

        source_info = f"{config.source.storage_account}/{config.source.container}/{config.source.folder_path}"

        pii_info = "None"
        if config.pii.enabled:
            pii_info = f"{config.pii.masking_type.value} masking (auto-detect columns)"

        transform_info = "None"
        if config.transformations.enabled:
            transform_info = ", ".join([s.type.value for s in config.transformations.steps])

        dest_info = config.destination.target.value
        if config.destination.table_name:
            dest_info += f" → {config.destination.table_name}"

        schedule_info = f"{config.schedule.frequency.capitalize()} at {config.schedule.time} {config.schedule.timezone}"

        return f"""**Pipeline:** {config.pipeline_name}

📦 **Source:** {source_info} (*.{config.source.file_format.value if config.source.file_format else 'csv'})
🔒 **PII Masking:** {pii_info}
🔄 **Transformations:** {transform_info}
📍 **Destination:** {dest_info} (Default Lakehouse)
⏰ **Schedule:** {schedule_info}"""

    async def _ask_transformations(self, context: ConversationContext) -> ChatResponse:
        """Helper to ask about transformations."""

        return ChatResponse(
            session_id=context.session_id,
            message="""**🔄 TRANSFORMATIONS**
Do you need any transformations on this data?

Please describe or say "none":
- Filter rows (e.g., "only active records")
- Select specific columns
- Other transformations""",
            state=context.state,
            config=context.config,
            options=["None", "Filter", "Select columns", "Other"],
            is_complete=False
        )
