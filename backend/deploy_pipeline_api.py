"""
API-Ready Deployment Module for Fabric Pipeline
This module provides a reusable function that can be called from FastAPI
to deploy pipelines based on user input from AI chat.

This is a standalone version - all template and functions are self-contained.
"""
import asyncio
import httpx
import json
import base64
from typing import Optional, Dict, Any
import msal
import sys

# Configure stdout to handle Unicode on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ============================================================================
# CONFIGURATION
# ============================================================================
# --- Service Principal Credentials ---
TENANT_ID = "e28d23e3-803d-418d-a720-c0bed39f77b6"
CLIENT_ID = "0944e22d-d0f1-40c1-a9fc-f422c05949f3"
CLIENT_SECRET = "oRF8Q~g03M~RuIJ3Tf.eKTS-W8kVvFQXCbIr-ac7"

# --- Fabric API ---
FABRIC_BASE_URL = "https://api.fabric.microsoft.com/v1"
FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"

# --- Default Warehouse Configuration ---
DEFAULT_WAREHOUSE_NAME = "jay-dev-warehouse"
DEFAULT_TABLE_NAME = "processedfiles"

# ============================================================================
# NOTEBOOK SOURCE CODE
# ============================================================================
# This is the PII/PHI detection logic - same as current implementation
NOTEBOOK_PYTHON_SOURCE_TEMPLATE = r"""from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, when, concat_ws, abs as spark_abs,
    current_timestamp, regexp_replace, udf, explode, array
)
from pyspark.sql.types import StringType, ArrayType
import re

# --- Configuration ---
SOURCE_CLAIM_FILE_PATH = "Files/{source_folder}/{{filename}}"
SOURCE_PRIOR_AUTH_FILE_PATH = "Files/priorauths/prior_authorization_data.csv"
OUTPUT_PATH = "Files/{output_folder}"

# Initialize Spark
spark = SparkSession.builder.appName("PHI_PII_Detection").getOrCreate()

# Get filename parameter
fileName = ""
try:
    fileName = spark.conf.get("fileName")
    print(f"Processing file: {{fileName}}")
except Exception as e:
    print(f"Error getting fileName parameter: {{e}}")
    raise

# Full paths
FULL_CLAIM_PATH = SOURCE_CLAIM_FILE_PATH.format(filename=fileName)
FULL_PRIOR_AUTH_PATH = SOURCE_PRIOR_AUTH_FILE_PATH

print(f"Reading claim file from: {{FULL_CLAIM_PATH}}")
print(f"Reading prior auth file from: {{FULL_PRIOR_AUTH_PATH}}")

# Read data
claims_df = spark.read.csv(FULL_CLAIM_PATH, header=True, inferSchema=True)
prior_auth_df = spark.read.csv(FULL_PRIOR_AUTH_PATH, header=True, inferSchema=True)

print(f"Claims records: {{claims_df.count()}}")
print(f"Prior auth records: {{prior_auth_df.count()}}")

# Define PII/PHI detection patterns
pii_phi_patterns = {{
    "SSN": r"\b\d{{3}}-\d{{2}}-\d{{4}}\b",
    "MemberID": r"\b[A-Z]{{2}}\d{{6,10}}\b",
    "DOB": r"\b\d{{2}}/\d{{2}}/\d{{4}}\b",
    "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{{2,}}\b",
    "Phone": r"\b\d{{3}}-\d{{3}}-\d{{4}}\b"
}}

# PII/PHI Detection UDF
def detect_pii_phi(text):
    if not text:
        return []
    detected = []
    for label, pattern in pii_phi_patterns.items():
        if re.search(pattern, str(text)):
            detected.append(label)
    return detected if detected else ["None"]

detect_pii_phi_udf = udf(detect_pii_phi, ArrayType(StringType()))

# Apply detection
claims_with_detection = claims_df.withColumn(
    "DetectedPII_PHI",
    detect_pii_phi_udf(concat_ws(" ", *[col(c) for c in claims_df.columns]))
)

# Join with prior authorization
result_df = claims_with_detection.join(
    prior_auth_df,
    claims_with_detection["ClaimID"] == prior_auth_df["ClaimID"],
    "left"
)

# Add metadata
final_df = result_df.withColumn("ProcessedTimestamp", current_timestamp()) \
                    .withColumn("SourceFile", lit(fileName))

# Write output
print(f"Writing results to: {{OUTPUT_PATH}}")
final_df.write.mode("overwrite").parquet(OUTPUT_PATH)

print(f"Successfully processed {{final_df.count()}} records")
print("Pipeline execution completed!")
"""

