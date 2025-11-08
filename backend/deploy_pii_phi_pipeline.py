"""
Full Automation Script: Deploy PII/PHI Detection Pipeline
This script handles the complete deployment:
1. Creates notebook with parameter cells from phi_pii_detection.py
2. Gets workspace and lakehouse IDs from current workspace
3. Prompts for connection IDs (Office365, SQL)
4. Replaces RefreshDataflow with Copy Data activity
5. Updates all external references in pipeline.json
6. Deploys the complete pipeline to Fabric
"""
import asyncio
import json
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


def print_step(step_num, text):
    """Print formatted step"""
    print(f"\n{step_num}. {text}")


async def main():
    """Full automation deployment"""

    print_header("PII/PHI Detection Pipeline - Full Automation Deployment")

    # -------------------------------------------------------------------------
    # STEP 1: Load Python code and pipeline JSON
    # -------------------------------------------------------------------------
    print_step(1, "Loading source files...")

    # Load phi_pii_detection.py
    notebook_code_path = "../phi_pii_detection.py"
    if not os.path.exists(notebook_code_path):
        print(f"\n❌ ERROR: File not found: {notebook_code_path}")
        return

    with open(notebook_code_path, 'r') as f:
        notebook_python_code = f.read()

    print(f"   ✓ Loaded notebook code: {notebook_code_path}")
    print(f"   ✓ Code length: {len(notebook_python_code)} characters")

    # Load pipeline.json
    pipeline_json_path = "../pipeline.json"
    if not os.path.exists(pipeline_json_path):
        print(f"\n❌ ERROR: File not found: {pipeline_json_path}")
        return

    with open(pipeline_json_path, 'r') as f:
        pipeline_json = json.load(f)

    print(f"   ✓ Loaded pipeline definition: {pipeline_json_path}")
    print(f"   ✓ Pipeline name: {pipeline_json.get('name')}")
    print(f"   ✓ Activities: {len(pipeline_json.get('properties', {}).get('activities', []))}")

    # -------------------------------------------------------------------------
    # STEP 2: Initialize Fabric API service
    # -------------------------------------------------------------------------
    print_step(2, "Initializing Fabric API service...")

    fabric_service = FabricAPIService()

    # Get access token
    print("   → Obtaining access token...")
    try:
        token = await fabric_service.get_access_token()
        print(f"   ✓ Token obtained (length: {len(token)})")
    except Exception as e:
        print(f"\n❌ ERROR: Failed to get access token: {e}")
        return

    # -------------------------------------------------------------------------
    # STEP 3: Get workspace and lakehouse
    # -------------------------------------------------------------------------
    print_step(3, "Fetching workspace and lakehouse information...")

    try:
        workspaces = await fabric_service.list_workspaces()
        print(f"   ✓ Found {len(workspaces)} workspace(s)")
    except Exception as e:
        print(f"\n❌ ERROR: Failed to fetch workspaces: {e}")
        return

    if not workspaces:
        print("\n❌ ERROR: No workspaces found. Please check your service principal permissions.")
        return

    # Display workspaces
    print("\n   Available workspaces:")
    for i, ws in enumerate(workspaces):
        print(f"   {i+1}. {ws.get('displayName')} (ID: {ws.get('id')})")

    # Select workspace
    if len(workspaces) == 1:
        workspace_idx = 0
        print(f"\n   → Auto-selected (only one workspace)")
    else:
        workspace_input = input(f"\n   Select workspace (1-{len(workspaces)}) [1]: ").strip()
        workspace_idx = (int(workspace_input) - 1) if workspace_input else 0

    workspace_id = workspaces[workspace_idx].get('id')
    workspace_name = workspaces[workspace_idx].get('displayName')
    print(f"   ✓ Using workspace: {workspace_name}")

    # Get lakehouses in workspace
    try:
        lakehouses = await fabric_service.get_workspace_lakehouses(workspace_id)
        print(f"   ✓ Found {len(lakehouses)} lakehouse(s)")
    except Exception as e:
        print(f"\n⚠️  WARNING: Failed to fetch lakehouses: {e}")
        lakehouses = []

    lakehouse_id = None
    lakehouse_name = None

    if lakehouses:
        print("\n   Available lakehouses:")
        for i, lh in enumerate(lakehouses):
            print(f"   {i+1}. {lh.get('displayName')} (ID: {lh.get('id')})")

        if len(lakehouses) == 1:
            lakehouse_idx = 0
            print(f"\n   → Auto-selected (only one lakehouse)")
        else:
            lakehouse_input = input(f"\n   Select lakehouse (1-{len(lakehouses)}) [1]: ").strip()
            lakehouse_idx = (int(lakehouse_input) - 1) if lakehouse_input else 0

        lakehouse_id = lakehouses[lakehouse_idx].get('id')
        lakehouse_name = lakehouses[lakehouse_idx].get('displayName')
        print(f"   ✓ Using lakehouse: {lakehouse_name}")
    else:
        print("\n   ⚠️  No lakehouses found. You'll need to create one first.")

    # -------------------------------------------------------------------------
    # STEP 4: Create notebook with parameter cells
    # -------------------------------------------------------------------------
    print_step(4, "Creating notebook with parameter cells...")

    notebook_name = "PHI_PII_detection_notebook"
    print(f"   → Notebook name: {notebook_name}")
    print(f"   → Preparing cells with 'fileName' parameter...")

    # Prepare cells with parameters
    cells = fabric_service.prepare_notebook_cells_with_parameters(
        python_code=notebook_python_code,
        parameter_name="fileName",
        parameter_default="claims_data.csv"
    )

    print(f"   ✓ Prepared {len(cells)} cells:")
    print(f"     - Cell 1: Parameters cell (tagged)")
    print(f"     - Cell 2: Main code ({len(cells[1]['source'])} characters)")

    # Create notebook
    print(f"\n   → Uploading notebook to workspace...")
    try:
        notebook_result = await fabric_service.create_notebook(
            workspace_id=workspace_id,
            notebook_name=notebook_name,
            cells=cells
        )

        if notebook_result.get("success"):
            notebook_id = notebook_result.get("notebook_id")
            print(f"   ✓ Notebook created successfully!")
            print(f"   ✓ Notebook ID: {notebook_id}")
        else:
            print(f"\n❌ ERROR: Failed to create notebook: {notebook_result.get('error')}")
            return
    except Exception as e:
        print(f"\n❌ ERROR: Failed to create notebook: {e}")
        return

    # -------------------------------------------------------------------------
    # STEP 5: Prompt for connection IDs
    # -------------------------------------------------------------------------
    print_step(5, "Connection IDs Configuration")

    print("\n   The pipeline requires these connections:")
    print("   - Office365 Email: For sending PII/PHI detection notifications")
    print("   - SQL Connection: For querying the processedfiles table")
    print()

    # Office365 Email Connection
    email_conn_id = input("   Enter Office365 Email Connection ID (or press Enter to skip): ").strip()
    if email_conn_id:
        print(f"   ✓ Will use Office365 connection: {email_conn_id}")
    else:
        print("   ⚠️  No Office365 connection provided - email activities may fail")

    # SQL Connection
    sql_conn_id = input("   Enter SQL Connection ID (or press Enter to skip): ").strip()
    if sql_conn_id:
        print(f"   ✓ Will use SQL connection: {sql_conn_id}")
    else:
        print("   ⚠️  No SQL connection provided - Script activity may fail")

    # -------------------------------------------------------------------------
    # STEP 6: Update external references
    # -------------------------------------------------------------------------
    print_step(6, "Updating external references in pipeline...")

    external_refs = {
        "workspace_id": workspace_id,
        "notebook_id": notebook_id
    }

    if lakehouse_id:
        external_refs["lakehouse_id"] = lakehouse_id

    if email_conn_id:
        external_refs["email_connection_id"] = email_conn_id

    if sql_conn_id:
        external_refs["sql_connection_id"] = sql_conn_id

    print(f"   ✓ Will update {len(external_refs)} external reference(s):")
    for ref_name, ref_id in external_refs.items():
        print(f"     - {ref_name}: {ref_id[:30]}...")

    # -------------------------------------------------------------------------
    # STEP 7: Deploy pipeline
    # -------------------------------------------------------------------------
    print_step(7, "Deploying pipeline to Fabric...")

    print("   → Replacing RefreshDataflow with Copy Data activity...")
    print("   → Updating external references...")
    print("   → Deploying to workspace...")

    try:
        deployment_result = await fabric_service.deploy_pipeline_from_json(
            workspace_id=workspace_id,
            pipeline_json=pipeline_json,
            external_refs=external_refs,
            replace_dataflow=True  # Replace dataflow with copy activity
        )

        # -------------------------------------------------------------------------
        # STEP 8: Show results
        # -------------------------------------------------------------------------
        print_header("DEPLOYMENT RESULT")

        if deployment_result.get("success"):
            print("\n✅ DEPLOYMENT SUCCESSFUL!")
            print()
            print(f"   Pipeline ID: {deployment_result.get('pipeline_id')}")
            print(f"   Pipeline Name: {deployment_result.get('pipeline_name')}")
            print(f"   Workspace: {workspace_name}")
            print(f"   Notebook: {notebook_name} (ID: {notebook_id})")
            if lakehouse_name:
                print(f"   Lakehouse: {lakehouse_name}")
            print()
            print("   🎉 Your pipeline is ready!")
            print()
            print("   Next steps:")
            print("   1. Open Microsoft Fabric workspace")
            print(f"   2. Navigate to '{workspace_name}'")
            print(f"   3. Open the pipeline '{deployment_result.get('pipeline_name')}'")
            print("   4. Verify the activities and connections")
            print("   5. Run the pipeline to test")
            print()
        else:
            print("\n❌ DEPLOYMENT FAILED")
            print()
            print(f"   Error: {deployment_result.get('error')}")
            print()
            print("   Possible issues:")
            print("   - Connection IDs are invalid or don't exist")
            print("   - Service principal lacks permissions")
            print("   - Pipeline definition has syntax errors")
            print()
            print("   📝 The notebook was created successfully, so you can still:")
            print(f"   - View the notebook '{notebook_name}' in your workspace")
            print("   - Manually create the pipeline in Fabric UI")
            print("   - Reference the notebook in your pipeline")
            print()

        print("="*80)

    except Exception as e:
        print_header("DEPLOYMENT ERROR")
        print(f"\n❌ ERROR: {e}")
        print()
        print("   The notebook was created, but pipeline deployment failed.")
        print(f"   Notebook: {notebook_name} (ID: {notebook_id})")
        print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
