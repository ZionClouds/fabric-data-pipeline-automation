import json
import logging
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
import settings
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
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.CLAUDE_MAX_TOKENS

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

CRITICAL: ONELAKE SHORTCUTS HANDLING
When the user mentions they have OneLake shortcuts to Azure Blob Storage or ADLS Gen2:

⚠️ IMPORTANT: Copy Activities CANNOT read directly from lakehouse Files/ paths (shortcuts)
✅ CORRECT PATTERN: Use Notebook Activity to read from shortcuts and write to tables

Pattern for Bronze Layer (Reading from Shortcuts):
{
  "name": "Load_Bronze_From_Shortcut",
  "type": "Notebook",
  "config": {
    "notebook": "nb_bronze_loader",
    "parameters": {
      "source_path": "Files/bronze",
      "target_table": "bronze_table_name",
      "file_pattern": "*.csv"
    }
  }
}

Pattern for Silver Layer (Table to Table):
{
  "name": "Copy_Bronze_To_Silver",
  "type": "Copy",
  "depends_on": ["Load_Bronze_From_Shortcut"],
  "config": {
    "source": {
      "type": "LakehouseTable",
      "table": "bronze_table_name",
      "query": "SELECT * FROM bronze_table_name WHERE column IS NOT NULL"
    },
    "sink": {
      "type": "LakehouseTable",
      "table": "silver_table_name"
    }
  }
}

🚨 KEY RULES:
1. Files/bronze and Files/silver are shortcuts - they contain CSV/Parquet FILES, not tables
2. To process files from shortcuts, you MUST use Notebook activities
3. Once data is in lakehouse TABLES, use Copy Activities for transformations
4. DO NOT try to use Copy Activity with "LakehouseFiles" source - it will fail!

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

