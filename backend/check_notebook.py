"""
Script to check if notebook was actually created in the workspace
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fabric_api_service import FabricAPIService


async def main():
    """Check if notebook exists"""

    print("\n" + "="*80)
    print("  Checking Notebook Creation Status")
    print("="*80)

    fabric_service = FabricAPIService()

    # Get access token
    print("\n1. Authenticating...")
    token = await fabric_service.get_access_token()
    print("   ✓ Authenticated")

    # Get workspaces
    print("\n2. Finding harshith-dev workspace...")
    workspaces = await fabric_service.list_workspaces()

    target_workspace = None
    for ws in workspaces:
        if 'harshith' in ws.get('displayName', '').lower():
            target_workspace = ws
            break

    if not target_workspace:
        print("   ❌ harshith-dev workspace not found")
        return

    workspace_id = target_workspace.get('id')
    workspace_name = target_workspace.get('displayName')
    print(f"   ✓ Found workspace: {workspace_name}")
    print(f"   ✓ Workspace ID: {workspace_id}")

    # List notebooks in workspace
    print("\n3. Listing notebooks in workspace...")

    list_url = f"{fabric_service.base_url}/workspaces/{workspace_id}/notebooks"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    import httpx
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(list_url, headers=headers)

        if response.status_code == 200:
            notebooks_data = response.json()
            notebooks = notebooks_data.get("value", [])

            print(f"   ✓ Found {len(notebooks)} notebook(s) in workspace\n")

            if notebooks:
                print("   Notebooks:")
                print("   " + "-"*76)
                for i, nb in enumerate(notebooks):
                    nb_name = nb.get("displayName", nb.get("name", "Unknown"))
                    nb_id = nb.get("id", "N/A")
                    nb_type = nb.get("type", "N/A")
                    print(f"   {i+1}. {nb_name}")
                    print(f"      ID: {nb_id}")
                    print(f"      Type: {nb_type}")
                    print()

                # Check for our specific notebook
                print("   " + "-"*76)
                our_notebook = None
                for nb in notebooks:
                    nb_name = nb.get("displayName", nb.get("name", ""))
                    if "FileIngestionStatus" in nb_name or "Create_FileIngestionStatus_Table" in nb_name:
                        our_notebook = nb
                        break

                if our_notebook:
                    print("\n   ✅ SUCCESS: Notebook 'Create_FileIngestionStatus_Table' EXISTS!")
                    print(f"   ✓ Notebook ID: {our_notebook.get('id')}")
                    print(f"   ✓ Display Name: {our_notebook.get('displayName')}")
                    print(f"\n   You can now:")
                    print(f"   1. Open it in Fabric UI")
                    print(f"   2. Run it to create the table")
                else:
                    print("\n   ❌ FAILED: Notebook 'Create_FileIngestionStatus_Table' NOT FOUND")
                    print("\n   This is the known issue where notebooks return 202 but don't actually get created.")
                    print("\n   Workaround: Create the notebook manually in Fabric UI")
            else:
                print("   ❌ No notebooks found in workspace")
                print("\n   This confirms the notebook was NOT created.")
                print("   The API returned 202 (Accepted) but the notebook never appeared.")

        else:
            print(f"   ❌ Failed to list notebooks: {response.status_code}")
            print(f"   Response: {response.text}")

    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(main())
