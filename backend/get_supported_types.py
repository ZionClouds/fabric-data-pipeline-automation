"""
Get list of supported connection types from Fabric API
"""
import asyncio
import sys
sys.path.append('.')

from services.fabric_api_service import FabricAPIService
import httpx

async def get_supported_types():
    """Get supported connection types from Fabric API"""

    fabric_service = FabricAPIService()

    print("=" * 80)
    print("GETTING SUPPORTED CONNECTION TYPES FROM FABRIC API")
    print("=" * 80)
    print()

    try:
        token = await fabric_service.get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = "https://api.fabric.microsoft.com/v1/connections/supportedConnectionTypes"

        print(f"Calling: {url}")
        print()

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                result = response.json()

                print("✅ SUCCESS! Supported connection types:")
                print("=" * 80)
                print()

                # Look for blob storage types
                print("Looking for Azure Blob Storage related types...")
                print("-" * 80)

                types_list = result.get("value", [])

                blob_types = []
                for conn_type in types_list:
                    type_name = conn_type.get("type", "")
                    display_name = conn_type.get("displayName", "")

                    if "blob" in type_name.lower() or "blob" in display_name.lower():
                        blob_types.append(conn_type)
                        print(f"\n🔹 Type: {type_name}")
                        print(f"   Display Name: {display_name}")

                        # Show creation methods
                        creation_methods = conn_type.get("creationMethods", [])
                        if creation_methods:
                            print(f"   Creation Methods:")
                            for method in creation_methods:
                                print(f"      - {method}")

                        # Show parameters
                        parameters = conn_type.get("parameters", [])
                        if parameters:
                            print(f"   Parameters:")
                            for param in parameters:
                                param_name = param.get("name")
                                param_type = param.get("dataType")
                                required = param.get("required", False)
                                print(f"      - {param_name} ({param_type}) {'[REQUIRED]' if required else ''}")

                print()
                print("=" * 80)
                print(f"Found {len(blob_types)} blob storage related types")
                print()

                if blob_types:
                    print("✅ We can use one of these types to create the connection!")
                else:
                    print("⚠️  No blob storage types found, showing all types:")
                    print()
                    for conn_type in types_list[:10]:  # Show first 10
                        print(f"  • {conn_type.get('type')} - {conn_type.get('displayName')}")

            else:
                print(f"❌ API call failed: {response.status_code}")
                print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(get_supported_types())