# ============================================================================
# PIPELINE TEMPLATE JSON
# ============================================================================
# This is the pipeline template copied from deploy_pipeline.py
# It will be modified with actual IDs during deployment

LAKEHOUSE_NAME = "jay_dev_lakehouse"  # Used in template modification
WAREHOUSE_NAME = "jay-dev-warehouse"   # Used in template modification
TABLE_NAME = "processedfiles"          # Used in template modification

PIPELINE_TEMPLATE_JSON = r"""
{
    "name": "PII_PHI_Pipeline",
    "properties": {
        "activities": [
            {
                "name": "Get Metadata",
                "type": "GetMetadata",
                "dependsOn": [],
                "policy": {
                    "timeout": "0.12:00:00",
                    "retry": 0,
                    "retryIntervalInSeconds": 30,
                    "secureOutput": false,
                    "secureInput": false
                },
                "typeProperties": {
                    "fieldList": [
                        "childItems"
                    ],
                    "datasetSettings": {
                        "annotations": [],
                        "connectionSettings": {
                            "name": "PII_PHI_lakehouse",
                            "properties": {
                                "annotations": [],
                                "type": "Lakehouse",
                                "typeProperties": {
                                    "workspaceId": "91ff9e14-fec6-4d76-ba4e-ba401c7a3f70",
                                    "artifactId": "ac63e579-02e7-4989-b6dc-7b0cbd5eefef",
                                    "rootFolder": "Files"
                                },
                                "externalReferences": {
                                    "connection": "f77bbbd6-2cd0-475b-89b2-eb86f449c7c9"
                                }
                            }
                        },
                        "type": "DelimitedText",
                        "typeProperties": {
                            "location": {
                                "type": "LakehouseLocation",
                                "folderPath": "claims"
                            },
                            "columnDelimiter": ",",
                            "escapeChar": "\\",
                            "firstRowAsHeader": true,
                            "quoteChar": "\""
                        },
                        "schema": []
                    },
                    "storeSettings": {
                        "type": "LakehouseReadSettings",
                        "recursive": true,
                        "enablePartitionDiscovery": false
                    },
                    "formatSettings": {
                        "type": "DelimitedTextReadSettings"
                    }
                }
            },
            {
                "name": "forEach",
                "type": "ForEach",
                "dependsOn": [
                    {
                        "activity": "FilterNewFiles",
                        "dependencyConditions": [
                            "Succeeded"
                        ]
                    }
                ],
                "typeProperties": {
                    "items": {
                        "value": "@activity('FilterNewFiles').output.value",
                        "type": "Expression"
                    },
                    "activities": [
                        {
                            "name": "PHI_PII_detection",
                            "type": "TridentNotebook",
                            "dependsOn": [],
                            "policy": {
                                "timeout": "0.12:00:00",
                                "retry": 0,
                                "retryIntervalInSeconds": 30,
                                "secureOutput": false,
                                "secureInput": false
                            },
                            "typeProperties": {
                                "notebookId": "adf61e58-6f63-4a99-97bf-3f9c4990ca8b",
                                "workspaceId": "91ff9e14-fec6-4d76-ba4e-ba401c7a3f70",
                                "parameters": {
                                    "fileName": {
                                        "value": {
                                            "value": "@item().name",
                                            "type": "Expression"
                                        },
                                        "type": "string"
                                    }
                                }
                            }
                        },
                        {
                            "name": "If Condition1",
                            "type": "IfCondition",
                            "dependsOn": [
                                {
                                    "activity": "PHI_PII_detection",
                                    "dependencyConditions": [
                                        "Succeeded"
                                    ]
                                }
                            ],
                            "typeProperties": {
                                "expression": {
                                    "value": "@bool(\n  json(activity('PHI_PII_detection').output.result.exitValue).PII_PHI\n)\n",
                                    "type": "Expression"
                                },
                                "ifFalseActivities": [
                                    {
                                        "name": "PII_PHI_notification1",
                                        "type": "Office365Email",
                                        "dependsOn": [],
                                        "policy": {
                                            "timeout": "0.12:00:00",
                                            "retry": 0,
                                            "retryIntervalInSeconds": 30,
                                            "secureOutput": false,
                                            "secureInput": false
                                        },
                                        "typeProperties": {
                                            "to": "jay.reddy@zionclouds.com",
                                            "subject": "PHI/PII not detection",
                                            "body": "<p>Hi Jay,</p>\n<p>PHI/PII not detected</p>"
                                        },
                                        "externalReferences": {
                                            "connection": "eedc7b74-01d7-4524-bf31-98ecead7fc5f"
                                        }
                                    }
                                ],
                                "ifTrueActivities": [
                                    {
                                        "name": "PII_PHI_notification",
                                        "type": "Office365Email",
                                        "dependsOn": [],
                                        "policy": {
                                            "timeout": "0.12:00:00",
                                            "retry": 0,
                                            "retryIntervalInSeconds": 30,
                                            "secureOutput": false,
                                            "secureInput": false
                                        },
                                        "typeProperties": {
                                            "to": "jay.reddy@zionclouds.com",
                                            "subject": "PHI/PII detected",
                                            "body": "<p>Hi Jay,</p>\n<p>PII/PHI detected</p>\n<p>@{item()}</p>"
                                        },
                                        "externalReferences": {
                                            "connection": "eedc7b74-01d7-4524-bf31-98ecead7fc5f"
                                        }
                                    }
                                ]
                            }
                        },
                        {
                            "name": "curated Data",
                            "type": "RefreshDataflow",
                            "dependsOn": [
                                {
                                    "activity": "If Condition1",
                                    "dependencyConditions": [
                                        "Succeeded"
                                    ]
                                }
                            ],
                            "policy": {
                                "timeout": "0.12:00:00",
                                "retry": 0,
                                "retryIntervalInSeconds": 30,
                                "secureOutput": false,
                                "secureInput": false
                            },
                            "typeProperties": {
                                "dataflowId": "2c7b952e-3ba0-45b3-b668-586b6bf5e14f",
                                "workspaceId": "91ff9e14-fec6-4d76-ba4e-ba401c7a3f70",
                                "notifyOption": "NoNotification",
                                "dataflowType": "DataflowFabric"
                            }
                        }
                    ]
                }
            },
            {
                "name": "SetEmptyFileArray",
                "type": "SetVariable",
                "dependsOn": [
                    {
                        "activity": "GetProcessedFileNames",
                        "dependencyConditions": [
                            "Succeeded"
                        ]
                    }
                ],
                "policy": {
                    "secureOutput": false,
                    "secureInput": false
                },
                "typeProperties": {
                    "variableName": "ProcessedFileNames",
                    "value": {
                        "value": "[]",
                        "type": "Expression"
                    }
                }
            },
            {
                "name": "FilterNewFiles",
                "type": "Filter",
                "dependsOn": [
                    {
                        "activity": "ForEach1",
                        "dependencyConditions": [
                            "Succeeded"
                        ]
                    }
                ],
                "typeProperties": {
                    "items": {
                        "value": "@activity('Get Metadata').output.childItems",
                        "type": "Expression"
                    },
                    "condition": {
                        "value": "@not(contains(variables('ProcessedFileNames'), item().name))",
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
                        "dependencyConditions": [
                            "Succeeded"
                        ]
                    }
                ],
                "typeProperties": {
                    "items": {
                        "value": "@activity('GetProcessedFileNames').output.resultSets[0].rows",
                        "type": "Expression"
                    },
                    "activities": [
                        {
                            "name": "Set variable1",
                            "type": "SetVariable",
                            "dependsOn": [],
                            "policy": {
                                "secureOutput": false,
                                "secureInput": false
                            },
                            "typeProperties": {
                                "variableName": "ProcessedFileNames",
                                "value": {
                                    "value": "@item().FileName",
                                    "type": "Expression"
                                }
                            }
                        }
                    ]
                }
            },
            {
                "name": "GetProcessedFileNames",
                "type": "Script",
                "dependsOn": [
                    {
                        "activity": "Get Metadata",
                        "dependencyConditions": [
                            "Succeeded"
                        ]
                    }
                ],
                "policy": {
                    "timeout": "0.12:00:00",
                    "retry": 0,
                    "retryIntervalInSeconds": 30,
                    "secureOutput": false,
                    "secureInput": false
                },
                "typeProperties": {
                    "scripts": [
                        {
                            "type": "Query",
                            "text": {
                                "value": "SELECT [FileName] FROM [PII_PHI_lakehouse].[dbo].[processedfiles] WHERE Status = 'Done'",
                                "type": "Expression"
                            }
                        }
                    ],
                    "scriptBlockExecutionTimeout": "02:00:00",
                    "database": "claimsauth"
                },
                "externalReferences": {
                    "connection": "fd7dd7e4-4330-43af-ae8a-d15f9318b440"
                }
            }
        ],
        "variables": {
            "v_fileName": {
                "type": "String"
            },
            "ProcessedFileNames": {
                "type": "String"
            },
            "SetEmptyFileArray": {
                "type": "String"
            },
            "v_ProcessedFileNames": {
                "type": "String"
            }
        }
    }
}
"""

