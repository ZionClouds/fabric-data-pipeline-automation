"""
Script to create a notebook that creates the FileIngestionStatus table
in the harshith-dev workspace
"""
import asyncio
import sys
import os

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fabric_api_service import FabricAPIService


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)


async def main():
    """Create table creation notebook"""

    print_header("Create FileIngestionStatus Table Notebook")

    # SQL to create the table
    table_creation_sql = """
# Create FileIngestionStatus Table

# This notebook creates the FileIngestionStatus table for tracking file ingestion

spark.sql(\"\"\"
CREATE TABLE IF NOT EXISTS dbo.FileIngestionStatus (
  Id         INT,
  FileName   VARCHAR(260)  NOT NULL,
  SourcePath VARCHAR(4000),
  Status     VARCHAR(20)   NOT NULL
)
\"\"\")

print("✅ Table 'FileIngestionStatus' created successfully!")

# Verify table creation
result = spark.sql("SHOW TABLES LIKE 'FileIngestionStatus'")
result.show()
"""

    print("\n1. Initializing Fabric API service...")
    fabric_service = FabricAPIService()

    # Get access token
    print("   → Obtaining access token...")
    try:
        token = await fabric_service.get_access_token()
        print(f"   [OK] Token obtained")
    except Exception as e:
        print(f"\n[ERROR] ERROR: Failed to get access token: {e}")
        return

    # Get workspaces
    print("\n2. Fetching workspaces...")
    try:
        workspaces = await fabric_service.list_workspaces()
        print(f"   [OK] Found {len(workspaces)} workspace(s)")
    except Exception as e:
        print(f"\n[ERROR] ERROR: Failed to fetch workspaces: {e}")
        return

    if not workspaces:
        print("\n[ERROR] ERROR: No workspaces found.")
        return

    # Find harshith-dev workspace
    print("\n3. Looking for 'harshith-dev' workspace...")
    target_workspace = None
    for ws in workspaces:
        ws_name = ws.get('displayName', '').lower()
        if 'harshith' in ws_name or 'harshith-dev' in ws_name or 'harshith_dev' in ws_name:
            target_workspace = ws
            break

    if not target_workspace:
        print("\n   [WARNING]  'harshith-dev' workspace not found.")
        print("\n   Available workspaces:")
        for i, ws in enumerate(workspaces):
            print(f"   {i+1}. {ws.get('displayName')} (ID: {ws.get('id')})")

        # Let user select
        workspace_input = input(f"\n   Select workspace (1-{len(workspaces)}) or press Enter to use first: ").strip()
        if workspace_input:
            workspace_idx = int(workspace_input) - 1
        else:
            workspace_idx = 0

        target_workspace = workspaces[workspace_idx]

    workspace_id = target_workspace.get('id')
    workspace_name = target_workspace.get('displayName')
    print(f"   [OK] Using workspace: {workspace_name}")
    print(f"   [OK] Workspace ID: {workspace_id}")

    # Create notebook
    print("\n4. Creating notebook...")
    notebook_name = "Create_FileIngestionStatus_Table"
    print(f"   → Notebook name: {notebook_name}")

    # Create single cell with the SQL
    cells = [
        {
            "cell_type": "code",
            "source": table_creation_sql.strip(),
            "metadata": {},
            "outputs": [],
            "execution_count": None
        }
    ]

    print(f"   → Uploading notebook to workspace...")
    try:
        notebook_result = await fabric_service.create_notebook(
            workspace_id=workspace_id,
            notebook_name=notebook_name,
            cells=cells
        )

        if notebook_result.get("success"):
            notebook_id = notebook_result.get("notebook_id")
            print(f"\n   [SUCCESS] Notebook created successfully!")
            print(f"   [OK] Notebook ID: {notebook_id}")
            print(f"   [OK] Notebook Name: {notebook_name}")
            print()
            print_header("NEXT STEPS")
            print()
            print("   The notebook has been created in your workspace.")
            print()
            print("   To create the table:")
            print(f"   1. Open Microsoft Fabric workspace: {workspace_name}")
            print(f"   2. Find the notebook: {notebook_name}")
            print("   3. Click 'Run all' to execute the notebook")
            print("   4. The FileIngestionStatus table will be created")
            print()
            print("   Table Schema:")
            print("   ┌──────────────┬──────────────┬──────────────┐")
            print("   │ Column       │ Type         │ Constraints  │")
            print("   ├──────────────┼──────────────┼──────────────┤")
            print("   │ Id           │ INT          │              │")
            print("   │ FileName     │ VARCHAR(260) │ NOT NULL     │")
            print("   │ SourcePath   │ VARCHAR(4000)│              │")
            print("   │ Status       │ VARCHAR(20)  │ NOT NULL     │")
            print("   └──────────────┴──────────────┴──────────────┘")
            print()
            print("="*80)
        else:
            print(f"\n[ERROR] ERROR: Failed to create notebook: {notebook_result.get('error')}")
            print()
            print("   Possible issues:")
            print("   - Service principal lacks notebook creation permissions")
            print("   - Workspace does not allow notebook creation")
            print("   - API endpoint restrictions")
            print()
            print("   Alternative: Create the table manually")
            print()
            print("   SQL to run in Fabric SQL Endpoint:")
            print("   " + "-"*76)
            print(table_creation_sql)
            print("   " + "-"*76)
    except Exception as e:
        print(f"\n[ERROR] ERROR: Failed to create notebook: {e}")
        print()
        print("   You can create the table manually using this SQL:")
        print()
        print(table_creation_sql)


if __name__ == "__main__":
    asyncio.run(main())
