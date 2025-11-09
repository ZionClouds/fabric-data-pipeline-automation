# Dataflow Gen2 Setup Guide - Silver to Final Table

## Overview

This guide explains how to complete the setup of the Dataflow Gen2 that reads parquet files from `Files/silver/` and writes to the `final_table` lakehouse table.

## What Was Deployed Automatically

The deployment script (`deploy_dataflow_standalone.py`) created:
- ✅ Dataflow Gen2 item: "Silver_to_Final_Table"
- ✅ Power Query M code to read parquet files from Files/silver/
- ✅ Query name: "Silver Parquet Files"

## What Needs Manual Configuration (One-Time)

The data destination must be configured manually in the Fabric UI due to API limitations.

---

## Step-by-Step Setup in Fabric UI

### Step 1: Open the Dataflow

1. Go to https://app.fabric.microsoft.com
2. Navigate to workspace: **jay-dev**
3. Find and click on: **Silver_to_Final_Table** (type: Dataflow)

### Step 2: Verify the Query

You should see a query named **"Silver Parquet Files"** in the left panel.

- This query reads all `.parquet` files from the `Files/silver/` folder
- It combines them into a single table
- The schema is automatically detected from the parquet files

### Step 3: Configure Data Destination

1. In the **Silver Parquet Files** query, look at the bottom-right corner
2. Click on the **"+"** icon next to "Data destination"
3. Select **"Lakehouse"**

4. **Lakehouse Selection:**
   - Choose workspace: **jay-dev**
   - Choose lakehouse: **jay_dev_lakehouse**
   - Click **Next**

5. **Destination Settings:**
   - **Destination target**: Select **Table**
   - **Table name**: Enter `final_table`
   - **Update method**: Select **Append**
   - Click **Next**

6. **Column Mapping (Automatic):**
   - Leave as **Automatic** (recommended)
   - This will auto-map columns from source to destination
   - Click **Save settings**

### Step 4: Publish the Dataflow

1. Click **Publish** button in the top-right corner
2. Wait for publishing to complete (~30 seconds)
3. You should see a success notification

### Step 5: Test the Dataflow

1. After publishing, you'll see a **"Refresh now"** button
2. Click **"Refresh now"** to test the dataflow
3. Monitor the refresh status (it will show a spinner)
4. When complete, check the **final_table** in your lakehouse

---

## Verify the Results

### Option 1: Via Lakehouse

1. Go to **jay_dev_lakehouse**
2. Navigate to **Tables**
3. Find **final_table**
4. Click to preview the data

### Option 2: Via SQL Endpoint

```sql
SELECT * FROM final_table LIMIT 100;
```

---

## Configuration Summary

| Setting | Value |
|---------|-------|
| Dataflow Name | Silver_to_Final_Table |
| Source | Files/silver/*.parquet |
| Destination Type | Lakehouse Table |
| Table Name | final_table |
| Update Method | Append |
| Column Mapping | Automatic |

---

## Important Notes

### About Append Mode

- Each dataflow refresh **adds new rows** to the table
- Existing rows are **not removed**
- If you re-process the same parquet files, you'll get **duplicate data**
- Consider:
  - Only placing new files in Files/silver/
  - OR moving processed files to a different folder
  - OR using Replace mode instead of Append

### Schema Changes

With automatic mapping:
- New columns in parquet files will be added to the table
- Removed columns won't affect existing table columns
- Data type changes may cause errors

### Performance

- The dataflow processes all parquet files in parallel
- Larger files will take longer to process
- Monitor refresh history for performance metrics

---

## Troubleshooting

### Error: "Lakehouse not found"
- Ensure you have access to the jay-dev workspace
- Verify the lakehouse name is exactly: `jay_dev_lakehouse`

### Error: "Schema mismatch"
- Check if parquet files have consistent schema
- Review column names and data types
- Consider using Fixed schema mode

### Refresh Failed
1. Check the refresh history
2. Review error details
3. Common issues:
   - Permissions
   - Invalid parquet files
   - Memory limits

### No Data in final_table
- Verify parquet files exist in Files/silver/
- Check that files are valid parquet format
- Ensure dataflow refresh completed successfully

---

## Next Steps

Once the dataflow is configured and tested:

1. **Pipeline Integration** - Add dataflow activity to your existing pipeline
2. **Scheduling** - Set up refresh schedule if needed
3. **Monitoring** - Set up alerts for failed refreshes

See `PIPELINE_INTEGRATION_GUIDE.md` for adding this dataflow to your pipeline.

---

## API Limitations (Why Manual Setup Required)

Current Fabric API limitations:
- ❌ Lakehouse destinations require organizational account authentication
- ❌ Service principals cannot be used for destination configuration
- ❌ Destination settings not fully exposed via REST API
- ✅ However, once configured, the dataflow CAN be triggered via pipeline or API

---

## Dataflow IDs

For reference:
- **Workspace ID**: 561d497c-4709-4a69-924d-e59ad8fa6ee1
- **Lakehouse ID**: 71b91fa4-7883-44e1-aa6f-f2d6c8d564ef
- **Dataflow ID**: 5873a332-965e-43be-9932-b87371f8fdd9