Example 1: Blob → OneLake via Shortcuts (Notebook for Files, Copy for Tables)
```json
{
  "activities": [
    {
      "name": "Load_Bronze_From_Shortcut",
      "type": "Notebook",
      "config": {
        "notebook": "nb_load_bronze",
        "parameters": {
          "source_path": "Files/bronze",
          "target_table": "bronze_sales_raw",
          "file_pattern": "*.csv"
        }
      }
    },
    {
      "name": "Copy_Bronze_To_Silver",
      "type": "Copy",
      "depends_on": ["Load_Bronze_From_Shortcut"],
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
  "notebooks": [
    {
      "notebook_name": "nb_load_bronze",
      "layer": "bronze",
      "code": "# Load CSV files from OneLake shortcut to bronze table\nfrom pyspark.sql import SparkSession\n\n# Get parameters from pipeline\nsource_path = spark.conf.get('source_path', 'Files/bronze')\ntarget_table = spark.conf.get('target_table', 'bronze_table')\nfile_pattern = spark.conf.get('file_pattern', '*.csv')\n\nprint(f'Loading data from {source_path}/{file_pattern}')\n\n# Read CSV files from OneLake shortcut\ndf = spark.read.format('csv') \\\n    .option('header', 'true') \\\n    .option('inferSchema', 'true') \\\n    .load(f'{source_path}/{file_pattern}')\n\nrow_count = df.count()\nprint(f'Loaded {row_count} rows')\n\n# Write to bronze lakehouse table\ndf.write.mode('overwrite').format('delta').saveAsTable(target_table)\n\nprint(f'Successfully wrote {row_count} rows to {target_table}')",
      "description": "Reads CSV files from OneLake shortcut (Files/bronze) and writes to bronze lakehouse table. Required because Copy Activities cannot read from lakehouse Files/ paths."
    }
  ],
  "reasoning": "Bronze layer requires Notebook activity to read CSV files from OneLake shortcut (Files/bronze) because Copy Activities cannot read from lakehouse Files paths. Silver layer uses Copy Activity for table-to-table transformation which is faster and cheaper than notebooks."
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

    async def generate_metadata_driven_pipeline(
        self,
        requirements: str,
        source_type: str,
        destination_type: str, 
        workspace_id: str,
        use_base_pattern: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a metadata-driven pipeline with base pattern:
        Get Metadata → Script → Set Variable → ForEach (with Filter)
        """
        
        base_activities = [
            {
                "name": "Get Metadata",
                "type": "GetMetadata",
                "dependsOn": [],
                "policy": {
                    "timeout": "7.00:00:00",
                    "retry": 2,
                    "retryIntervalInSeconds": 30,
                    "secureOutput": False,
                    "secureInput": False
                },
                "userProperties": [],
                "typeProperties": {
                    "dataset": {
                        "referenceName": "SourceDataset",
                        "type": "DatasetReference",
                        "parameters": {
                            "folderPath": "@pipeline().parameters.sourceFolderPath"
                        }
                    },
                    "fieldList": ["childItems", "exists", "itemName", "itemType", "lastModified"],
                    "storeSettings": {
                        "type": f"{source_type}ReadSettings",
                        "recursive": True,
                        "enablePartitionDiscovery": False
                    },
                    "formatSettings": {
                        "type": "BinaryReadSettings"
                    }
                }
            },
            {
                "name": "GetProcessedFileNames",
                "type": "Script",
                "dependsOn": [
                    {
                        "activity": "Get Metadata",
                        "dependencyConditions": ["Succeeded"]
                    }
                ],
                "policy": {
                    "timeout": "7.00:00:00",
                    "retry": 2,
                    "retryIntervalInSeconds": 30,
                    "secureOutput": False,
                    "secureInput": False
                },
                "userProperties": [],
                "typeProperties": {
                    "scriptType": "Query",
                    "script": {
                        "value": "SELECT FileName, ProcessedDate, Status FROM dbo.ProcessedFiles WHERE WorkspaceId = '@{pipeline().parameters.workspaceId}' AND Status = 'Completed'",
                        "type": "Expression"
                    },
                    "scriptBlockExecutionTimeout": "02:00:00",
                    "datasetSettings": {
                        "type": "SqlServerTable",
                        "linkedServiceName": {
                            "referenceName": "MetadataDatabase",
                            "type": "LinkedServiceReference"
                        }
                    }
                }
            },
            {
                "name": "SetEmptyFileArray",
                "type": "SetVariable",
                "dependsOn": [
                    {
                        "activity": "GetProcessedFileNames",
                        "dependencyConditions": ["Succeeded"]
                    }
                ],
                "policy": {
                    "timeout": "7.00:00:00",
                    "retry": 0,
                    "retryIntervalInSeconds": 30,
                    "secureOutput": False,
                    "secureInput": False
                },
                "userProperties": [],
                "typeProperties": {
                    "variableName": "FileArray",
                    "value": {
                        "value": "@activity('Get Metadata').output.childItems",
                        "type": "Expression"
                    }
                }
            },
            {
                "name": "ForEach1",
                "type": "ForEach",
                "dependsOn": [
                    {
                        "activity": "SetEmptyFileArray",
                        "dependencyConditions": ["Succeeded"]
                    }
                ],
                "userProperties": [],
                "typeProperties": {
                    "items": {
                        "value": "@variables('FileArray')",
                        "type": "Expression"
                    },
                    "isSequential": False,
                    "batchCount": 10,
                    "activities": [
                        {
                            "name": "FilterNewFiles",
                            "type": "Filter",
                            "dependsOn": [],
                            "userProperties": [],
                            "typeProperties": {
                                "items": {
                                    "value": "@createArray(item())",
                                    "type": "Expression"
                                },
                                "condition": {
                                    "value": "@not(contains(string(activity('GetProcessedFileNames').output.value), item().name))",
                                    "type": "Expression"
                                }
                            }
                        }
                    ]
                }
            }
        ]
        
        # Add user-specific activities based on requirements
        user_activities = self._generate_user_activities(requirements, source_type, destination_type)
        
        # Insert user activities into the ForEach
        if user_activities:
            base_activities[3]["typeProperties"]["activities"].extend(user_activities)
        
        # Generate notebooks if complex transformations are needed
        notebooks = []
        if "complex" in requirements.lower() or "transformation" in requirements.lower():
            notebooks.append(self._generate_transformation_notebook(requirements, source_type, destination_type))
        
        return {
            "success": True,
            "pipeline_name": f"metadata_driven_{source_type}_to_{destination_type}_{workspace_id[:8]}",
            "activities": base_activities,
            "variables": {
                "FileArray": {
                    "type": "Array",
                    "defaultValue": []
                },
                "ProcessedFiles": {
                    "type": "Array",
                    "defaultValue": []
                },
                "CurrentFileName": {
                    "type": "String",
                    "defaultValue": ""
                }
            },
            "parameters": {
                "sourceFolderPath": {
                    "type": "String",
                    "defaultValue": "/"
                },
                "workspaceId": {
                    "type": "String",
                    "defaultValue": workspace_id
                }
            },
            "notebooks": notebooks,
            "suggestions": [
                "✅ Metadata-driven pattern implemented for maximum scalability",
                "📊 Get Metadata activity will dynamically discover all files/tables",
                "🔍 Script activity queries your metadata database to avoid reprocessing",
                "⚡ Filter activity ensures only new/unprocessed items are handled",
                "🚀 ForEach runs up to 10 items in parallel for optimal performance",
                "💡 Add a Script activity at the end to log processed files"
            ],
            "estimated_cost": "$0.50-2.00 per 1000 files processed (activity-based pricing)",
            "performance_estimate": "Processes 100 files/minute with parallel execution"
        }

    def _generate_user_activities(self, requirements: str, source_type: str, destination_type: str) -> List[Dict[str, Any]]:
        """
        Generate user-specific activities based on requirements
        """
        activities = []
        
        # Add Copy Activity for basic data movement
        copy_activity = {
            "name": "CopyFilteredData",
            "type": "Copy",
            "dependsOn": [
                {
                    "activity": "FilterNewFiles",
                    "dependencyConditions": ["Succeeded"]
                }
            ],
            "policy": {
                "timeout": "7.00:00:00",
                "retry": 2,
                "retryIntervalInSeconds": 30,
                "secureOutput": False,
                "secureInput": False
            },
            "userProperties": [],
            "typeProperties": {
                "source": {
                    "type": f"{source_type}Source",
                    "storeSettings": {
                        "type": f"{source_type}ReadSettings",
                        "recursive": False,
                        "wildcardFileName": {
                            "value": "@item().name",
                            "type": "Expression"
                        }
                    }
                },
                "sink": {
                    "type": f"{destination_type}Sink",
                    "storeSettings": {
                        "type": f"{destination_type}WriteSettings"
                    },
                    "formatSettings": {
                        "type": "ParquetWriteSettings"
                    }
                },
                "enableStaging": False,
                "parallelCopies": 4,
                "dataIntegrationUnits": 4
            }
        }
        activities.append(copy_activity)
        
        # Add logging activity
        log_activity = {
            "name": "LogProcessedFile",
            "type": "Script",
            "dependsOn": [
                {
                    "activity": "CopyFilteredData",
                    "dependencyConditions": ["Succeeded"]
                }
            ],
            "policy": {
                "timeout": "7.00:00:00",
                "retry": 1,
                "retryIntervalInSeconds": 30
            },
            "userProperties": [],
            "typeProperties": {
                "scriptType": "NonQuery",
                "script": {
                    "value": "INSERT INTO dbo.ProcessedFiles (FileName, ProcessedDate, Status, WorkspaceId) VALUES ('@{item().name}', GETDATE(), 'Completed', '@{pipeline().parameters.workspaceId}')",
                    "type": "Expression"
                },
                "scriptBlockExecutionTimeout": "02:00:00"
            }
        }
        activities.append(log_activity)
        
        return activities

    def _generate_transformation_notebook(self, requirements: str, source_type: str, destination_type: str) -> Dict[str, Any]:
        """
        Generate a PySpark notebook for complex transformations
        """
        notebook_code = f'''# Metadata-Driven Transformation Notebook
# Generated for: {requirements}
# Source: {source_type}, Destination: {destination_type}

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from datetime import datetime

# Initialize Spark Session
spark = SparkSession.builder \\
    .appName("MetadataDrivenTransformation") \\
    .config("spark.sql.adaptive.enabled", "true") \\
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \\
    .getOrCreate()

# Parameters (passed from pipeline)
file_path = spark.conf.get("file_path", "")
output_path = spark.conf.get("output_path", "")
workspace_id = spark.conf.get("workspace_id", "")

print(f"Processing file: {{file_path}}")

# Read source data
df = spark.read.parquet(file_path) if file_path.endswith('.parquet') else spark.read.csv(file_path, header=True, inferSchema=True)

# Data Quality Checks
print(f"Initial row count: {{df.count()}}")
print(f"Column count: {{len(df.columns)}}")

# Remove duplicates
df_clean = df.dropDuplicates()

# Add metadata columns
df_with_metadata = df_clean \\
    .withColumn("processed_timestamp", current_timestamp()) \\
    .withColumn("workspace_id", lit(workspace_id)) \\
    .withColumn("source_file", lit(file_path))

# Custom transformations based on requirements
# Add your specific transformation logic here

# Data validation
assert df_with_metadata.count() > 0, "No data after transformation"

# Write to destination
df_with_metadata.write \\
    .mode("append") \\
    .option("mergeSchema", "true") \\
    .parquet(output_path)

print(f"Successfully processed {{df_with_metadata.count()}} records to {{output_path}}")

# Update metadata table
metadata_update = f"""
UPDATE dbo.ProcessedFiles 
SET RecordCount = {{df_with_metadata.count()}}, 
    LastModified = GETDATE() 
WHERE FileName = '{{file_path}}' 
    AND WorkspaceId = '{{workspace_id}}'
"""

print("Transformation complete!")
'''
        
        return {
            "name": "metadata_driven_transformation",
            "code": notebook_code,
            "language": "python",
            "description": "Complex transformation notebook for metadata-driven pipeline"
        }