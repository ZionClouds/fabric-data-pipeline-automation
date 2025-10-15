"""
Deploy a new data pipeline with Copy Data activity from Azure Blob to Lakehouse
"""
import asyncio
import sys
sys.path.append('.')

from services.fabric_api_service import FabricAPIService

async def deploy_copy_pipeline():
    """Deploy pipeline with Copy Data activity"""

    fabric_service = FabricAPIService()

    # Configuration
    WORKSPACE_ID = "c64f4ec0-087b-4ff7-a94e-9fe5cc5370cb"  # soaham-test workspace
    LAKEHOUSE_NAME = "soaham_test_lakehouse"

    print("=" * 80)
    print("DEPLOYING COPY DATA PIPELINE")
    print("=" * 80)
    print()

    # Step 1: Create Blob Storage Connection
    print("Step 1: Creating Azure Blob Storage connection...")
    print("-" * 80)

    connection_config = {
        "account_name": "fabricsatest123",
        "account_key": "eyIW38VoXk6BQ8dYJG2FTiAdIEafvXA5btOq+oePQ2frm/WYvpEdUd21I1jjDKm9kPlCoO0cGIjZ+AStOcJPMw==",
        "auth_type": "Key"
    }

    # Try to create connection - if it fails, we'll use notebook approach
    try:
        connection_result = await fabric_service.create_connection(
            workspace_id=WORKSPACE_ID,
            connection_name="AzureBlob_Amazon_Connection",
            source_type="blob",
            connection_config=connection_config
        )
    except Exception as e:
        print(f"⚠️  Connection API not available: {str(e)}")
        connection_result = {"success": False}

    if connection_result.get("success"):
        connection_id = connection_result.get("connection_id")
        connection_name = connection_result.get("connection_name")
        print(f"✅ Connection created successfully!")
        print(f"   Connection ID: {connection_id}")
        print(f"   Connection Name: {connection_name}")
        print()
    else:
        print(f"❌ Connection creation failed: {connection_result.get('error')}")
        print("   Continuing anyway - connection might already exist...")
        connection_name = "AzureBlob_Amazon_Connection"
        print()

    # Step 2: Create Pipeline Definition with Copy Activity
    print("Step 2: Creating pipeline with Copy Data activity...")
    print("-" * 80)

    pipeline_definition = {
        "name": "CopyBlob_To_Lakehouse_Pipeline",
        "properties": {
            "activities": [
                {
                    "name": "Copy_Amazon_Data",
                    "type": "Copy",
                    "dependsOn": [],
                    "policy": {
                        "timeout": "0.12:00:00",
                        "retry": 2,
                        "retryIntervalInSeconds": 30
                    },
                    "typeProperties": {
                        "source": {
                            "type": "DelimitedTextSource",
                            "connection": {
                                "referenceName": connection_name,
                                "type": "ConnectionReference"
                            },
                            "storeSettings": {
                                "type": "AzureBlobStorageReadSettings",
                                "recursive": False,
                                "wildcardFileName": "amazon.csv",
                                "container": "fabric"
                            },
                            "formatSettings": {
                                "type": "DelimitedTextReadSettings"
                            }
                        },
                        "sink": {
                            "type": "LakehouseSink",
                            "workspaceId": WORKSPACE_ID,
                            "rootFolder": "Tables",
                            "table": "bronze_amazon_products",
                            "tableActionOption": "Append"
                        },
                        "enableStaging": False
                    }
                }
            ],
            "annotations": [],
            "folder": {
                "name": "AI Generated Pipelines"
            }
        }
    }

    print(f"Pipeline Name: CopyBlob_To_Lakehouse_Pipeline")
    print(f"Activity: Copy_Amazon_Data (Azure Blob → Lakehouse)")
    print(f"Source: fabricsatest123/fabric/amazon.csv")
    print(f"Destination: {LAKEHOUSE_NAME}/Tables/bronze_amazon_products")
    print(f"Table Action: Append")
    print()

    # Step 3: Deploy Pipeline
    print("Step 3: Deploying pipeline to Fabric...")
    print("-" * 80)

    pipeline_result = await fabric_service.create_pipeline(
        workspace_id=WORKSPACE_ID,
        pipeline_name="CopyBlob_To_Lakehouse_Pipeline",
        pipeline_definition=pipeline_definition
    )

    print()
    print("=" * 80)
    print("DEPLOYMENT RESULT")
    print("=" * 80)
    print()

    if pipeline_result.get("success"):
        print("✅ PIPELINE DEPLOYED SUCCESSFULLY!")
        print()
        print(f"Pipeline ID: {pipeline_result.get('pipeline_id')}")
        print(f"Pipeline Name: {pipeline_result.get('pipeline_name')}")
        print(f"Workspace ID: {pipeline_result.get('workspace_id')}")
        print()
        print("Pipeline Details:")
        print(f"  • 1 Copy Data activity")
        print(f"  • Source: Azure Blob Storage (fabricsatest123/fabric/amazon.csv)")
        print(f"  • Destination: Lakehouse ({LAKEHOUSE_NAME}/bronze_amazon_products)")
        print(f"  • Connection: {connection_name}")
        print(f"  • Action: Append data to table")
        print()
        print("Next Steps:")
        print("  1. Open the pipeline in Fabric workspace")
        print("  2. Verify the Copy activity configuration")
        print("  3. Run the pipeline to test data copy")
        print()
    else:
        print("❌ PIPELINE DEPLOYMENT FAILED")
        print()
        print(f"Error: {pipeline_result.get('error')}")
        print()

    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(deploy_copy_pipeline())