# ============================================================================
# AUTHENTICATION & HELPER FUNCTIONS
# ============================================================================
async def get_access_token() -> str:
    """Get Azure AD access token"""
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        client_credential=CLIENT_SECRET
    )
    result = app.acquire_token_for_client(scopes=[FABRIC_SCOPE])

    if "access_token" not in result:
        raise RuntimeError(f"Authentication failed: {result}")

    return result["access_token"]


async def find_workspace(token: str, workspace_name: str) -> Optional[dict]:
    """Find workspace by name"""
    url = f"{FABRIC_BASE_URL}/workspaces"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()

        workspaces = response.json().get("value", [])
        for ws in workspaces:
            if ws.get("displayName") == workspace_name:
                return ws
    return None


async def find_item_in_workspace(
    token: str,
    workspace_id: str,
    item_type: str,
    item_name: str
) -> Optional[dict]:
    """Find an item by type and name in workspace"""
    url = f"{FABRIC_BASE_URL}/workspaces/{workspace_id}/items"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"type": item_type}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()

        items = response.json().get("value", [])
        for item in items:
            if item.get("displayName") == item_name:
                return item
    return None


async def get_or_create_item(
    token: str,
    workspace_id: str,
    item_type: str,
    item_name: str
) -> dict:
    """Get existing item or create new one"""
    existing = await find_item_in_workspace(token, workspace_id, item_type, item_name)

    if existing:
        print(f"   ! {item_type} already exists: {existing.get('id')}")
        return existing

    print(f"   ! {item_type} not found. Creating '{item_name}'...")
    url = f"{FABRIC_BASE_URL}/workspaces/{workspace_id}/items"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "type": item_type,
        "displayName": item_name
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        item = response.json()
        print(f"   [OK] Created {item_type}: {item.get('id')}")
        return item


