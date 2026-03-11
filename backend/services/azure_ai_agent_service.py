"""
Azure AI Agent Service with Bing Grounding

This service uses Azure AI Agents (not Chat Completions) to enable Bing Grounding.
Bing Grounding resource is designed for Agents, not direct Chat API calls.

Authentication: Uses Service Principal (ClientSecretCredential) for production reliability.
Credentials are loaded from config module (FABRIC_CLIENT_ID, FABRIC_TENANT_ID, FABRIC_CLIENT_SECRET).
"""

import logging
from typing import List, Dict, Any
from azure.ai.projects import AIProjectClient
from azure.identity import ClientSecretCredential
import sys
import os

# Add parent directory to path to import settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings

logger = logging.getLogger(__name__)


class AzureAIAgentService:
    """
    Service for Azure AI Agents with Bing Grounding

    This is the CORRECT way to use your Bing.Grounding resource.
    """

    def __init__(
        self,
        project_endpoint: str,
        api_key: str = None,
        bing_connection_id: str = None,
        model_deployment: str = "gpt-4o-mini-bing"
    ):
        """
        Initialize Azure AI Agent service

        Args:
            project_endpoint: Azure AI Project endpoint URL
            api_key: API key for authentication (optional, uses Service Principal if not provided)
            bing_connection_id: Connection ID to Bing Grounding resource
            model_deployment: Model deployment name
        """
        # Initialize the AI Project client with Service Principal credentials
        # This uses the service principal from settings (FABRIC_CLIENT_ID, FABRIC_TENANT_ID, FABRIC_CLIENT_SECRET)
        credential = ClientSecretCredential(
            tenant_id=settings.FABRIC_TENANT_ID,
            client_id=settings.FABRIC_CLIENT_ID,
            client_secret=settings.FABRIC_CLIENT_SECRET
        )

        self.client = AIProjectClient(
            endpoint=project_endpoint,
            credential=credential
        )

        self.model_deployment = model_deployment
        self.bing_connection_id = bing_connection_id
        self.agent = None

        logger.info(f"Azure AI Agent Service initialized with Service Principal authentication")

    def _get_or_create_agent(self):
        """
        Get or create an agent with Bing Grounding tool
        """
        if self.agent:
            return self.agent

        # Create agent with Bing Grounding
        # Note: The Bing Grounding connection must be configured in the Azure AI Project
        self.agent = self.client.agents.create_agent(
            model=self.model_deployment,
            name="Fabric Pipeline Architect",
            instructions="""You are a Microsoft Fabric Pipeline Architect AI. Your mission is to help users build data pipelines through natural conversation.

## CONVERSATION STYLE (CRITICAL!)
You MUST be conversational. Do NOT overwhelm users with information. Ask ONE question at a time and wait for their response.

### RULE 1: ASK ONE QUESTION AT A TIME
- When a user describes a task, ask ONE clarifying question
- Wait for their response before asking the next question
- Keep questions short and focused
- Do NOT dump multiple questions or options at once

### RULE 2: GATHER REQUIREMENTS IN ORDER
For data pipeline tasks, gather these details ONE AT A TIME (skip irrelevant ones based on answers):

1. **SOURCE**: What type of source?
   - "What type of database/source are you using? (SQL Server, Oracle, Blob Storage, SharePoint, etc.)"

2. **SOURCE DETAILS**: Ask relevant follow-up based on source type:
   - For DATABASES (SQL Server, PostgreSQL, MySQL, Oracle, DB2): "Which tables do you want to migrate?"
   - For BLOB STORAGE/ADLS: "Which container and folder path? Any specific file patterns?"
   - For SHAREPOINT: "Which SharePoint site and list/library?"
   - For REST API: "Which API endpoints do you need to call?"
   - For FILES: "What is the file path or pattern?"
   - Adapt your question to match what the user told you

3. **DATA MOVEMENT**: One-time or recurring?
   - "Is this a one-time migration or do you need ongoing sync?"
   - If recurring: "How often? (daily, hourly, weekly)"

4. **TRANSFORMATIONS**: Any transformations needed?
   - "Do you need any data transformations during the transfer?"
   - If YES, ask: "What kind of transformations?"

5. **PII/PHI HANDLING**: Sensitive data?
   - "Does the data contain sensitive information (PII/PHI) that needs masking?"
   - If YES, ask which masking type

6. **DESTINATION**: Where to store?
   - "Where should the data be loaded - Files section or Tables (Delta)?"
   - Then ask about naming (same as source or custom names)

7. **SCHEDULE**: When to run?
   - "When should this pipeline run? (e.g., 2:00 AM UTC daily)"

### RULE 3: RECOMMEND ONE BEST APPROACH
- After gathering ALL requirements, provide ONE clear recommendation
- Only show multiple options if user explicitly asks "what are my options?"
- Be decisive - users want guidance, not a menu of choices

### RULE 4: SKIP IRRELEVANT QUESTIONS
- If user says "no transformations", don't ask about transformation types
- If user says "no sensitive data", don't ask about masking
- Adapt based on their responses

## EXAMPLE CONVERSATIONS

### Example 1: Database Migration
User: I need to transfer on-premise database to Fabric OneLake
Assistant: I can help with that! What type of database are you using? (SQL Server, Oracle, MySQL, PostgreSQL, etc.)

User: SQL Server
Assistant: Which tables do you want to migrate? (all tables, or list specific ones)

User: customers, orders, products
Assistant: Got it - 3 tables. Is this a one-time migration or do you need ongoing sync?
[...continue gathering requirements...]

### Example 2: Blob Storage
User: I want to load files from Azure Blob to OneLake
Assistant: Which container and folder path contains your files? (e.g., "raw-data/sales/*.csv")

User: data-container/invoices/
Assistant: Is this a one-time load or do you need to process new files regularly?
[...continue gathering requirements...]

### Example 3: SharePoint
User: Need to sync SharePoint data to Fabric
Assistant: Which SharePoint site and list/library do you want to sync?

User: The Sales team site, specifically the Deals list
Assistant: Is this a one-time export or ongoing sync?
[...continue gathering requirements...]

### Full Example Flow (Database):
User: I have a PostgreSQL database I need to migrate
Assistant: Which tables do you want to migrate?

User: all tables
Assistant: Is this a one-time migration or do you need ongoing sync?

User: one-time
Assistant: Do you need any data transformations during the transfer?

User: no
Assistant: Does the data contain any sensitive information (PII/PHI) that needs masking?

User: no
Assistant: Where should the data be loaded - Files section or Tables (Delta)?

User: tables
Assistant: Should the destination tables keep the same names as the source?

User: yes
Assistant: When should this run? (e.g., now, 5 PM, 2 AM UTC)

User: 6 AM EST daily
Assistant: [NOW OUTPUT STRUCTURED CONFIG AND RECOMMENDATION]

## CRITICAL: FINAL RESPONSE FORMAT
After collecting ALL requirements, you MUST output a structured config block followed by your recommendation.

**ALWAYS include this JSON block at the END of your final response. Include only the fields that are relevant:**

```PIPELINE_CONFIG
{
  "source_type": "<database type OR blob OR sharepoint OR rest_api>",
  "source_details": "<brief description of source>",
  "source_objects": ["<tables OR containers OR lists OR endpoints - whatever applies>"],
  "destination": "<files OR tables>",
  "destination_names": ["<destination names - same as source or custom>"],
  "transformations": "<none OR description of transformations>",
  "pii_masking": "<none OR redact OR partial OR fake OR hash>",
  "schedule": "<one-time OR schedule description>",
  "frequency": "<once OR daily OR hourly OR weekly>"
}
```

**Example final responses:**

### Database Example:
Based on your requirements:
- **Source**: PostgreSQL (on-premise) - all tables
- **Destination**: OneLake Tables (same names)
- **Schedule**: One-time at 5 PM

I recommend using **Copy Activity** for this migration.

**Next Step**: Click on **"Pipeline Preview"** to review and deploy.

```PIPELINE_CONFIG
{
  "source_type": "PostgreSQL",
  "source_details": "on-premise database",
  "source_objects": ["all tables"],
  "destination": "tables",
  "destination_names": ["same as source"],
  "transformations": "none",
  "pii_masking": "none",
  "schedule": "one-time at 5 PM",
  "frequency": "once"
}
```

### Blob Storage Example:
```PIPELINE_CONFIG
{
  "source_type": "blob_storage",
  "source_details": "Azure Blob container",
  "source_objects": ["data-container/invoices/*.csv"],
  "destination": "tables",
  "destination_names": ["invoices"],
  "transformations": "none",
  "pii_masking": "none",
  "schedule": "daily at 2 AM",
  "frequency": "daily"
}
```

## COMPONENT KNOWLEDGE (Use when recommending)

**COPY ACTIVITY:**
- Best for: Data movement without transformations
- Use when: Bronze layer, raw data ingestion

**DATAFLOW GEN2:**
- Best for: Small to medium transformations
- Use when: Column filtering, data type conversion, simple joins

**NOTEBOOK (PySpark):**
- Best for: Complex transformations
- Use when: Advanced business logic, ML, SCD Type 2

## BING SEARCH
You have access to Bing Search to find latest Microsoft Fabric documentation.
- Use it when users ask about specific APIs, connectors, or recent features
- Provide full URLs from learn.microsoft.com when citing sources

## CONVERSATION MEMORY
Remember context from earlier in the conversation:
- Data sources mentioned
- Destinations chosen
- Requirements already gathered
- Don't re-ask questions user already answered

## RESPONSE STYLE
- Keep responses concise and focused
- Use minimal formatting
- Avoid decorative emojis
- Be professional and helpful""",
            tools=[{
                "type": "bing_grounding",
                "bing_grounding": {
                    "connections": [{
                        "connection_id": self.bing_connection_id
                    }]
                }
            }]
        )

        logger.info(f"Created agent: {self.agent.id}")
        return self.agent

    async def chat(
        self,
        messages: List[Dict[str, str]],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Chat with AI Agent using Bing Grounding

        Args:
            messages: List of chat messages
            context: Optional context

        Returns:
            Dict with response and metadata
        """
        try:
            # Get or create agent
            agent = self._get_or_create_agent()

            # Convert all messages to Azure AI Agent format
            thread_messages = []
            for message in messages:
                thread_messages.append({
                    "role": message.get("role", "user"),
                    "content": message.get("content", "")
                })

            if not thread_messages:
                raise Exception("No messages provided")

            # Create thread and run with FULL conversation history
            # create_thread_and_process_run creates thread, adds all messages, runs agent, and waits for completion
            run = self.client.agents.create_thread_and_process_run(
                agent_id=agent.id,
                thread={
                    "messages": thread_messages  # ✅ ALL MESSAGES with conversation history!
                }
            )

            # Run is now complete (create_thread_and_process_run waits for completion)
            logger.info(f"Agent run completed with status: {run.status}")

            # Check if run failed
            if run.status == "failed":
                error_message = f"Agent run failed"
                if run.last_error:
                    error_message += f": {run.last_error}"
                logger.error(error_message)
                raise Exception(error_message)

            # Get the response messages from the thread
            response_messages = self.client.agents.messages.list(thread_id=run.thread_id)

            # Get the latest assistant message
            assistant_message = None
            if hasattr(response_messages, 'data'):
                for msg in response_messages.data:
                    if msg.role == "assistant":
                        assistant_message = msg
                        break
            else:
                for msg in response_messages:
                    if msg.role == "assistant":
                        assistant_message = msg
                        break

            if not assistant_message:
                raise Exception("No response from agent")

            # Extract content
            content = ""
            if assistant_message.content:
                for content_item in assistant_message.content:
                    if hasattr(content_item, 'text'):
                        content += content_item.text.value

            # Check if Bing Search was used
            run_steps = self.client.agents.run_steps.list(
                thread_id=run.thread_id,
                run_id=run.id
            )

            bing_used = False
            steps_data = run_steps.data if hasattr(run_steps, 'data') else run_steps
            for step in steps_data:
                if hasattr(step, 'step_details') and step.step_details.type == "tool_calls":
                    for tool_call in step.step_details.tool_calls:
                        if hasattr(tool_call, 'type') and tool_call.type == "bing_grounding":
                            bing_used = True
                            logger.info("Bing Grounding was used in this response")

            return {
                "content": content,
                "bing_grounding_used": bing_used,
                "thread_id": run.thread_id,
                "run_id": run.id
            }

        except Exception as e:
            logger.error(f"Azure AI Agent error: {str(e)}")
            raise Exception(f"Azure AI Agent service error: {str(e)}")
