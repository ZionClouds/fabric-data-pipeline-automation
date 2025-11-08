"""
Standalone test script to create Microsoft Fabric pipelines with file sources
This tests whether file-based sources can actually work via the Fabric REST API
"""
import asyncio
import httpx
import json
import sys
import os

# Add parent directory to path to import settings
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import settings

class FabricPipelineTester:
    def __init__(self):
        self.base_url = "https://api.fabric.microsoft.com/v1"
        self.token = None

    async def get_access_token(self):
        """Get OAuth2 token for Fabric API"""
        token_url = f"https://login.microsoftonline.com/{settings.FABRIC_TENANT_ID}/oauth2/v2.0/token"

        data = {
            "grant_type": "client_credentials",
            "client_id": settings.FABRIC_CLIENT_ID,
            "client_secret": settings.FABRIC_CLIENT_SECRET,
            "scope": "https://api.fabric.microsoft.com/.default"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)

            if response.status_code == 200:
                self.token = response.json()["access_token"]
                print("[OK] Successfully obtained access token")
                return True
            else:
                print(f"[ERROR] Failed to get token: {response.status_code}")
                print(response.text)
                return False

    def get_headers(self):
        """Get headers for API requests"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    async def test_lakehouse_table_to_table(self, workspace_id: str, lakehouse_id: str):
        """
        TEST 1: Create pipeline with LakehouseTable source (table-to-table)
        This should work without issues
        """
        print("\n" + "="*80)
        print("TEST 1: LakehouseTable → LakehouseTable (Should Work)")
        print("="*80)

        pipeline_def = {
            "displayName": "Test_Table_To_Table",
            "properties": {
                "activities": [
                    {
                        "name": "CopyTableToTable",
                        "type": "Copy",
                        "dependsOn": [],
                        "policy": {
                            "timeout": "0.12:00:00",
                            "retry": 0,
                            "retryIntervalInSeconds": 30
                        },
                        "typeProperties": {
                            "source": {
                                "type": "LakehouseTableSource"
                            },
                            "sink": {
                                "type": "LakehouseTableSink",
                                "tableActionOption": "Append"
                            },
                            "translator": {
                                "type": "TabularTranslator",
                                "typeConversion": True,
                                "typeConversionSettings": {
                                    "allowDataTruncation": True,
                                    "treatBooleanAsNumber": False
                                }
                            }
                        },
                        "inputs": [
                            {
                                "referenceName": f"LH_{lakehouse_id}_source_table",
                                "type": "DatasetReference",
                                "parameters": {}
                            }
                        ],
                        "outputs": [
                            {
                                "referenceName": f"LH_{lakehouse_id}_dest_table",
                                "type": "DatasetReference",
                                "parameters": {}
                            }
                        ]
                    }
                ]
            }
        }

        url = f"{self.base_url}/workspaces/{workspace_id}/dataPipelines"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=pipeline_def, headers=self.get_headers())

            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text}")

            if response.status_code in [200, 201]:
                print("[PASS] TEST 1 PASSED: Table-to-table pipeline created successfully")
                return True
            else:
                print("[FAIL] TEST 1 FAILED")
                return False

    async def test_lakehouse_files_with_workspace_artifact(self, workspace_id: str, lakehouse_id: str):
        """
        TEST 2: Create pipeline with Lakehouse Files using workspace artifact reference
        Testing if workspaceId/itemId in storeSettings works
        """
        print("\n" + "="*80)
        print("TEST 2: Lakehouse Files with workspaceId/itemId")
        print("="*80)

        pipeline_def = {
            "displayName": "Test_Files_With_IDs",
            "properties": {
                "activities": [
                    {
                        "name": "CopyFilesToTable",
                        "type": "Copy",
                        "dependsOn": [],
                        "policy": {
                            "timeout": "0.12:00:00",
                            "retry": 0
                        },
                        "typeProperties": {
                            "source": {
                                "type": "DelimitedTextSource",
                                "storeSettings": {
                                    "type": "LakehouseReadSettings",
                                    "recursive": True,
                                    "wildcardFileName": "*.csv",
                                    "wildcardFolderPath": "Files/test",
                                    "enablePartitionDiscovery": False,
                                    "workspaceId": workspace_id,
                                    "itemId": lakehouse_id
                                },
                                "formatSettings": {
                                    "type": "DelimitedTextReadSettings"
                                }
                            },
                            "sink": {
                                "type": "LakehouseTableSink",
                                "tableActionOption": "Append"
                            }
                        }
                    }
                ]
            }
        }

        url = f"{self.base_url}/workspaces/{workspace_id}/dataPipelines"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=pipeline_def, headers=self.get_headers())

            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text}")

            if response.status_code in [200, 201]:
                print("[PASS] TEST 2 PASSED: Files with workspaceId/itemId works!")
                return True
            else:
                print("[FAIL] TEST 2 FAILED")
                return False

    async def test_lakehouse_files_with_artifact_reference(self, workspace_id: str, lakehouse_id: str):
        """
        TEST 3: Create pipeline with Lakehouse Files using artifact reference
        """
        print("\n" + "="*80)
        print("TEST 3: Lakehouse Files with artifact reference")
        print("="*80)

        pipeline_def = {
            "displayName": "Test_Files_Artifact_Ref",
            "properties": {
                "activities": [
                    {
                        "name": "CopyFilesToTable",
                        "type": "Copy",
                        "dependsOn": [],
                        "policy": {
                            "timeout": "0.12:00:00",
                            "retry": 0
                        },
                        "typeProperties": {
                            "source": {
                                "type": "DelimitedTextSource",
                                "storeSettings": {
                                    "type": "LakehouseReadSettings",
                                    "recursive": True,
                                    "wildcardFileName": "*.csv",
                                    "wildcardFolderPath": "Files/test",
                                    "enablePartitionDiscovery": False,
                                    "artifactId": lakehouse_id
                                },
                                "formatSettings": {
                                    "type": "DelimitedTextReadSettings"
                                }
                            },
                            "sink": {
                                "type": "LakehouseTableSink",
                                "tableActionOption": "Append"
                            }
                        }
                    }
                ]
            }
        }

        url = f"{self.base_url}/workspaces/{workspace_id}/dataPipelines"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=pipeline_def, headers=self.get_headers())

            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text}")

            if response.status_code in [200, 201]:
                print("[PASS] TEST 3 PASSED: Files with artifactId works!")
                return True
            else:
                print("[FAIL] TEST 3 FAILED")
                return False

    async def test_lakehouse_files_minimal(self, workspace_id: str, lakehouse_id: str):
        """
        TEST 4: Minimal file source configuration
        """
        print("\n" + "="*80)
        print("TEST 4: Minimal Lakehouse Files configuration")
        print("="*80)

        pipeline_def = {
            "displayName": "Test_Files_Minimal",
            "properties": {
                "activities": [
                    {
                        "name": "CopyFilesToTable",
                        "type": "Copy",
                        "typeProperties": {
                            "source": {
                                "type": "DelimitedTextSource",
                                "storeSettings": {
                                    "type": "LakehouseReadSettings",
                                    "wildcardFileName": "*.csv",
                                    "wildcardFolderPath": "Files"
                                },
                                "formatSettings": {
                                    "type": "DelimitedTextReadSettings"
                                }
                            },
                            "sink": {
                                "type": "LakehouseTableSink"
                            }
                        }
                    }
                ]
            }
        }

        url = f"{self.base_url}/workspaces/{workspace_id}/dataPipelines"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=pipeline_def, headers=self.get_headers())

            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text}")

            if response.status_code in [200, 201]:
                print("[PASS] TEST 4 PASSED: Minimal configuration works!")
                return True
            else:
                print("[FAIL] TEST 4 FAILED")
                return False

    async def run_all_tests(self, workspace_id: str, lakehouse_id: str):
        """Run all tests"""
        print("\n" + "="*80)
        print("FABRIC PIPELINE FILE SOURCE TESTS")
        print("="*80)
        print(f"Workspace ID: {workspace_id}")
        print(f"Lakehouse ID: {lakehouse_id}")

        # Get access token
        if not await self.get_access_token():
            print("[ERROR] Cannot proceed without access token")
            return

        results = []

        # Run tests
        # results.append(("Table to Table", await self.test_lakehouse_table_to_table(workspace_id, lakehouse_id)))
        results.append(("Files with workspaceId/itemId", await self.test_lakehouse_files_with_workspace_artifact(workspace_id, lakehouse_id)))
        results.append(("Files with artifactId", await self.test_lakehouse_files_with_artifact_reference(workspace_id, lakehouse_id)))
        results.append(("Files minimal config", await self.test_lakehouse_files_minimal(workspace_id, lakehouse_id)))

        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        for test_name, passed in results:
            status = "[PASSED]" if passed else "[FAILED]"
            print(f"{test_name}: {status}")

        passed_count = sum(1 for _, passed in results if passed)
        print(f"\nTotal: {passed_count}/{len(results)} tests passed")

async def main():
    """Main function"""
    # Replace these with your actual IDs
    WORKSPACE_ID = "561d497c-4709-4a69-924d-e59ad8fa6ee1"  # Your workspace ID
    LAKEHOUSE_ID = "71b91fa4-7883-44e1-aa6f-f2d6c8d564ef"  # Your lakehouse ID

    tester = FabricPipelineTester()
    await tester.run_all_tests(WORKSPACE_ID, LAKEHOUSE_ID)

if __name__ == "__main__":
    asyncio.run(main())