# ============================================================================
# MAIN DEPLOYMENT FUNCTION (API-READY)
# ============================================================================

async def deploy_fabric_pipeline(
    workspace_id: str,
    lakehouse_name: str,
    source_folder: str,
    output_folder: str,
    pipeline_name: str,
    warehouse_name: str = DEFAULT_WAREHOUSE_NAME,
    notebook_name: str = "PHI_PII_detection"
) -> Dict[str, Any]:
    """
    Deploy a Fabric pipeline with customizable parameters.

    Args:
        workspace_id: ID of the Fabric workspace (or name for backwards compatibility)
        lakehouse_name: Name of the lakehouse
        source_folder: Source folder name (e.g., "bronze")
        output_folder: Output folder name (e.g., "silver")
        pipeline_name: Name for the pipeline
        warehouse_name: Name of the warehouse (optional)
        notebook_name: Name for the notebook (optional)

    Returns:
        Dict with deployment status and component IDs
    """

    try:
        print(f"\n{'='*80}")
        print(f"  DEPLOYING FABRIC PIPELINE")
        print(f"{'='*80}")
        print(f"\n  Workspace ID:  {workspace_id}")
        print(f"  Lakehouse:     {lakehouse_name}")
        print(f"  Source:        Files/{source_folder}")
        print(f"  Output:        Files/{output_folder}")
        print(f"  Pipeline Name: {pipeline_name}")
        print(f"  Notebook Name: {notebook_name}")
        print(f"\n{'='*80}\n")

        # Step 1: Authenticate
        print("1. Authenticating...")
        token = await get_access_token()
        print("   [OK] Access token obtained")

        # Step 2: Find workspace
        print(f"\n2. Finding workspace '{workspace_name}'...")
        workspace = await find_workspace(token, workspace_name)
        if not workspace:
            raise RuntimeError(f"Workspace '{workspace_name}' not found")
        workspace_id = workspace.get("id")
        print(f"   [OK] Found workspace: {workspace_id}")
        print(f"\n2. Using workspace '{workspace_id}'...")
        print(f"   ✓ Workspace ID: {workspace_id}")


        # Step 3: Find lakehouse
        print(f"\n3. Finding lakehouse...")
        # Try to find by name first, otherwise use first available
        lakehouse = await find_item_in_workspace(token, workspace_id, "Lakehouse", lakehouse_name)
        if not lakehouse:
            # Get first available lakehouse
            print(f"   - Lakehouse '{lakehouse_name}' not found, using first available...")
            lakehouses_url = f"{FABRIC_BASE_URL}/workspaces/{workspace_id}/items?type=Lakehouse"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(lakehouses_url, headers={"Authorization": f"Bearer {token}"})
                response.raise_for_status()
                lakehouses = response.json().get("value", [])
                if not lakehouses:
                    raise RuntimeError(f"No lakehouses found in workspace '{workspace_id}'")
                lakehouse = lakehouses[0]
                print(f"   [OK] Using lakehouse: {lakehouse.get('displayName')}")
        lakehouse_id = lakehouse.get("id")
        lakehouse_display_name = lakehouse.get("displayName")
        print(f"   [OK] Lakehouse: {lakehouse_display_name} ({lakehouse_id})")

        # Step 4: Find warehouse
        print(f"\n4. Finding warehouse...")
        # Try to find by name first, otherwise use first available
        warehouse = await find_item_in_workspace(token, workspace_id, "Warehouse", warehouse_name)
        if not warehouse:
            # Get first available warehouse
            print(f"   - Warehouse '{warehouse_name}' not found, using first available...")
            warehouses_url = f"{FABRIC_BASE_URL}/workspaces/{workspace_id}/items?type=Warehouse"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(warehouses_url, headers={"Authorization": f"Bearer {token}"})
                response.raise_for_status()
                warehouses = response.json().get("value", [])
                if not warehouses:
                    raise RuntimeError(f"No warehouses found in workspace '{workspace_id}'")
                warehouse = warehouses[0]
                print(f"   [OK] Using warehouse: {warehouse.get('displayName')}")
        warehouse_id = warehouse.get("id")
        warehouse_display_name = warehouse.get("displayName")
        print(f"   [OK] Warehouse: {warehouse_display_name} ({warehouse_id})")

        # Step 5: Get warehouse connection
        print(f"\n5. Getting warehouse SQL connection...")
        # Get SQL endpoint
        endpoint_url = f"{FABRIC_BASE_URL}/workspaces/{workspace_id}/warehouses/{warehouse_id}"
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint_url, headers=headers)
            response.raise_for_status()
            warehouse_data = response.json()
            sql_endpoint = warehouse_data.get("properties", {}).get("connectionString")

        print(f"   [OK] SQL Endpoint: {sql_endpoint}")

        # Find or create connection
        # Use the same hardcoded connection name as deploy_pipeline.py
        connection_name = "Warehouse_jay_reddy"
        print(f"   - Looking for connection: {connection_name}")

        # Use global connections endpoint (same as deploy_pipeline.py)
        connections_url = f"{FABRIC_BASE_URL}/connections"
        warehouse_connection = None
        warehouse_connection_id = None

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try to get existing connections
            response = await client.get(connections_url, headers=headers)

            if response.status_code == 200:
                connections = response.json().get("value", [])
                for conn in connections:
                    if conn.get("displayName") == connection_name:
                        warehouse_connection = conn
                        warehouse_connection_id = conn.get("id")
                        print(f"   [OK] Found existing connection: {warehouse_connection_id}")
                        break
            elif response.status_code == 404:
                print(f"   ⚠️  Connections API not available (404)")

            # If we didn't find a connection, try to create one
            if not warehouse_connection_id:
                print(f"   - Attempting to create connection: {connection_name}")

                # Use the same payload format as deploy_pipeline.py
                connection_payload = {
                    "connectivityType": "ShareableCloud",
                    "displayName": connection_name,
                    "connectionDetails": {
                        "type": "SQL",
                        "creationMethod": "Sql",
                        "parameters": [
                            {
                                "dataType": "Text",
                                "name": "server",
                                "value": sql_endpoint
                            },
                            {
                                "dataType": "Text",
                                "name": "database",
                                "value": warehouse_name
                            }
                        ]
                    },
                    "privacyLevel": "Organizational",
                    "credentialDetails": {
                        "singleSignOnType": "None",
                        "connectionEncryption": "NotEncrypted",
                        "skipTestConnection": False,
                        "credentials": {
                            "credentialType": "ServicePrincipal",
                            "servicePrincipalClientId": CLIENT_ID,
                            "servicePrincipalSecret": CLIENT_SECRET,
                            "tenantId": TENANT_ID
                        }
                    }
                }

                try:
                    # Use global connections endpoint (not workspace-specific)
                    global_connections_url = f"{FABRIC_BASE_URL}/connections"
                    create_response = await client.post(
                        global_connections_url,
                        headers=headers,
                        data=json.dumps(connection_payload)
                    )

                    if create_response.status_code in [200, 201]:
                        warehouse_connection = create_response.json()
                        warehouse_connection_id = warehouse_connection.get("id")
                        print(f"   [OK] Created new connection: {warehouse_connection_id}")
                    elif create_response.status_code == 404:
                        print(f"   ⚠️  Cannot create connection - API not available (404)")
                        warehouse_connection_id = None
                        print(f"   → Proceeding without connection (pipeline will use direct lakehouse access)")
                    else:
                        print(f"   ⚠️  Connection creation failed: {create_response.status_code}")
                        print(f"   Response: {create_response.text}")
                        warehouse_connection_id = None
                        print(f"   → Proceeding without connection (pipeline will use direct lakehouse access)")

                except Exception as e:
                    print(f"   ⚠️  Error creating connection: {str(e)}")
                    warehouse_connection_id = None
                    print(f"   → Proceeding without connection (pipeline will use direct lakehouse access)")

        # Step 6: Create notebook with custom folders
        print(f"\n6. Deploying notebook '{notebook_name}'...")

        # Customize notebook source with folder names
        notebook_source = NOTEBOOK_PYTHON_SOURCE_TEMPLATE.format(
            source_folder=source_folder,
            output_folder=output_folder
        )

        # Create or get notebook
        notebook = await get_or_create_item(token, workspace_id, "Notebook", notebook_name)
        notebook_id = notebook.get("id")

        print("   - Waiting for notebook to provision...")
        await asyncio.sleep(3)

        # Create notebook definition with lakehouse attached
        print("   - Creating notebook definition...")
        notebook_def = create_notebook_definition(notebook_source, lakehouse_id, lakehouse_name)

        # Upload notebook
        print("   - Uploading notebook...")
        print(f"   - Notebook preview: {notebook_def[:80]}...")
        
        await update_notebook_definition(token, workspace_id, notebook_id, notebook_def)
        print(f"   [OK] Notebook deployed: {notebook_id}")

        # Step 7: Create pipeline
        print(f"\n7. Deploying pipeline '{pipeline_name}'...")

        pipeline = await get_or_create_item(token, workspace_id, "DataPipeline", pipeline_name)
        pipeline_id = pipeline.get("id")

        print("   - Waiting for pipeline to provision...")
        await asyncio.sleep(3)

        # Create pipeline definition
        print("   - Creating pipeline definition...")
        pipeline_def = create_pipeline_definition(
            workspace_id=workspace_id,
            lakehouse_id=lakehouse_id,
            lakehouse_name=lakehouse_name,
            notebook_id=notebook_id,
            warehouse_name=warehouse_name,
            warehouse_connection_id=warehouse_connection_id,
            source_folder=source_folder
        )

        # Upload pipeline
        print("   - Uploading pipeline...")
        print(f"   - Pipeline preview: {pipeline_def[:80]}...")
        
        await update_pipeline_definition(token, workspace_id, pipeline_id, pipeline_def)
        print(f"   [OK] Pipeline deployed: {pipeline_id}")

        # Success
        print(f"\n{'='*80}")
        print("  ✅ DEPLOYMENT SUCCESSFUL")
        print(f"{'='*80}\n")

        return {
            "status": "success",
            "workspace_id": workspace_id,
            "lakehouse_id": lakehouse_id,
            "lakehouse_name": lakehouse_name,
            "notebook_id": notebook_id,
            "notebook_name": notebook_name,
            "pipeline_id": pipeline_id,
            "pipeline_name": pipeline_name,
            "source_folder": f"Files/{source_folder}",
            "output_folder": f"Files/{output_folder}",
            "message": f"Pipeline '{pipeline_name}' deployed successfully!"
        }

    except Exception as e:
        print(f"\n{'='*80}")
        print("  [FAILED] DEPLOYMENT FAILED")
        print(f"{'='*80}")
        print(f"\n  Error: {str(e)}\n")

        return {
            "status": "failed",
            "error": str(e),
            "message": f"Deployment failed: {str(e)}"
        }


