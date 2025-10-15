"""
Test creating Azure Blob Storage connection with correct parameters
"""
import asyncio
import sys
sys.path.append('.')

from services.fabric_api_service import FabricAPIService

async def test_create_blob_connection():
    """Test creating a blob storage connection"""

    fabric_service = FabricAPIService()

    print("=" * 80)
    print("CREATING AZURE BLOB STORAGE CONNECTION")
    print("=" * 80)
    print()

    connection_config = {
        "account_name": "fabricsatest123",
        "account_key": "eyIW38VoXk6BQ8dYJG2FTiAdIEafvXA5btOq+oePQ2frm/WYvpEdUd21I1jjDKm9kPlCoO0cGIjZ+AStOcJPMw==",
        "auth_type": "Key"
    }

    result = await fabric_service.create_connection(
        connection_name="BlobStorage_Amazon_Data",
        source_type="blob",
        connection_config=connection_config
    )

    if result.get("success"):
        connection_id = result.get("connection_id")
        print(f"✅ CONNECTION CREATED SUCCESSFULLY!")
        print()
        print(f"Connection ID: {connection_id}")
        print(f"Connection Name: {result.get('connection_name')}")
        print()
        print("=" * 80)
        print("NEXT STEPS:")
        print("=" * 80)
        print()
        print("1. This connection can now be referenced in Copy Activities")
        print(f"2. Use connection ID '{connection_id}' in pipeline activities")
        print("3. Re-enable Copy Activities in fabric_api_service.py")
        print("4. Update Copy Activity source to reference this connection")
        print()
    else:
        print(f"❌ CONNECTION CREATION FAILED")
        print()
        print(f"Error: {result.get('error')}")
        print(f"Status Code: {result.get('status_code')}")
        print()

if __name__ == "__main__":
    asyncio.run(test_create_blob_connection())
