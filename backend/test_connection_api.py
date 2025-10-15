"""
Test the new Fabric Connections API
"""
import asyncio
import sys
sys.path.append('.')

from services.fabric_api_service import FabricAPIService

async def test_create_connection():
    """Test creating a connection using the new API"""

    fabric_service = FabricAPIService()

    print("=" * 80)
    print("TESTING FABRIC CONNECTIONS API")
    print("=" * 80)
    print()

    # Test blob storage connection with different type values
    connection_types_to_try = [
        ("AzureBlobStorage", "AzureBlobStorage"),
        ("AzureBlobs", "AzureBlobs"),
        ("AzureStorage", "AzureStorage"),
        ("Blob", "Blob"),
        ("BlobStorage", "BlobStorage")
    ]

    connection_config = {
        "account_name": "fabricsatest123",
        "account_key": "eyIW38VoXk6BQ8dYJG2FTiAdIEafvXA5btOq+oePQ2frm/WYvpEdUd21I1jjDKm9kPlCoO0cGIjZ+AStOcJPMw==",
        "auth_type": "Key"
    }

    print("Trying different connection type values...")
    print("-" * 80)

    for conn_type, creation_method in connection_types_to_try:
        print(f"\nTrying type='{conn_type}', creationMethod='{creation_method}'...")

        # Temporarily modify the service to use this type
        import json
        token = await fabric_service.get_access_token()

        payload = {
            "connectivityType": "ShareableCloud",
            "displayName": f"Test_{conn_type}",
            "connectionDetails": {
                "type": conn_type,
                "creationMethod": creation_method,
                "parameters": [
                    {
                        "dataType": "Text",
                        "name": "account",
                        "value": "fabricsatest123"
                    }
                ]
            },
            "privacyLevel": "Organizational",
            "credentialDetails": {
                "singleSignOnType": "None",
                "connectionEncryption": "NotEncrypted",
                "skipTestConnection": False,
                "credentials": {
                    "credentialType": "Key",
                    "key": "eyIW38VoXk6BQ8dYJG2FTiAdIEafvXA5btOq+oePQ2frm/WYvpEdUd21I1jjDKm9kPlCoO0cGIjZ+AStOcJPMw=="
                }
            }
        }

        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.fabric.microsoft.com/v1/connections",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code in [200, 201]:
                print(f"   ✅ SUCCESS with type '{conn_type}'!")
                result = response.json()
                print(f"   Connection ID: {result.get('id')}")
                break
            else:
                error_msg = response.text[:200]
                print(f"   ❌ Failed: {error_msg}")

    result = {"success": False}  # Default if all fail

    if result.get("success"):
        print(f"✅ Connection created successfully!")
        print(f"   Connection ID: {result.get('connection_id')}")
        print(f"   Connection Name: {result.get('connection_name')}")
        print()
        print("This connection can now be referenced in Copy Activities!")
        print()
    else:
        print(f"❌ Connection creation failed")
        print(f"   Error: {result.get('error')}")
        print(f"   Status Code: {result.get('status_code')}")
        print()

    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_create_connection())
