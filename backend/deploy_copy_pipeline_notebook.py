"""
Deploy a new data pipeline with Notebook activity to copy data from Azure Blob to Lakehouse
Since Copy Activity with connections isn't working yet, we'll use a Notebook approach
"""
import asyncio
import sys
sys.path.append('.')

from services.fabric_api_service import FabricAPIService

async def deploy_copy_pipeline_with_notebook():
    """Deploy pipeline with Notebook activity for data copy"""

    fabric_service = FabricAPIService()

    # Configuration
    WORKSPACE_ID = "c64f4ec0-087b-4ff7-a94e-9fe5cc5370cb"  # soaham-test workspace
    LAKEHOUSE_NAME = "soaham_test_lakehouse"

    print("=" * 80)
    print("DEPLOYING DATA PIPELINE WITH NOTEBOOK ACTIVITY")
    print("=" * 80)
    print()

    # Notebook code to copy data from blob to lakehouse
    notebook_code = """
# Copy data from Azure Blob Storage to Lakehouse
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit

# Azure Blob Storage configuration
storage_account_name = "fabricsatest123"
storage_account_key = "eyIW38VoXk6BQ8dYJG2FTiAdIEafvXA5btOq+oePQ2frm/WYvpEdUd21I1jjDKm9kPlCoO0cGIjZ+AStOcJPMw=="
container_name = "fabric"
file_path = "amazon.csv"
target_table = "bronze_amazon_products"

# Configure blob storage access
spark.conf.set(
    f"fs.azure.account.key.{storage_account_name}.blob.core.windows.net",
    storage_account_key
)

# Build blob storage path
blob_path = f"wasbs://{container_name}@{storage_account_name}.blob.core.windows.net/{file_path}"

print(f"Reading data from: {blob_path}")

# Read CSV from blob storage
df = spark.read.format("csv") \\
    .option("header", "true") \\
    .option("inferSchema", "true") \\
    .load(blob_path)

# Add metadata columns
df_with_metadata = df.withColumn("ingestion_timestamp", current_timestamp()) \\
    .withColumn("source_file", lit(file_path)) \\
    .withColumn("source_system", lit("azure_blob_storage"))

print(f"Loaded {df_with_metadata.count()} rows")

# Write to lakehouse table
df_with_metadata.write.format("delta") \\
    .mode("append") \\
    .saveAsTable(target_table)

print(f"Successfully appended data to {target_table}")
"""

    # Step 1: Create Notebook
    print("Step 1: Creating notebook for data copy...")
    print("-" * 80)

    notebook_result = await fabric_service.create_notebook(
        workspace_id=WORKSPACE_ID,
        notebook_name="Copy_BlobToLakehouse_Notebook",
        notebook_code=notebook_code
    )

    if notebook_result.get("success"):
        notebook_id = notebook_result.get("notebook_id")
        print(f"✅ Notebook created successfully!")
        print(f"   Notebook ID: {notebook_id}")
        print(f"   Notebook Name: Copy_BlobToLakehouse_Notebook")

        # If status is 202, notebook is being created async - wait a bit
        if notebook_result.get("status_code") == 202:
            print(f"   Status: Creating (async)... waiting 30 seconds")
            await asyncio.sleep(30)
            print(f"   ✅ Should be ready now")
        print()
    else:
        print(f"❌ Notebook creation failed: {notebook_result.get('error')}")
        print("   Notebook might already exist, continuing...")
        print()

    # Step 2: Create Pipeline with Notebook Activity
    print("Step 2: Creating pipeline with Notebook activity...")
    print("-" * 80)

    pipeline_definition = {
        "name": "Amazon_BlobToLakehouse_Pipeline",
        "properties": {
            "activities": [
                {
                    "name": "Copy_Amazon_Data",
                    "type": "SynapseNotebook",
                    "dependsOn": [],
                    "policy": {
                        "timeout": "0.12:00:00",
                        "retry": 2,
                        "retryIntervalInSeconds": 30
                    },
                    "typeProperties": {
                        "notebook": {
                            "referenceName": "Copy_BlobToLakehouse_Notebook",
                            "type": "NotebookReference"
                        },
                        "parameters": {}
                    }
                }
            ],
            "annotations": [],
            "folder": {
                "name": "AI Generated Pipelines"
            }
        }
    }

    print(f"Pipeline Name: Amazon_BlobToLakehouse_Pipeline")
    print(f"Activity: Copy_Amazon_Data (Notebook)")
    print(f"Notebook: Copy_BlobToLakehouse_Notebook")
    print(f"Source: fabricsatest123/fabric/amazon.csv")
    print(f"Destination: {LAKEHOUSE_NAME}/bronze_amazon_products")
    print(f"Mode: Append")
    print()

    # Step 3: Deploy Pipeline
    print("Step 3: Deploying pipeline to Fabric...")
    print("-" * 80)

    pipeline_result = await fabric_service.create_pipeline(
        workspace_id=WORKSPACE_ID,
        pipeline_name="Amazon_BlobToLakehouse_Pipeline",
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
        print(f"Workspace: soaham-test ({WORKSPACE_ID})")
        print()
        print("Pipeline Details:")
        print(f"  • 1 Notebook activity")
        print(f"  • Notebook: Copy_BlobToLakehouse_Notebook")
        print(f"  • Source: Azure Blob Storage (fabricsatest123/fabric/amazon.csv)")
        print(f"  • Destination: Lakehouse (bronze_amazon_products)")
        print(f"  • Mode: Append data to table")
        print()
        print("Next Steps:")
        print("  1. Open the pipeline in Fabric workspace 'soaham-test'")
        print("  2. Verify the Notebook activity configuration")
        print("  3. Run the pipeline to copy data from blob to lakehouse")
        print("  4. Check the bronze_amazon_products table in lakehouse")
        print()
    else:
        print("❌ PIPELINE DEPLOYMENT FAILED")
        print()
        print(f"Error: {pipeline_result.get('error')}")
        print()

    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(deploy_copy_pipeline_with_notebook())
