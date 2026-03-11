# Multi-Agent Pipeline Architect System

## Overview

This document describes the multi-agent architecture for the Data Pipeline Architect system. The system uses specialized AI agents that work together to understand user requirements, design optimal pipeline architectures, and deploy them to Microsoft Fabric.

## Architecture Diagram

```
                         ┌──────────────────────────────┐
                         │     ORCHESTRATOR AGENT       │
                         │   "Chief Pipeline Architect" │
                         │                              │
                         │  - Coordinates all agents    │
                         │  - Maintains conversation    │
                         │  - Tracks requirements state │
                         │  - Makes final decisions     │
                         └──────────────┬───────────────┘
                                        │
         ┌──────────────┬───────────────┼───────────────┬──────────────┐
         ▼              ▼               ▼               ▼              ▼
   ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
   │ DISCOVERY │  │  SOURCE   │  │  FABRIC   │  │ TRANSFORM │  │  DEPLOY   │
   │   AGENT   │  │  ANALYST  │  │ ARCHITECT │  │  EXPERT   │  │   AGENT   │
   │           │  │           │  │           │  │           │  │           │
   │"Understand│  │"Analyze   │  │"Design    │  │"Plan data │  │"Build &   │
   │ the WHY"  │  │ sources"  │  │ solution" │  │ transforms│  │ deploy"   │
   └───────────┘  └───────────┘  └───────────┘  └───────────┘  └───────────┘
```

## Pipeline Requirements State

The system tracks all information needed to build a complete pipeline:

```python
PIPELINE_REQUIREMENTS = {
    "source": {
        "type": None,              # postgresql, sql_server, blob, sharepoint, etc.
        "location": None,          # cloud, on_premise
        "host": None,
        "database": None,
        "objects": [],             # tables, files, lists
        "volume_gb": None,
        "schema": {},
        "change_pattern": None,    # static, insert_only, updates, deletes
        "gateway_available": None,
    },
    "business_context": {
        "use_case": None,          # analytics, ml, operational, archive
        "consumers": [],           # power_bi, data_scientists, applications
        "sla_hours": None,
        "criticality": None,       # poc, development, production
        "deadline": None,
    },
    "transformations": {
        "needed": None,            # true/false
        "cleaning": [],            # dedupe, null_handling, format_fixes
        "enrichment": [],          # joins, lookups
        "aggregations": [],        # sums, counts, averages
        "pii_handling": None,      # none, detect, mask, encrypt
        "custom_logic": None,
    },
    "destination": {
        "type": None,              # lakehouse_tables, lakehouse_files, warehouse
        "lakehouse_id": None,
        "naming_convention": None,
        "partition_by": None,
        "file_format": None,       # delta, parquet, csv
    },
    "operations": {
        "frequency": None,         # manual, hourly, daily, weekly, realtime
        "schedule_time": None,
        "error_handling": None,    # retry, alert, skip
        "dependencies": [],
    },
    "infrastructure": {
        "workspace_id": None,
        "gateway_id": None,
        "connections_needed": [],
    }
}
```

## Agent Specifications

### 1. Discovery Agent

**Purpose**: Understand the business context and use case before diving into technical details.

**Thinking Rules**:
- If user says "migrate" → Ask if they need ongoing sync too
- If user mentions "customer/sales/employee data" → Flag potential PII
- If user says "Power BI/dashboard" → Will need aggregated Gold layer
- If user says "real-time" → Different architecture (Eventstream)
- If user says "ML/data science" → Need feature engineering layer

**Required Information**:
- What is the source system?
- What is the end goal/use case?
- Who will consume this data?
- Is this one-time or ongoing?
- Business criticality (POC vs Production)

**Smart Inferences**:
```python
DISCOVERY_INFERENCES = {
    "customer data": {"pii_likely": True, "suggest_masking": True},
    "sales data": {"pii_likely": True, "needs_aggregation": True},
    "employee data": {"pii_likely": True, "compliance": "hr_policies"},
    "power bi": {"needs_gold_layer": True, "optimize_queries": True},
    "machine learning": {"needs_feature_store": True, "format": "delta"},
    "real-time": {"architecture": "streaming", "component": "eventstream"},
    "daily report": {"frequency": "daily", "schedule": "early_morning"},
}
```

### 2. Source Analyst Agent

**Purpose**: Deep expertise on source systems, connection methods, and extraction strategies.