# ============================================================================
# HELPER FUNCTIONS FOR DEFINITIONS
# ============================================================================

def create_notebook_definition(notebook_source: str, lakehouse_id: str, lakehouse_name: str) -> str:
    """
    Create notebook definition in Fabric Python format with lakehouse attached.
    Returns RAW Python content - wrapping happens in update_item_definition.
    """
    # Create Fabric Python notebook format with proper prologue and metadata
    fabric_py_content = f"""# Fabric notebook source

# METADATA ********************

# META {{
# META   "dependencies": {{
# META     "lakehouse": {{
# META       "default_lakehouse": "{lakehouse_id}",
# META       "default_lakehouse_name": "",
# META       "default_lakehouse_workspace_id": ""
# META     }}
# META   }}
# META }}

# CELL ********************

{notebook_source}
"""

    # Return RAW Python content - update_item_definition will base64 encode and wrap it
    return fabric_py_content


def modify_pipeline_definition(
    template_str: str,
    new_workspace_id: str,
    new_lakehouse_id: str,
    new_notebook_id: str,
    warehouse_connection_id: str
) -> str:
    """
    Modifies the pipeline JSON to use all new, automated items.
    FIXED: Includes required storeSettings for Get Metadata to prevent UI errors.
    """
    print("   - Modifying pipeline template...")

    # Load into Python dict for structural changes
    data = json.loads(template_str)

    # --- HELPER: Recursive ID replacement ---
    def replace_ids(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    # Replace known placeholder IDs
                    if "91ff9e14-fec6-4d76-ba4e-ba401c7a3f70" in value:
                         obj[key] = value.replace("91ff9e14-fec6-4d76-ba4e-ba401c7a3f70", new_workspace_id)
                    if "ac63e579-02e7-4989-b6dc-7b0cbd5eefef" in value:
                         obj[key] = value.replace("ac63e579-02e7-4989-b6dc-7b0cbd5eefef", new_lakehouse_id)
                    if "adf61e58-6f63-4a99-97bf-3f9c4990ca8b" in value:
                         obj[key] = value.replace("adf61e58-6f63-4a99-97bf-3f9c4990ca8b", new_notebook_id)
                else:
                    replace_ids(value)
        elif isinstance(obj, list):
            for item in obj:
                replace_ids(item)

    # Initial pass to update all standard IDs in the template
    replace_ids(data)

    # --- 1. CLEANUP: Remove ONLY Email and old Dataflow activities ---
    print("   - Removing Email and old Dataflow activities...")
    activities_to_remove = [
        "PII_PHI_notification1",
        "PII_PHI_notification",
        "curated Data",
        "If Condition1"
    ]

    # Filter main activities list
    data["properties"]["activities"] = [
        act for act in data["properties"]["activities"]
        if act["name"] not in activities_to_remove
    ]

    # Filter activities inside the 'forEach' loop
    foreach_activity = next(act for act in data["properties"]["activities"] if act["name"] == "forEach")
    foreach_activity["typeProperties"]["activities"] = [
        act for act in foreach_activity["typeProperties"]["activities"]
        if act["name"] not in activities_to_remove
    ]

    # --- 2. UPDATE: Get Metadata Activity (CRITICAL FIX) ---
    print(f"   - Rebuilding 'Get Metadata' activity with correct settings")
    get_metadata_activity = next(act for act in data["properties"]["activities"] if act["name"] == "Get Metadata")
    
    # Completely replace typeProperties to ensure valid structure
    get_metadata_activity["typeProperties"] = {
        "fieldList": ["childItems"],
        "storeSettings": {
            "type": "LakehouseReadSettings",
            "recursive": True,
            "enablePartitionDiscovery": False
        },
        "datasetSettings": {
            "type": "Binary",
            "linkedService": {
                "name": LAKEHOUSE_NAME,
                "properties": {
                    "type": "Lakehouse",
                    "typeProperties": {
                        "workspaceId": new_workspace_id,
                        "artifactId": new_lakehouse_id,
                        "rootFolder": "Files"
                    }
                }
            },
            "typeProperties": {
                "location": {
                    "type": "LakehouseLocation",
                    "folderPath": "bronze"
                }
            }
        }
    }

    # --- 3. UPDATE: Script Activity (Warehouse Connection) ---
    print(f"   - Updating 'GetProcessedFileNames' Script activity with warehouse connection")
    script_activity = next(act for act in data["properties"]["activities"] if act["name"] == "GetProcessedFileNames")
    # Update SQL Query and Database
    script_activity["typeProperties"]["scripts"][0]["text"]["value"] = f"SELECT [FileName] FROM [dbo].[{TABLE_NAME}] WHERE Status = 'Done'"
    script_activity["typeProperties"]["database"] = WAREHOUSE_NAME
    # Add Warehouse Connection Reference
    script_activity["externalReferences"] = {
        "connection": warehouse_connection_id
    }

    print("   [OK] Pipeline modification complete!")
    return json.dumps(data)


def create_pipeline_definition(
    workspace_id: str,
    lakehouse_id: str,
    lakehouse_name: str,
    notebook_id: str,
    warehouse_name: str,
    warehouse_connection_id: str = None,
    source_folder: str = "bronze"
) -> str:
    """
    Create pipeline definition using the same template as deploy_pipeline.py.
    Returns RAW JSON string - wrapping happens in update_item_definition.
    """
    if warehouse_connection_id:
        print(f"   → Using warehouse connection: {warehouse_connection_id}")
        # Use the full pipeline template with warehouse filtering
        return modify_pipeline_definition(
            template_str=PIPELINE_TEMPLATE_JSON,
            new_workspace_id=workspace_id,
            new_lakehouse_id=lakehouse_id,
            new_notebook_id=notebook_id,
            warehouse_connection_id=warehouse_connection_id
        )
    else:
        print(f"   → No warehouse connection - pipeline will process all files")
        # For now, still use the same template but we could simplify it
        # The modify function will handle missing warehouse connection gracefully
        return modify_pipeline_definition(
            template_str=PIPELINE_TEMPLATE_JSON,
            new_workspace_id=workspace_id,
            new_lakehouse_id=lakehouse_id,
            new_notebook_id=notebook_id,
            warehouse_connection_id=""  # Empty string for no connection
        )


async def update_notebook_definition(token: str, workspace_id: str, notebook_id: str, python_content: str):
    """
    Update NOTEBOOK definition - Python format only.
    Separate function to avoid any confusion with pipeline updates.
    """
    url = f"{FABRIC_BASE_URL}/workspaces/{workspace_id}/items/{notebook_id}/updateDefinition"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Validate it's Python content
    if not python_content.startswith("# Fabric notebook source"):
        raise ValueError(f"ERROR: Expected Python notebook content starting with '# Fabric notebook source', got: {python_content[:100]}")
    
    print(f"   - Encoding notebook as base64...")
    # Base64 encode
    encoded_payload = base64.b64encode(python_content.encode("utf-8")).decode("ascii")
    
    # Create payload with notebook-content.py path
    update_payload = {
        "definition": {
            "parts": [
                {
                    "path": "notebook-content.py",
                    "payload": encoded_payload,
                    "payloadType": "InlineBase64"
                }
            ]
        }
    }
    
    print(f"   - Sending update with path: notebook-content.py")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, data=json.dumps(update_payload))
        
        if response.status_code not in [200, 202]:
            print(f"   [FAILED] Notebook update failed: {response.status_code}")
            print(f"   Response: {response.text}")
            try:
                error_details = response.json()
                print(f"   Error details: {json.dumps(error_details, indent=2)}")
            except:
                pass
            response.raise_for_status()
        
        # Poll if async
        operation_id = response.headers.get("x-ms-operation-id")
        if operation_id and response.status_code == 202:
            print(f"   - Polling notebook update operation...")
            await poll_operation(token, operation_id)


