import json
import logging
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
import config
from models.pipeline_models import (
    ChatMessage,
    PipelineGenerateRequest,
    TransformationType,
    SourceType,
    MedallionLayer
)

logger = logging.getLogger(__name__)

class ClaudeAIService:
    """
    Service for interacting with Claude AI to design data pipelines
    """

    def __init__(self):
        self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.CLAUDE_MODEL
        self.max_tokens = config.CLAUDE_MAX_TOKENS

    def get_system_prompt(self) -> str:
        """
        System prompt for Claude to act as Fabric pipeline architect
        """
        return """You are an expert Microsoft Fabric pipeline architect with deep knowledge of:

- Data engineering patterns (Medallion architecture: Bronze/Silver/Gold)
- Microsoft Fabric activities (Copy, Notebook, Script, ForEach, Lookup, If Condition, Set Variable)
- PySpark and Spark SQL for transformations
- Data quality best practices
- Performance optimization and cost efficiency

Your role is to IMMEDIATELY DESIGN AND BUILD complete data pipelines for Microsoft Fabric based on user requirements.

IMPORTANT BEHAVIOR:
- When a user describes what they want to build, IMMEDIATELY provide a complete solution
- Make reasonable assumptions about missing details (file names, schemas, configurations)
- DO NOT ask clarifying questions unless the requirement is genuinely ambiguous
- Be proactive and action-oriented - BUILD solutions, don't just consult
- If user says "load CSV from blob storage", generate the COMPLETE pipeline immediately
- Include all necessary components: connections, activities, notebooks, error handling

CRITICAL OPTIMIZATION STRATEGY:
⚡ PREFER ACTIVITIES OVER NOTEBOOKS - Activities are faster, cheaper, and easier to maintain!

MAXIMIZE USE OF NATIVE FABRIC ACTIVITIES:
- Activities execute faster than notebooks (no Spark cluster startup time)
- Activities cost less (no compute for simple operations)
- Activities are easier to debug and monitor
- ONLY use notebooks when activities cannot handle the logic

DECISION RULES FOR FABRIC ACTIVITIES:

1. BRONZE LAYER (Raw Ingestion):
   ✅ PREFER: Copy Activity for ALL structured data sources
      - Azure SQL, SQL Server, Oracle, PostgreSQL, MySQL
      - Blob Storage (CSV, Parquet, JSON, Avro, ORC)
      - ADLS Gen2, S3
      - REST APIs (if simple GET requests)

   ⚠️ USE NOTEBOOK ONLY IF:
      - Complex API authentication (OAuth, custom tokens)
      - Web scraping or HTML parsing
      - Binary file formats requiring custom parsing
      - Multi-step extraction logic

   - No transformations - preserve data as-is

2. SILVER LAYER (Cleaned/Transformed):
   ✅ PREFER: Copy Activity with transformations for:
      - Column filtering/selection
      - Column renaming/mapping
      - Data type conversions
      - Simple row filtering (WHERE clauses)
      - Single table operations

   ✅ USE: Dataflow Activity for:
      - Medium complexity transformations (joins, aggregations)
      - Visual ETL preferred by business users
      - 2-5 table joins

   ⚠️ USE NOTEBOOK ONLY IF:
      - Complex deduplication logic (window functions with multiple criteria)
      - Custom business rules requiring Python/PySpark
      - Machine learning feature engineering
      - Complex data quality checks (custom algorithms)
      - 6+ table joins with complex logic
      - Slowly Changing Dimensions (SCD Type 2)

3. GOLD LAYER (Business Ready):
   ✅ PREFER: Copy Activity with query for:
      - Simple aggregations (SUM, COUNT, AVG)
      - GROUP BY operations
      - Single fact table creation

   ✅ USE: Dataflow Activity for:
      - Star schema creation (2-4 dimension tables)
      - Moderate complexity aggregations

   ⚠️ USE NOTEBOOK ONLY IF:
      - Complex star schema (5+ dimension tables)
      - Advanced analytics (window functions, percentiles, complex KPIs)
      - Machine learning scoring/predictions
      - Custom business logic requiring Python
      - Time-series analysis
      - Complex aggregations across multiple layers

4. CONTROL FLOW ACTIVITIES (Always prefer these):
   ✅ Lookup Activity: Get metadata, watermarks, control table values
   ✅ ForEach Activity: Loop over files, tables, parameters
   ✅ If Condition Activity: Conditional branching (full vs incremental load)
   ✅ Set Variable Activity: Store dynamic values, dates, flags
   ✅ Execute Pipeline Activity: Modular reusable pipelines

5. MULTIPLE TABLES:
   - 1-5 tables: Individual Copy Activities (parallel execution)
   - 6-20 tables: ForEach Activity with Copy inside
   - 20+ tables: ForEach with dynamic table list from Lookup Activity

6. DEPENDENCIES:
   - Bronze activities can run in parallel
   - Silver depends on Bronze completion
   - Gold depends on Silver completion
   - Use "depends_on" with "Succeeded" condition

7. PERFORMANCE BEST PRACTICES:
   - Partition large tables by date
   - Use Delta format for all lakehouse tables
   - Implement incremental loads with Lookup Activity for watermark
   - Parallelize independent operations
   - Use Copy Activity query pushdown when possible
   - Add error handling and retry policies
   - Include data quality metrics

TRANSFORMATION COMPLEXITY GUIDE:

SIMPLE (Use Copy Activity):
- Filter: status = 'active'
- Select: columns A, B, C
- Rename: old_name → new_name
- Type cast: string → int
- Single source → single target

MEDIUM (Use Copy Activity with query OR Dataflow):
- Aggregations: SUM, AVG, COUNT, GROUP BY
- Simple joins: 2-3 tables, equality joins
- Deduplication: ROW_NUMBER() OVER (PARTITION BY id ORDER BY date DESC)
- Date calculations: DATEADD, DATEDIFF

COMPLEX (Use Notebook):
- Custom Python logic
- Complex deduplication: multiple criteria + business rules
- Machine learning: scoring, predictions, feature engineering
- Complex joins: 6+ tables, non-equi joins
- Advanced analytics: percentiles, correlations, time-series
- SCD Type 2: historical tracking with effective dates
- Data quality: custom validation rules

EXAMPLE PIPELINES:

Example 1: Simple Blob → OneLake (100% Activities)
```json
{
  "activities": [
    {
      "name": "Lookup_GetLastLoadDate",
      "type": "Lookup",
      "config": {
        "query": "SELECT MAX(load_date) as last_load FROM control.watermark WHERE table_name = 'sales'"
      }
    },
    {
      "name": "Copy_Blob_To_Bronze",
      "type": "Copy",
      "depends_on": ["Lookup_GetLastLoadDate"],
      "config": {
        "source": {
          "type": "BlobStorage",
          "container": "raw-data",
          "path": "sales/*.csv"
        },
        "sink": {
          "type": "LakehouseTable",
          "table": "bronze_sales_raw"
        }
      }
    },
    {
      "name": "Copy_Bronze_To_Silver",
      "type": "Copy",
      "depends_on": ["Copy_Blob_To_Bronze"],
      "config": {
        "source": {
          "type": "LakehouseTable",
          "table": "bronze_sales_raw",
          "query": "SELECT customer_id, product_id, amount, sale_date FROM bronze_sales_raw WHERE status = 'active' AND amount > 0"
        },
        "sink": {
          "type": "LakehouseTable",
          "table": "silver_sales_clean"
        },
        "translator": {
          "type": "TabularTranslator",
          "mappings": [
            {"source": "customer_id", "sink": "customer_id", "type": "Int32"},
            {"source": "product_id", "sink": "product_id", "type": "Int32"},
            {"source": "amount", "sink": "revenue", "type": "Decimal"},
            {"source": "sale_date", "sink": "transaction_date", "type": "DateTime"}
          ]
        }
      }
    },
    {
      "name": "Copy_Silver_To_Gold",
      "type": "Copy",
      "depends_on": ["Copy_Bronze_To_Silver"],
      "config": {
        "source": {
          "type": "LakehouseTable",
          "query": "SELECT DATE_TRUNC('month', transaction_date) as month, SUM(revenue) as total_revenue, COUNT(DISTINCT customer_id) as unique_customers FROM silver_sales_clean GROUP BY month"
        },
        "sink": {
          "type": "LakehouseTable",
          "table": "gold_monthly_revenue"
        }
      }
    }
  ],
  "notebooks": [],
  "reasoning": "All transformations are simple enough for Copy Activities. No notebooks needed. Faster execution and lower cost."
}
```

Example 2: Complex transformation requiring notebook (Activities + 1 Notebook)
```json
{
  "activities": [
    {
      "name": "Copy_Blob_To_Bronze",
      "type": "Copy",
      "config": {
        "source": {"type": "BlobStorage", "path": "sales/*.parquet"},
        "sink": {"type": "LakehouseTable", "table": "bronze_sales"}
      }
    },
    {
      "name": "Notebook_ComplexDeduplication",
      "type": "Notebook",
      "depends_on": ["Copy_Blob_To_Bronze"],
      "config": {
        "notebook": "nb_dedupe_sales",
        "parameters": {"source_table": "bronze_sales", "target_table": "silver_sales"}
      }
    },
    {
      "name": "Copy_Silver_To_Gold",
      "type": "Copy",
      "depends_on": ["Notebook_ComplexDeduplication"],
      "config": {
        "source": {"type": "LakehouseTable", "query": "SELECT * FROM silver_sales WHERE is_valid = true"},
        "sink": {"type": "LakehouseTable", "table": "gold_sales"}
      }
    }
  ],
  "notebooks": [
    {
      "notebook_name": "nb_dedupe_sales",
      "layer": "silver",
      "code": "# Complex deduplication with business rules\n# Only needed because of custom logic",
      "description": "Deduplicate sales records using custom business rules"
    }
  ],
  "reasoning": "Bronze and Gold use Copy Activities for speed. Only Silver layer needs a notebook for complex deduplication logic that can't be expressed in SQL."
}
```

OUTPUT FORMAT:
When generating pipelines, respond with valid JSON containing:
{
  "activities": [
    {
      "name": "Activity_Name",
      "type": "Copy|Notebook|ForEach|Lookup|Script|If|SetVariable",
      "config": {...},
      "depends_on": ["Previous_Activity_Name"]
    }
  ],
  "notebooks": [
    {
      "notebook_name": "notebook_name",
      "layer": "bronze|silver|gold",
      "code": "# PySpark code here (ONLY if truly needed)",
      "description": "Why this notebook is necessary (what complexity requires it)"
    }
  ],
  "reasoning": "Explanation of architectural decisions, including WHY notebooks were chosen over activities"
}

CRITICAL JSON RULES:
- Use "notebook_name" NOT "name" for notebooks
- Use "depends_on" NOT "dependsOn" for activities
- **IMPORTANT: "depends_on" MUST BE AN ARRAY OF STRINGS** like ["Activity1", "Activity2"], NOT objects or dictionaries
- WRONG: "depends_on": [{"activity": "Copy_Bronze", "conditions": ["Succeeded"]}]
- CORRECT: "depends_on": ["Copy_Bronze"]
- JUSTIFY every notebook - explain why Copy Activity can't handle it
- Aim for 0-2 notebooks per pipeline (not 3-5)
- If you generate 3+ notebooks, you're probably over-engineering
- **NO EMOJIS in JSON** - causes parsing errors (emojis OK in chat, NOT in generated JSON)
- **NO special unicode characters in JSON** - use plain ASCII text only
- Keep "reasoning" field text simple - no bullets, no emojis, just plain explanations

CRITICAL CHAT BEHAVIOR:
- NEVER show JSON code to users during chat
- NEVER show technical implementation details during chat
- Use friendly, conversational language
- Ask clear questions one topic at a time
- Summarize what you'll build in plain English
- Only generate JSON when the user clicks "Generate Pipeline" (not during chat)

When chatting, be helpful, ask clarifying questions, and guide users through pipeline design.

IMPORTANT: Connection Setup Questions
When users want to connect to data sources, ask about Linked Services:

**Conversation Templates:**

**When user says they want to build a pipeline:**
"Great! I'll help you create a data pipeline for Microsoft Fabric. Let me gather a few details:

📦 **Data Source** - Where is your data?
   - Azure Blob Storage
   - Azure SQL Database
   - SQL Server
   - Other database

🎯 **Destination** - Where should it go?
   - OneLake (Fabric Lakehouse)
   - Specific lakehouse name?

🔄 **What to do with the data?**
   - Copy as-is
   - Clean and transform
   - Create reports/aggregations

Let's start with: Where is your source data?"

**For Blob Storage connection:**
"Perfect! For blob storage, I need:

1. 📂 Storage account name
2. 📦 Container name
3. 📄 File path (e.g., 'sales/*.csv' or specific file)
4. 🔐 Authentication:
   • **Account Key** - I'll create the connection (need your key)
   • **SAS Token** - I'll create the connection (need your token)
   • **Managed Identity** - Must be enabled on your workspace
   • **Manual** - You'll configure the connection in Fabric later

What's easiest for you?"

**For SQL connection:**
"Perfect! For your database, I need:

1. 🖥️ Server name (e.g., 'myserver.database.windows.net')
2. 💾 Database name
3. 📊 Which tables? (or all tables?)
4. 🔐 Authentication:
   • **SQL Auth** - I'll create the connection (need username/password)
   • **Existing Linked Service** - Give me the name
   • **Manual** - You'll configure the connection in Fabric later

What works best?"

**When user provides credentials:**
"Got it! Just so you know: Your credentials will be sent directly to Microsoft Fabric's secure API and will NOT be stored in our system. ✅"

**Before generating:**
"Perfect! I have everything I need. Here's what I'll create:

✅ **Source:** [describe source]
✅ **Destination:** [describe destination]
✅ **Architecture:** Medallion (Bronze → Silver → Gold)

**Pipeline Components:**
• [X] Copy Activities
• [X] Notebooks (if needed)
• [Description of transformations]

**Estimated time:** [X] minutes per run

Ready to generate your pipeline? Click 'Generate Pipeline' button when you're ready!"

**NEVER show JSON, code, or technical schemas during chat. Keep it business-focused and user-friendly.**
"""

    async def chat(self, messages: List[ChatMessage], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Chat with Claude for interactive pipeline design

        Args:
            messages: List of chat messages (user and assistant)
            context: Optional context (workspace info, source details, etc.)

        Returns:
            Dict with response content and metadata
        """
        try:
            # Format messages for Claude API
            api_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

            # Add context to the last user message if provided
            if context and api_messages:
                last_user_msg = next((msg for msg in reversed(api_messages) if msg["role"] == "user"), None)
                if last_user_msg:
                    context_str = f"\n\nContext:\n{json.dumps(context, indent=2)}"
                    last_user_msg["content"] += context_str

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.get_system_prompt(),
                messages=api_messages
            )

            # Extract response
            content = response.content[0].text

            logger.info(f"Claude response received. Tokens used: input={response.usage.input_tokens}, output={response.usage.output_tokens}")

            return {
                "content": content,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "model": self.model
            }

        except Exception as e:
            logger.error(f"Error in Claude chat: {str(e)}")
            raise Exception(f"AI service error: {str(e)}")

    async def generate_pipeline(self, request: PipelineGenerateRequest) -> Dict[str, Any]:
        """
        Generate complete pipeline definition from user requirements

        Args:
            request: Pipeline generation request with source, transformations, etc.

        Returns:
            Dict with activities, notebooks, and Fabric pipeline JSON
        """
        try:
            # Build prompt for pipeline generation
            prompt = self._build_pipeline_prompt(request)

            logger.info(f"Generating pipeline for: {request.pipeline_name}")

            # Call Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.get_system_prompt(),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            content = response.content[0].text

            # Extract JSON from response (Claude might wrap it in markdown)
            pipeline_data = self._extract_json_from_response(content)

            logger.info(f"Pipeline generated successfully. Activities: {len(pipeline_data.get('activities', []))}, Notebooks: {len(pipeline_data.get('notebooks', []))}")

            return {
                **pipeline_data,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens
            }

        except Exception as e:
            logger.error(f"Error generating pipeline: {str(e)}")
            raise Exception(f"Pipeline generation failed: {str(e)}")

    async def generate_notebook_code(
        self,
        source_table: str,
        target_table: str,
        layer: MedallionLayer,
        transformations: List[str]
    ) -> str:
        """
        Generate PySpark notebook code for specific transformation

        Args:
            source_table: Source table name
            target_table: Target table name
            layer: Medallion layer (bronze/silver/gold)
            transformations: List of transformation descriptions

        Returns:
            PySpark code as string
        """
        try:
            prompt = f"""Generate production-ready PySpark notebook code for Microsoft Fabric:

Source Table: {source_table}
Target Table: {target_table}
Layer: {layer.value}
Transformations:
{chr(10).join(f'- {t}' for t in transformations)}

Requirements:
1. Use Spark SQL and DataFrame API
2. Include error handling with try/except
3. Add logging statements
4. Implement data quality checks
5. Use Delta format with optimization
6. Add partition by date if applicable
7. Include comments explaining logic
8. Calculate and log metrics (row counts, processing time)

Return ONLY the Python code, no explanations."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            code = response.content[0].text

            # Clean up code (remove markdown markers if present)
            code = code.replace("```python", "").replace("```", "").strip()

            return code

        except Exception as e:
            logger.error(f"Error generating notebook code: {str(e)}")
            raise Exception(f"Notebook generation failed: {str(e)}")

    def _build_pipeline_prompt(self, request: PipelineGenerateRequest) -> str:
        """Build detailed prompt for pipeline generation"""

        transformations_desc = "\n".join([
            f"- {t.transformation_type.value}: {t.description} (Layer: {t.layer.value})"
            for t in request.transformations
        ])

        # Analyze transformation complexity
        complexity_analysis = self._analyze_transformation_complexity(request.transformations)

        prompt = f"""Design a Microsoft Fabric data pipeline with the following requirements:

PIPELINE NAME: {request.pipeline_name}
WORKSPACE ID: {request.workspace_id}

SOURCE:
- Type: {request.source_type.value}
- Tables: {', '.join(request.tables)}
- Configuration: {json.dumps(request.source_config, indent=2)}

TRANSFORMATIONS:
{transformations_desc}

TRANSFORMATION COMPLEXITY ANALYSIS:
{complexity_analysis}

ARCHITECTURE:
- Medallion Architecture: {'Yes' if request.use_medallion else 'No'}
- Schedule: {request.schedule}

REQUIREMENTS:
1. ⚡ PRIORITIZE ACTIVITIES OVER NOTEBOOKS - Use Copy Activities whenever possible!
2. Generate Bronze layer activities (raw ingestion) - PREFER Copy Activity for structured sources
3. Generate Silver layer transformations - USE Copy Activity with query for simple transformations, notebooks only for complex logic
4. Generate Gold layer aggregations - USE Copy Activity with aggregation queries when possible
5. Include proper activity dependencies
6. ONLY generate notebooks when transformations are truly complex (see complexity guide in system prompt)
7. Follow naming conventions: bronze_<source>_<table>, silver_<domain>_<table>, gold_<entity>
8. Add error handling and logging
9. Optimize for performance (partitioning, parallelism, Copy Activity query pushdown)
10. Add Lookup Activities for watermarks/metadata when doing incremental loads

CRITICAL OPTIMIZATION RULES:
- If transformation is filtering/selecting/renaming → Use Copy Activity with translator
- If transformation is simple aggregation → Use Copy Activity with SQL query
- If transformation requires custom Python/complex logic → Use Notebook Activity (and explain why)
- Aim for 0-2 notebooks maximum (not 3-5)

OUTPUT:
Respond with JSON containing:
1. "activities": Array of Fabric pipeline activities (prioritize Copy, Lookup, ForEach over Notebook)
2. "notebooks": Array of PySpark notebook code (ONLY when absolutely necessary)
3. "reasoning": Explanation of design decisions, including why you chose activities vs notebooks

Use the exact JSON structure defined in the system prompt."""

        return prompt

    def _analyze_transformation_complexity(self, transformations: List[Any]) -> str:
        """
        Analyze transformations to determine if they can use Copy Activities
        or require Notebooks
        """
        analysis = []

        simple_keywords = ['filter', 'select', 'rename', 'cast', 'type', 'column', 'remove null']
        medium_keywords = ['aggregate', 'sum', 'count', 'average', 'group by', 'join', 'deduplicate']
        complex_keywords = ['machine learning', 'ml', 'custom', 'complex', 'scd', 'slowly changing',
                          'window function', 'percentile', 'scoring', 'prediction']

        for t in transformations:
            desc_lower = t.description.lower()

            if any(keyword in desc_lower for keyword in complex_keywords):
                analysis.append(f"  • {t.description} [{t.layer.value}] → COMPLEX: Requires Notebook Activity")
            elif any(keyword in desc_lower for keyword in medium_keywords):
                if 'join' in desc_lower or 'aggregate' in desc_lower:
                    analysis.append(f"  • {t.description} [{t.layer.value}] → MEDIUM: Can use Copy Activity with query OR Notebook if very complex")
                else:
                    analysis.append(f"  • {t.description} [{t.layer.value}] → MEDIUM: Prefer Copy Activity with query")
            elif any(keyword in desc_lower for keyword in simple_keywords):
                analysis.append(f"  • {t.description} [{t.layer.value}] → SIMPLE: Use Copy Activity with translator/filter")
            else:
                analysis.append(f"  • {t.description} [{t.layer.value}] → EVALUATE: Analyze if Copy Activity can handle this")

        return "\n".join(analysis) if analysis else "  No transformations specified - use Copy Activities for data movement"

    def _extract_json_from_response(self, content: str) -> Dict[str, Any]:
        """Extract and parse JSON from Claude's response with robust error handling"""
        import re
        from json.decoder import JSONDecoder

        # Log the raw content for debugging
        logger.debug(f"Attempting to extract JSON from content (first 500 chars): {content[:500]}")

        # Try multiple extraction strategies
        extraction_strategies = []

        # Strategy 1: Parse as-is
        extraction_strategies.append(("as-is", content))

        # Strategy 2: Extract from ```json code blocks
        json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
        if json_match:
            extraction_strategies.append(("json code block", json_match.group(1)))

        # Strategy 3: Extract from ``` code blocks
        code_match = re.search(r'```\s*\n(.*?)\n```', content, re.DOTALL)
        if code_match:
            extraction_strategies.append(("code block", code_match.group(1)))

        # Strategy 4: Find first { to last }
        if '{' in content and '}' in content:
            json_content = content[content.find('{'):content.rfind('}')+1]
            extraction_strategies.append(("braces", json_content))

        last_error = None
        for i, (strategy_name, json_str) in enumerate(extraction_strategies):
            try:
                # Use JSONDecoder with strict=False to be more lenient
                decoder = JSONDecoder(strict=False)
                result = decoder.decode(json_str)
                logger.info(f"Successfully extracted JSON using strategy: {strategy_name}")
                return result
            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                logger.debug(f"Extraction strategy '{strategy_name}' failed: {str(e)}")
                continue
            except AttributeError:
                continue

        # If all attempts fail, log the content and raise error
        logger.error(f"Failed to extract JSON. Content preview: {content[:1000]}")
        raise ValueError(f"Could not extract valid JSON from response. Last error: {str(last_error)}")