**Knowledge Base**:
```python
SOURCE_KNOWLEDGE = {
    "postgresql": {
        "cloud_connection": "direct",
        "onprem_connection": "gateway_required",
        "cdc_options": ["logical_replication", "triggers", "timestamp_column"],
        "bulk_extract": "pg_dump or COPY command",
        "considerations": ["connection_pooling", "read_replica_recommended"],
    },
    "sql_server": {
        "cloud_connection": "direct",
        "onprem_connection": "gateway_required",
        "cdc_options": ["change_tracking", "cdc", "temporal_tables"],
        "fabric_native": "mirroring_available",
        "considerations": ["snapshot_isolation", "index_usage"],
    },
    "blob_storage": {
        "connection": "account_key or sas or managed_identity",
        "patterns": ["wildcard_files", "folder_partition"],
        "formats": ["csv", "parquet", "json", "avro"],
        "considerations": ["file_size", "partition_structure"],
    },
    "sharepoint": {
        "connection": "service_principal or user_auth",
        "objects": ["lists", "document_libraries", "sites"],
        "limitations": ["api_throttling", "5000_item_threshold"],
        "considerations": ["delta_sync", "pagination"],
    },
    "rest_api": {
        "auth_types": ["api_key", "oauth", "bearer_token"],
        "patterns": ["pagination", "rate_limiting", "retry"],
        "considerations": ["response_format", "nested_json"],
    },
}
```

**Decision Logic**:
```python
def analyze_source(source_type, location, volume_gb):
    recommendations = []

    if location == "on_premise":
        recommendations.append({
            "requirement": "gateway",
            "priority": "blocker",
            "message": "On-premises Data Gateway required"
        })

    if volume_gb > 100:
        recommendations.append({
            "requirement": "partitioning",
            "priority": "high",
            "message": "Large volume - recommend partitioned extraction"
        })

    if source_type == "sql_server" and location == "cloud":
        recommendations.append({
            "option": "mirroring",
            "priority": "consider",
            "message": "Fabric Mirroring available for real-time CDC"
        })

    return recommendations
```

### 3. Fabric Architect Agent

**Purpose**: Design the optimal pipeline architecture using Fabric components.

**Component Selection Matrix**:
```python
COMPONENT_DECISION_MATRIX = {
    "Copy Activity": {
        "use_when": [
            "No transformations needed",
            "Simple data movement",
            "Bronze layer ingestion",
            "Less than 20 tables",
        ],
        "avoid_when": [
            "Complex transformations",
            "PII masking required",
            "Data quality checks needed",
        ],
        "strengths": ["Simple", "Fast", "Low cost"],
    },
    "Dataflow Gen2": {
        "use_when": [
            "Light transformations (filter, rename, type cast)",
            "PII masking needed",
            "Visual debugging helpful",
            "Silver layer processing",
        ],
        "avoid_when": [
            "Very large datasets (>100GB)",
            "Complex Python logic",
            "Custom ML models",
        ],
        "strengths": ["Visual", "Built-in transforms", "PII detection"],
    },
    "Notebook (PySpark)": {
        "use_when": [
            "Complex transformations",
            "Large datasets (>100GB)",
            "Custom Python/ML logic",
            "Gold layer aggregations",
            "Data quality frameworks (Great Expectations)",
        ],
        "avoid_when": [
            "Simple copies",
            "Team lacks Python skills",
        ],
        "strengths": ["Flexible", "Powerful", "Scalable"],
    },
    "Mirroring": {
        "use_when": [
            "SQL Server or Azure SQL source",
            "Real-time CDC needed",
            "Continuous sync required",
        ],
        "avoid_when": [
            "Non-SQL sources",
            "One-time migration",
            "Complex transformations at source",
        ],
        "strengths": ["Real-time", "Automatic CDC", "Low latency"],
    },
}
```

**Architecture Patterns**:
```python
ARCHITECTURE_PATTERNS = {
    "simple_copy": {
        "description": "Direct copy from source to destination",
        "layers": ["landing"],
        "components": ["Copy Activity"],
        "use_when": "One-time migration, no transforms, small data",
    },
    "medallion_bronze_only": {
        "description": "Raw data ingestion to Bronze layer",
        "layers": ["bronze"],
        "components": ["Copy Activity with ForEach"],
        "use_when": "Need raw data preservation, transforms done elsewhere",
    },
    "medallion_full": {
        "description": "Complete Bronze → Silver → Gold architecture",
        "layers": ["bronze", "silver", "gold"],
        "components": ["Copy Activity", "Dataflow Gen2", "Notebook"],
        "use_when": "Analytics use case, need data quality, aggregations",
    },
    "streaming": {
        "description": "Real-time event processing",
        "layers": ["stream", "serving"],
        "components": ["Eventstream", "KQL Database"],
        "use_when": "Real-time requirements, event-driven",
    },
}
```

### 4. Transform Expert Agent

**Purpose**: Design transformation logic, data quality rules, and medallion layer processing.

