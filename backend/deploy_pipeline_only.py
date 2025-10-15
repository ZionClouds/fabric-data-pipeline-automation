"""
Deploy Only Pipeline - Use existing connection and shortcut
"""

import asyncio
import logging
import sys
from services.fabric_api_service import FabricAPIService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    print("=" * 80)
    print("🚀 Creating Pipeline with Error Handling for CSV")
    print("=" * 80)
    print()

    # Configuration
    WORKSPACE_ID = "c64f4ec0-087b-4ff7-a94e-9fe5cc5370cb"
    LAKEHOUSE_ID = "5bb4039e-fe83-4a78-a314-145ce103cc64"
    SHORTCUT_NAME = "amazon_data"  # Existing shortcut
    PIPELINE_NAME = "Copy_Amazon_Data_WithErrorHandling"
    TARGET_TABLE_NAME = "amazon"

    fabric_service = FabricAPIService()

    try:
        print("🔧 Creating Data Pipeline with CSV Error Handling...")
        print(f"   Pipeline Name: {PIPELINE_NAME}")
        print(f"   Source: Lakehouse Files/{SHORTCUT_NAME}")
        print(f"   Sink: Lakehouse Tables/{TARGET_TABLE_NAME}")
        print(f"   Error Handling: Skip incompatible rows ✅")
        print()

        # Pipeline definition with error handling
        pipeline_definition = {
            "properties": {
                "activities": [
                    {
                        "name": "Copy_ShortcutToTable",
                        "type": "Copy",
                        "dependsOn": [],
                        "policy": {
                            "timeout": "0.12:00:00",
                            "retry": 2,
                            "retryIntervalInSeconds": 30,
                            "secureOutput": False,
                            "secureInput": False
                        },
                        "userProperties": [],
                        "typeProperties": {
                            "enableSkipIncompatibleRow": True,
                            "source": {
                                "type": "DelimitedTextSource",
                                "storeSettings": {
                                    "type": "LakehouseReadSettings",
                                    "recursive": True,
                                    "wildcardFileName": "*.csv",
                                    "enablePartitionDiscovery": False
                                },
                                "formatSettings": {
                                    "type": "DelimitedTextReadSettings",
                                    "skipLineCount": 0
                                },
                                "datasetSettings": {
                                    "annotations": [],
                                    "linkedService": {
                                        "name": "soaham_test_lakehouse",
                                        "properties": {
                                            "annotations": [],
                                            "type": "Lakehouse",
                                            "typeProperties": {
                                                "workspaceId": WORKSPACE_ID,
                                                "artifactId": LAKEHOUSE_ID,
                                                "rootFolder": "Files"
                                            }
                                        }
                                    },
                                    "type": "DelimitedText",
                                    "typeProperties": {
                                        "location": {
                                            "type": "LakehouseLocation",
                                            "folderPath": SHORTCUT_NAME
                                        },
                                        "columnDelimiter": ",",
                                        "escapeChar": "\\",
                                        "firstRowAsHeader": True,
                                        "quoteChar": "\""
                                    },
                                    "schema": []
                                }
                            },
                            "sink": {
                                "type": "LakehouseTableSink",
                                "tableActionOption": "Append",
                                "partitionOption": "None",
                                "datasetSettings": {
                                    "annotations": [],
                                    "linkedService": {
                                        "name": "soaham_test_lakehouse",
                                        "properties": {
                                            "annotations": [],
                                            "type": "Lakehouse",
                                            "typeProperties": {
                                                "workspaceId": WORKSPACE_ID,
                                                "artifactId": LAKEHOUSE_ID,
                                                "rootFolder": "Tables"
                                            }
                                        }
                                    },
                                    "type": "LakehouseTable",
                                    "schema": [],
                                    "typeProperties": {
                                        "schema": "",
                                        "table": TARGET_TABLE_NAME
                                    }
                                }
                            },
                            "enableStaging": False
                        }
                    }
                ]
            }
        }

        # Create pipeline
        pipeline_result = await fabric_service.create_pipeline(
            workspace_id=WORKSPACE_ID,
            pipeline_name=PIPELINE_NAME,
            pipeline_definition=pipeline_definition
        )

        if pipeline_result.get("success"):
            print(f"✅ Pipeline created successfully!")
            print(f"   Pipeline ID: {pipeline_result.get('pipeline_id')}")
            print(f"   Pipeline Name: {PIPELINE_NAME}")
            print()
            print("=" * 80)
            print("🎉 DEPLOYMENT COMPLETE!")
            print("=" * 80)
            print()
            print("📝 Next Steps:")
            print(f"   1. Open pipeline '{PIPELINE_NAME}' in Fabric UI")
            print("   2. Click 'Run' to copy data")
            print("   3. Bad rows (like line 23) will be skipped automatically ✅")
            print(f"   4. Check Tables/{TARGET_TABLE_NAME} for data")
            print()
        else:
            print(f"❌ Pipeline creation failed: {pipeline_result.get('error')}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