async def update_pipeline_definition(token: str, workspace_id: str, pipeline_id: str, json_content: str):
    """
    Update PIPELINE definition - JSON format only.
    Separate function to avoid any confusion with notebook updates.
    """
    url = f"{FABRIC_BASE_URL}/workspaces/{workspace_id}/items/{pipeline_id}/updateDefinition"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Validate it's JSON content
    try:
        json.loads(json_content)
        print(f"   - Validated pipeline JSON structure")
    except Exception as e:
        raise ValueError(f"ERROR: Expected valid JSON pipeline content, got error: {e}, content: {json_content[:100]}")
    
    print(f"   - Encoding pipeline as base64...")
    # Base64 encode
    encoded_payload = base64.b64encode(json_content.encode("utf-8")).decode("ascii")
    
    # Create payload with pipeline-content.json path
    update_payload = {
        "definition": {
            "parts": [
                {
                    "path": "pipeline-content.json",
                    "payload": encoded_payload,
                    "payloadType": "InlineBase64"
                }
            ]
        }
    }
    
    print(f"   - Sending update with path: pipeline-content.json")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, data=json.dumps(update_payload))
        
        if response.status_code not in [200, 202]:
            print(f"   [FAILED] Pipeline update failed: {response.status_code}")
            print(f"   Response: {response.text}")
            try:
                error_details = response.json()
                print(f"   Error details: {json.dumps(error_details, indent=2)}")
            except:
                pass
            response.raise_for_status()
        
        # Poll if async
        operation_id = response.headers.get("x-ms-operation-id")
        if operation_id and response.status_code == 202:
            print(f"   - Polling pipeline update operation...")
            await poll_operation(token, operation_id)


async def poll_operation(token: str, operation_id: str, max_attempts: int = 30):
    """Poll operation status until completion"""
    url = f"{FABRIC_BASE_URL}/operations/{operation_id}"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        for _ in range(max_attempts):
            await asyncio.sleep(2)
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                status = data.get("status")

                if status == "Succeeded":
                    return data
                elif status == "Failed":
                    raise RuntimeError(f"Operation failed: {data.get('error')}")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Deploy a pipeline
    result = asyncio.run(deploy_fabric_pipeline(
        workspace_name="jay-dev",
        lakehouse_name="jay_dev_lakehouse",
        source_folder="bronze",
        output_folder="silver",
        pipeline_name="PII_PHI_Pipeline"
    ))

    print("\n" + "="*80)
    print("DEPLOYMENT RESULT:")
    print("="*80)
    print(json.dumps(result, indent=2))