**Transformation Catalog**:
```python
TRANSFORMATION_CATALOG = {
    "cleaning": {
        "deduplication": {
            "description": "Remove duplicate records",
            "implementation": "Dataflow or Notebook",
            "pyspark": "df.dropDuplicates(['key_column'])",
        },
        "null_handling": {
            "description": "Handle null values",
            "options": ["drop", "fill_default", "fill_previous"],
            "implementation": "Dataflow or Notebook",
        },
        "type_conversion": {
            "description": "Convert data types",
            "implementation": "Dataflow (preferred) or Notebook",
        },
        "trim_whitespace": {
            "description": "Clean string columns",
            "implementation": "Dataflow or Notebook",
        },
    },
    "pii_handling": {
        "detection": {
            "description": "Detect PII columns automatically",
            "columns": ["email", "phone", "ssn", "credit_card", "address"],
            "implementation": "Dataflow Gen2 with Presidio",
        },
        "masking_redact": {
            "description": "Replace with placeholder",
            "example": "john@email.com → [REDACTED]",
            "implementation": "Dataflow or Notebook",
        },
        "masking_partial": {
            "description": "Partial masking",
            "example": "john@email.com → j***@***.com",
            "implementation": "Notebook with custom logic",
        },
        "masking_hash": {
            "description": "One-way hash",
            "example": "john@email.com → a1b2c3d4...",
            "implementation": "Notebook with SHA256",
        },
    },
    "enrichment": {
        "lookup_join": {
            "description": "Join with reference data",
            "implementation": "Dataflow or Notebook",
        },
        "derived_columns": {
            "description": "Calculate new columns",
            "implementation": "Dataflow or Notebook",
        },
    },
    "aggregation": {
        "summary_stats": {
            "description": "Sum, count, average, min, max",
            "implementation": "Notebook (preferred for Gold layer)",
        },
        "time_aggregation": {
            "description": "Daily, weekly, monthly rollups",
            "implementation": "Notebook with window functions",
        },
    },
}
```

**Medallion Layer Design**:
```python
MEDALLION_LAYERS = {
    "bronze": {
        "purpose": "Raw data exactly as received from source",
        "transforms": "None - preserve original",
        "format": "Delta table",
        "naming": "{source}_{table}_raw",
        "retention": "Keep forever or per compliance",
    },
    "silver": {
        "purpose": "Cleaned, deduplicated, validated data",
        "transforms": ["dedupe", "null_handling", "type_cast", "pii_mask"],
        "format": "Delta table",
        "naming": "{domain}_{entity}_clean",
        "retention": "Keep forever",
    },
    "gold": {
        "purpose": "Business-ready aggregated data",
        "transforms": ["aggregations", "business_logic", "kpis"],
        "format": "Delta table optimized for queries",
        "naming": "{domain}_{metric}_agg",
        "retention": "Rolling window or forever",
    },
}
```

### 5. Deploy Agent

**Purpose**: Build and deploy the actual pipeline to Fabric.

**Capabilities**:
```python
DEPLOY_CAPABILITIES = {
    "connections": {
        "create_gateway_connection": "For on-premise sources",
        "create_cloud_connection": "For Azure services",
        "create_shortcut": "For external storage access",
    },
    "pipeline": {
        "generate_json": "Create Fabric pipeline JSON",
        "create_activities": "Build Copy, Dataflow, Notebook activities",
        "set_dependencies": "Configure activity dependencies",
        "configure_schedule": "Set up triggers",
    },
    "notebooks": {
        "generate_bronze_notebook": "PySpark for raw ingestion",
        "generate_silver_notebook": "PySpark for cleaning/transforms",
        "generate_gold_notebook": "PySpark for aggregations",
    },
    "monitoring": {
        "configure_alerts": "Set up failure notifications",
        "enable_logging": "Configure diagnostic logging",
    },
}
```

## Orchestration Flow

### State Machine

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   INITIAL   │ ──▶ │  DISCOVERY  │ ──▶ │  ANALYZING  │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                    ┌──────────────────────────┘
                    ▼
            ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
            │  DESIGNING  │ ──▶ │  REVIEWING  │ ──▶ │  DEPLOYING  │
            └─────────────┘     └─────────────┘     └─────────────┘
                                                           │
                                                           ▼
                                                    ┌─────────────┐
                                                    │  COMPLETED  │
                                                    └─────────────┘
```

### Orchestrator Decision Logic

```python
def orchestrator_decide(state, user_message):
    """Decide which agent to call based on current state and message"""

    if state.stage == "INITIAL":
        # Always start with Discovery
        return call_agent("discovery", user_message)

    elif state.stage == "DISCOVERY":
        # Check if we have enough basic info
        if state.has_basic_requirements():
            state.stage = "ANALYZING"
            # Call specialists in parallel
            return call_parallel([
                ("source_analyst", state.source_info),
                ("fabric_architect", state.requirements),
                ("transform_expert", state.transform_needs),
            ])
        else:
            # Need more info from Discovery
            return call_agent("discovery", user_message)

    elif state.stage == "ANALYZING":
        # Merge specialist insights and present design
        state.stage = "DESIGNING"
        return present_design(state.merged_insights)

    elif state.stage == "DESIGNING":
        if user_confirms_design(user_message):
            state.stage = "DEPLOYING"
            return call_agent("deploy", state.final_design)
        else:
            # User wants changes
            return modify_design(user_message)

    elif state.stage == "DEPLOYING":
        state.stage = "COMPLETED"
        return deployment_result
```

## Integration Points

### With Existing Code

1. **azure_ai_agent_service.py**: Base AI service for API calls
2. **fabric_api_service.py**: Fabric SDK operations
3. **main.py**: Chat endpoint integration

### New Files to Create

```
backend/
├── services/
│   └── multi_agent/
│       ├── __init__.py
│       ├── base_agent.py          # Base agent class
│       ├── orchestrator.py        # Main orchestrator
│       ├── discovery_agent.py     # Discovery specialist
│       ├── source_analyst.py      # Source specialist
│       ├── fabric_architect.py    # Fabric specialist
│       ├── transform_expert.py    # Transform specialist
│       ├── deploy_agent.py        # Deployment specialist
│       └── state_manager.py       # Requirements state
```

## Example Conversation Flow

```
User: "I have an on-premise PostgreSQL database with customer data
       that needs to be analyzed in Power BI"

[ORCHESTRATOR] → [DISCOVERY AGENT]
Discovery THINKS:
- "on-premise" = gateway needed
- "PostgreSQL" = specific connection type
- "customer data" = likely PII
- "Power BI" = needs optimized queries, possibly Gold layer

Discovery ASKS:
"I'll help you build a pipeline for your PostgreSQL to Power BI analytics!

 A few questions to design the best solution:
 1. How many tables do you need to bring over?
 2. Roughly what's the data size?
 3. How often does this data change?"

User: "About 15 tables, around 30GB, changes daily"

[ORCHESTRATOR] Has enough info, calls specialists in PARALLEL:

[SOURCE ANALYST] THINKS:
- On-prem PostgreSQL = gateway required
- 30GB = medium size, no special handling needed
- Daily changes = need incremental strategy
- Check: Does gateway exist?

[FABRIC ARCHITECT] THINKS:
- 15 tables = ForEach with parallelism
- Daily refresh = scheduled pipeline
- Power BI = need Gold aggregated layer
- Analytics = Medallion architecture recommended

[TRANSFORM EXPERT] THINKS:
- Customer data = PII likely (names, emails, phones)
- Power BI = clean data needed
- Recommend: Bronze → Silver (with masking) → Gold

[ORCHESTRATOR] Merges insights and presents:

"Based on my analysis, here's my recommended architecture:

 ⚠️  PREREQUISITE NEEDED
 └── On-Premises Data Gateway (not yet installed)

 📐 ARCHITECTURE: Medallion (Bronze → Silver → Gold)

 ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
 │   BRONZE    │ →  │   SILVER    │ →  │    GOLD     │
 │  Copy Act.  │    │  Dataflow   │    │  Notebook   │
 │  15 tables  │    │  + PII Mask │    │  Aggregates │
 └─────────────┘    └─────────────┘    └─────────────┘

 🔒 PII: Auto-detected, will mask in Silver layer
 📅 SCHEDULE: Daily at 2 AM

 Shall I proceed with this design?"

User: "Yes, proceed"

[ORCHESTRATOR] → [DEPLOY AGENT]
Deploy EXECUTES:
1. Check/guide gateway setup
2. Create PostgreSQL connection
3. Generate pipeline JSON
4. Create Bronze Copy Activities (15 tables, parallel)
5. Create Silver Dataflow with PII masking
6. Create Gold Notebook for aggregations
7. Deploy to Fabric workspace
8. Configure daily schedule

"Pipeline deployed successfully!
 Pipeline ID: abc-123
 Next run: Tomorrow 2:00 AM

 Would you like me to trigger a test run now?"
```

## Performance Considerations

### Token Usage
- Each agent call = separate API call
- Parallel calls reduce latency but increase concurrent tokens
- State summaries keep context minimal

### Optimization Strategies
1. **Minimal context passing**: Only pass relevant state to each agent
2. **Parallel execution**: Source, Fabric, Transform agents run simultaneously
3. **Caching**: Cache agent knowledge bases locally
4. **Early termination**: Skip agents if not needed (e.g., no transforms)

## Success Metrics

1. **Requirement Completeness**: All pipeline requirements gathered before design
2. **Design Quality**: Appropriate component selection for use case
3. **User Satisfaction**: Fewer follow-up questions needed
4. **Deployment Success**: Pipelines deploy without errors
5. **Time to Deploy**: Faster than manual design process
