"""
STANDALONE SCRIPT - Deploy PII/PHI Solution (Hybrid Architecture)
Deploys:
1. Lakehouse (Finds 'jay_dev_lakehouse' for file reads)
2. Warehouse (Assumes 'jay-dev-warehouse' and table 'processedfiles' already exist)
3. Notebook (Creates, uploads definition, attaches lakehouse, writes to warehouse)
4. Pipeline (Creates a SIMPLIFIED pipeline due to API limitations)

- Get Metadata reads from Lakehouse.
- Notebook write/read from Warehouse.
- Pipeline Filtering logic (Script Activity) is REMOVED because
  its Connection ('externalReferences') cannot be set via API.
"""
import asyncio
import httpx
import json
import base64
from typing import Optional, Dict, Any

# ============================================================================
# CONFIGURATION
# ============================================================================
# --- Service Principal Credentials ---
TENANT_ID = "e28d23e3-803d-418d-a720-c0bed39f77b6"
CLIENT_ID = "0944e22d-d0f1-40c1-a9fc-f422c05949f3"
CLIENT_SECRET = "oRF8Q~g03M~RuIJ3Tf.eKTS-W8kVvFQXCbIr-ac7"

# --- Fabric Item Names ---
WORKSPACE_NAME = "jay-dev"
LAKEHOUSE_NAME = "jay_dev_lakehouse"
WAREHOUSE_NAME = "jay-dev-warehouse" # Assumed to exist
TABLE_NAME = "processedfiles"       # Assumed to exist in Warehouse
NOTEBOOK_NAME = "PHI_PII_detection"
PIPELINE_NAME = "PII_PHI_Pipeline"

# --- Fabric API ---
FABRIC_BASE_URL = "https://api.fabric.microsoft.com/v1"
FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"
# ============================================================================


# ============================================================================
# NOTEBOOK & PIPELINE DEFINITIONS
# ============================================================================

# --- Source code for the Notebook (MODIFIED) ---
# This code now writes to the WAREHOUSE table
NOTEBOOK_PYTHON_SOURCE = r"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, when, concat_ws, abs as spark_abs,
    current_timestamp, to_date, regexp_replace, trim, coalesce, sha2, concat
)
from pyspark.sql.types import DoubleType
from datetime import datetime
from notebookutils import mssparkutils
import json
# -------------------------------
# Configuration
# -------------------------------
# fileName="claims_data.csv"

# -------------------------------
# Pipeline configuration
# -------------------------------
# fileName is passed from the pipeline
fileName = mssparkutils.widgets.get("fileName")

# --- Read from Lakehouse Files ---
SOURCE_CLAIM_FILE_PATH = "Files/bronze/{filename}"
SOURCE_PRIOR_AUTH_FILE_PATH = "Files/priorauths/prior_authorization_data.csv"
OUTPUT_PATH = "Files/silver" # Writes parquet to Lakehouse Files/silver

# --- Write to Warehouse Table ---
WAREHOUSE_DB_NAME = "jay-dev-warehouse"
PROCESSED_FILES_TABLE = "processedfiles"
FULL_WAREHOUSE_TABLE_NAME = f"{WAREHOUSE_DB_NAME}.dbo.{PROCESSED_FILES_TABLE}"

spark = SparkSession.builder.appName("Claims Prior Auth Matching - Parameterized").getOrCreate()
FULL_CLAIM_PATH = SOURCE_CLAIM_FILE_PATH.format(filename=fileName)
RUN_ID = f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"  # Unique run ID

# -------------------------------
# Helpers
# -------------------------------
def clean_numeric_column(df, column_name):
    if column_name in df.columns:
        return df.withColumn(column_name, regexp_replace(col(column_name), ",", "").cast(DoubleType()))
    return df

# -------------------------------
# MAIN
# -------------------------------
notebook_output = {
    "status": "UNKNOWN",
    "execution_timestamp": datetime.now().isoformat(),
    "file_processed": fileName,
    "PII_PHI": False,
    "processing_summary": {},
    "error": None
}

try:
    try:
        mssparkutils.fs.mkdirs(OUTPUT_PATH)
        print(f"Output dir ready: {OUTPUT_PATH}")
    except:
        pass

    print("="*100)
    print(f"STEP 1: READ CLAIMS FILE: {fileName}")
    print("="*100)

    claims_df = (
        spark.read.option("header", "true").option("inferSchema", "false").csv(FULL_CLAIM_PATH)
        .withColumn("source_file", lit(fileName))
    )
    claims_df = clean_numeric_column(claims_df, "Dollars")
    claims_df = clean_numeric_column(claims_df, "Units")
    for c in ["DCN", "RecipientID", "CatgOfServiceCd", "ProcCd", "ProviderID", "ProviderName"]:
        if c in claims_df.columns:
            claims_df = claims_df.withColumn(c, trim(col(c)))
    print(f"Claims rows: {claims_df.count()}")

    print("="*100)
    print(f"STEP 2: READ PRIOR AUTH FILE: {SOURCE_PRIOR_AUTH_FILE_PATH}")
    print("="*100)

    prior_auth_df = (
        spark.read.option("header", "true").option("inferSchema", "false").csv(SOURCE_PRIOR_AUTH_FILE_PATH)
    )
    prior_auth_df = clean_numeric_column(prior_auth_df, "AuthorizedAmt")
    prior_auth_df = clean_numeric_column(prior_auth_df, "AuthorizedRateAmt")
    prior_auth_df = clean_numeric_column(prior_auth_df, "AuthorizationQuan")
    for c in ["RecipientID", "CatgOfServiceCd", "PriorApprovalServiceNbr", "ServiceProviderID", "Name"]:
        if c in prior_auth_df.columns:
            prior_auth_df = prior_auth_df.withColumn(c, trim(col(c)))
    print(f"Prior auth rows: {prior_auth_df.count()}")

    print("="*100)
    print("STEP 3: MATCHING")
    print("="*100)

    claims_df = claims_df.withColumn(
        "ServiceFromDt_Date",
        coalesce(
            to_date(col("ServiceFromDt"), "M/d/yy"),
            to_date(col("ServiceFromDt"), "MM/dd/yy"),
            to_date(col("ServiceFromDt"), "M/dd/yy"),
            to_date(col("ServiceFromDt"), "MM/d/yy")
        )
    )

    prior_auth_df = prior_auth_df.withColumn(
        "BeginDt_Date",
        coalesce(
            to_date(col("BeginDt"), "M/d/yy"),
            to_date(col("BeginDt"), "MM/dd/yy"),
            to_date(col("BeginDt"), "M/dd/yy"),
            to_date(col("BeginDt"), "MM/d/yy")
        )
    ).withColumn(
        "EndDt_Date",
        coalesce(
            to_date(col("EndDt"), "M/d/yy"),
            to_date(col("EndDt"), "MM/dd/yy"),
            to_date(col("EndDt"), "M/dd/yy"),
            to_date(col("EndDt"), "MM/d/yy")
        )
    )

    claims_df = claims_df.withColumn(
        "Claim_Rate_Per_Unit",
        when((col("Units").isNotNull()) & (col("Units") > 0), col("Dollars")/col("Units")).otherwise(0)
    )

    joined_df = claims_df.alias("c").join(
        prior_auth_df.alias("a"),
        (col("c.RecipientID") == col("a.RecipientID")) &
        (col("c.CatgOfServiceCd") == col("a.CatgOfServiceCd")) &
        (col("c.ProcCd") == col("a.PriorApprovalServiceNbr")),
        "left"
    )

    joined_df = joined_df.withColumn("Patient_Match", col("a.RecipientID").isNotNull()) \
        .withColumn("Provider_Match", when(col("Patient_Match"), col("c.ProviderID") == col("a.ServiceProviderID")).otherwise(False)) \
        .withColumn("ServiceType_Match", col("a.CatgOfServiceCd").isNotNull()) \
        .withColumn("Procedure_Match", col("a.PriorApprovalServiceNbr").isNotNull()) \
        .withColumn(
            "DateWithinPeriod",
            when(
                col("Patient_Match") &
                col("c.ServiceFromDt_Date").isNotNull() &
                col("a.BeginDt_Date").isNotNull() &
                col("a.EndDt_Date").isNotNull(),
                (col("c.ServiceFromDt_Date") >= col("a.BeginDt_Date")) &
                (col("c.ServiceFromDt_Date") <= col("a.EndDt_Date"))
            ).otherwise(False)
        ) \
        .withColumn(
            "Rate_Match",
            when(
                col("Patient_Match") &
                col("c.Claim_Rate_Per_Unit").isNotNull() &
                col("a.AuthorizedRateAmt").isNotNull(),
                spark_abs(col("c.Claim_Rate_Per_Unit") - col("a.AuthorizedRateAmt")) < 0.01
            ).otherwise(False)
        ) \
        .withColumn(
            "Units_Available",
            when(
                col("Patient_Match") &
                col("c.Units").isNotNull() &
                col("a.AuthorizationQuan").isNotNull(),
                col("c.Units") <= col("a.AuthorizationQuan")
            ).otherwise(False)
        ) \
        .withColumn(
            "Overall_Match",
            col("Patient_Match") & col("Provider_Match") & col("ServiceType_Match") &
            col("Procedure_Match") & col("DateWithinPeriod") & col("Rate_Match") & col("Units_Available")
        ) \
        .withColumn(
            "Issue_Category",
            when(~col("Patient_Match"), "NO_AUTHORIZATION")
            .when(~col("Provider_Match"), "PROVIDER_MISMATCH")
            .when(~col("DateWithinPeriod"), "DATE_MISMATCH")
            .when(~col("Rate_Match"), "RATE_MISMATCH")
            .when(~col("Units_Available"), "UNITS_EXCEEDED")
            .when(col("Overall_Match"), "FULLY_MATCHED")
            .otherwise("MULTIPLE_ISSUES")
        ) \
        .withColumn(
            "Match_Issues",
            when(~col("Patient_Match"), "No authorization found for this patient/service/procedure combination")
            .when(col("Overall_Match"), "All criteria match")
            .otherwise(
                concat_ws("; ",
                    when(~col("Provider_Match"),
                         concat_ws("", lit("Provider mismatch: Auth="), col("a.ServiceProviderID"),
                                   lit(", Claim="), col("c.ProviderID"))).otherwise(lit("")),
                    when(~col("DateWithinPeriod"),
                         concat_ws("", lit("Date outside period: Service="), col("c.ServiceFromDt"),
                                   lit(", Auth Period="), col("a.BeginDt"), lit(" to "), col("a.EndDt"))
                         ).otherwise(lit("")),
                    when(~col("Rate_Match"),
                         concat_ws("", lit("Rate mismatch: Claim rate=$"), col("c.Claim_Rate_Per_Unit"),
                                   lit(", Auth rate=$"), col("a.AuthorizedRateAmt"))).otherwise(lit("")),
                    when(~col("Units_Available"),
                         concat_ws("", lit("Units exceed authorization: Claimed="), col("c.Units"),
                                   lit(", Authorized="), col("a.AuthorizationQuan"))).otherwise(lit(""))
                )
            )
        )

    print("="*100)
    print("STEP 4: BUILD OUTPUT + PRIVACY PROTECTION (NO HARDCODED COLUMNS)")
    print("="*100)

    output_df = joined_df.select(
        col("c.DCN").alias("DCN"),
        col("c.ServiceLineNbr").alias("ServiceLineNbr"),
        col("c.ServiceFromDt").alias("ServiceFromDt"),
        col("c.RecipientID").alias("RecipientID"),
        col("c.CatgOfServiceCd").alias("CatgOfServiceCd"),
        col("c.ProcCd").alias("ProcCd"),
        col("c.MCESubmitterCd").alias("MCESubmitterCd"),
        col("c.Dollars").alias("Claim_Dollars"),
        col("c.Units").alias("Claim_Units"),
        col("c.ProviderTypeCd").alias("ProviderTypeCd"),
        col("c.ProviderNbr").alias("ProviderNbr"),
        col("c.ProviderID").alias("ProviderID"),
        col("c.ProviderName").alias("Claim_ProviderName"),
        col("a.ReferenceNbr").alias("Auth_ReferenceNbr"),
        col("a.BeginDt").alias("Auth_BeginDt"),
        col("a.EndDt").alias("Auth_EndDt"),
        col("a.AuthorizedRateAmt").alias("Auth_Rate"),
        col("a.AuthorizationQuan").alias("Auth_Quantity"),
        col("a.AuthorizedAmt").alias("Auth_TotalAmount"),
        col("a.ServiceProviderID").alias("Auth_ProviderID"),
        col("a.Name").alias("Auth_ProviderName"),
        col("Overall_Match"),
        col("Issue_Category"),
        col("Match_Issues"),
        current_timestamp().alias("loaded_timestamp")
    )

    # <<< Detect PII/PHI before applying protection >>>
    print("Checking for PII/PHI in data...")

    # Define sensitive columns that contain PII/PHI
    pii_phi_columns = {
        "patient_identifiers": ["RecipientID"],
        "provider_identifiers": ["ProviderID", "Auth_ProviderID", "ProviderNbr"],
        "document_identifiers": ["DCN", "Auth_ReferenceNbr"],
        "provider_names": ["Claim_ProviderName", "Auth_ProviderName"]
    }

    # Check if any PII/PHI exists in the data
    pii_phi_detected = False
    pii_phi_details = {}

    for category, columns in pii_phi_columns.items():
        for col_name in columns:
            if col_name in output_df.columns:
                # Count non-null values in this sensitive column
                non_null_count = output_df.filter(col(col_name).isNotNull()).count()
                if non_null_count > 0:
                    pii_phi_detected = True
                    pii_phi_details[col_name] = {
                        "category": category,
                        "records_with_data": non_null_count
                    }

    if pii_phi_detected:
        print(f"WARNING: PII/PHI DETECTED in {len(pii_phi_details)} column(s)")
        for col_name, info in pii_phi_details.items():
            print(f"   - {col_name}: {info['records_with_data']} records ({info['category']})")
    else:
        print("No PII/PHI detected in data")

    # <<< Apply Spark-native privacy protection >>>
    print("Applying privacy protection...")

    # Define columns to protect based on sensitivity
    # IDs: Hash deterministically (preserves joins/grouping)
    id_columns = ["DCN", "RecipientID", "ProviderID", "Auth_ProviderID", "ProviderNbr", "Auth_ReferenceNbr"]
    # Names: Replace with generic placeholder
    name_columns = ["Claim_ProviderName", "Auth_ProviderName"]

    # Apply hashing to ID columns
    for col_name in id_columns:
        if col_name in output_df.columns:
            output_df = output_df.withColumn(
                col_name,
                when(col(col_name).isNotNull(), sha2(concat(lit("SALT_"), col(col_name)), 256))
                .otherwise(None)
            )

    # Apply masking to name columns
    for col_name in name_columns:
        if col_name in output_df.columns:
            output_df = output_df.withColumn(
                col_name,
                when(col(col_name).isNotNull(), lit("<PROVIDER_NAME>"))
                .otherwise(None)
            )

    print("Privacy protection applied (IDs hashed, names masked)")

    total_records = output_df.count()
    matched_count = output_df.filter(col("Overall_Match") == True).count()
    unmatched_count = total_records - matched_count

    print("="*100)
    print("STEP 5: WRITE PARQUET (APPEND)")
    print("="*100)

    output_df.write.mode("append").parquet(OUTPUT_PATH)
    print(f"Appended {total_records} records from {fileName} to {OUTPUT_PATH}")

    final_df = spark.read.parquet(f"{OUTPUT_PATH}/*.parquet")
    total_cumulative = final_df.count()

    print("="*100)
    print(f"STEP 6: UPDATE PROCESSED FILES TABLE IN WAREHOUSE: {FULL_WAREHOUSE_TABLE_NAME}")
    print("="*100)

    # Only update table if processing was successful
    try:
        # Create record for this processed file
        processed_record = spark.createDataFrame([{
            "FilePath": FULL_CLAIM_PATH,
            "FileName": fileName,
            "LastModified": datetime.now(),
            "Status": "Done",
            "ProcessedOn": datetime.now(),
            "RunId": RUN_ID
        }])

        # --- MODIFICATION ---
        # Append to warehouse table (or create if doesn't exist)
        processed_record.write.mode("append").saveAsTable(FULL_WAREHOUSE_TABLE_NAME)
        print(f"Updated {FULL_WAREHOUSE_TABLE_NAME}: {fileName} -> Done")
    except Exception as e:
        print(f"WARNING: Could not update {FULL_WAREHOUSE_TABLE_NAME}: {e}")

    notebook_output["status"] = "SUCCESS"
    notebook_output["PII_PHI"] = pii_phi_detected
    notebook_output["processing_summary"] = {
        "file_processed": fileName,
        "records_written": total_records,
        "matched_in_file": matched_count,
        "unmatched_in_file": unmatched_count,
        "cumulative_total_records": total_cumulative,
        "output_path": OUTPUT_PATH,
        "pii_phi_detected": pii_phi_detected,
        "pii_phi_details": pii_phi_details
    }

    print("PROCESSING COMPLETE")

except Exception as e:
    notebook_output["status"] = "ERROR"
    notebook_output["error"] = {"message": str(e), "type": type(e).__name__}
    import traceback; traceback.print_exc()

# Return the JSON output for the pipeline
mssparkutils.notebook.exit(json.dumps(notebook_output))
"""

# --- Source JSON for the Pipeline (as a template) ---
# This is the original, full pipeline JSON
PIPELINE_TEMPLATE_JSON = r"""
{
    "name": "PII_PHI_Pipeline",
    "properties": {
        "activities": [
            {
                "name": "Get Metadata",
                "type": "GetMetadata",
                "dependsOn": [],
                "policy": {
                    "timeout": "0.12:00:00",
                    "retry": 0,
                    "retryIntervalInSeconds": 30,
                    "secureOutput": false,
                    "secureInput": false
                },
                "typeProperties": {
                    "fieldList": [
                        "childItems"
                    ],
                    "datasetSettings": {
                        "annotations": [],
                        "connectionSettings": {
                            "name": "PII_PHI_lakehouse",
                            "properties": {
                                "annotations": [],
                                "type": "Lakehouse",
                                "typeProperties": {
                                    "workspaceId": "91ff9e14-fec6-4d76-ba4e-ba401c7a3f70",
                                    "artifactId": "ac63e579-02e7-4989-b6dc-7b0cbd5eefef",
                                    "rootFolder": "Files"
                                },
                                "externalReferences": {
                                    "connection": "f77bbbd6-2cd0-475b-89b2-eb86f449c7c9"
                                }
                            }
                        },
                        "type": "DelimitedText",
                        "typeProperties": {
                            "location": {
                                "type": "LakehouseLocation",
                                "folderPath": "claims"
                            },
                            "columnDelimiter": ",",
                            "escapeChar": "\\",
                            "firstRowAsHeader": true,
                            "quoteChar": "\""
                        },
                        "schema": []
                    },
                    "storeSettings": {
                        "type": "LakehouseReadSettings",
                        "recursive": true,
                        "enablePartitionDiscovery": false
                    },
                    "formatSettings": {
                        "type": "DelimitedTextReadSettings"
                    }
                }
            },
            {
                "name": "forEach",
                "type": "ForEach",
                "dependsOn": [
                    {
                        "activity": "FilterNewFiles",
                        "dependencyConditions": [
                            "Succeeded"
                        ]
                    }
                ],
                "typeProperties": {
                    "items": {
                        "value": "@activity('FilterNewFiles').output.value",
                        "type": "Expression"
                    },
                    "activities": [
                        {
                            "name": "PHI_PII_detection",
                            "type": "TridentNotebook",
                            "dependsOn": [],
                            "policy": {
                                "timeout": "0.12:00:00",
                                "retry": 0,
                                "retryIntervalInSeconds": 30,
                                "secureOutput": false,
                                "secureInput": false
                            },
                            "typeProperties": {
                                "notebookId": "adf61e58-6f63-4a99-97bf-3f9c4990ca8b",
                                "workspaceId": "91ff9e14-fec6-4d76-ba4e-ba401c7a3f70",
                                "parameters": {
                                    "fileName": {
                                        "value": {
                                            "value": "@item().name",
                                            "type": "Expression"
                                        },
                                        "type": "string"
                                    }
                                }
                            }
                        },
                        {
                            "name": "If Condition1",
                            "type": "IfCondition",
                            "dependsOn": [
                                {
                                    "activity": "PHI_PII_detection",
                                    "dependencyConditions": [
                                        "Succeeded"
                                    ]
                                }
                            ],
                            "typeProperties": {
                                "expression": {
                                    "value": "@bool(\n  json(activity('PHI_PII_detection').output.result.exitValue).PII_PHI\n)\n",
                                    "type": "Expression"
                                },
                                "ifFalseActivities": [
                                    {
                                        "name": "PII_PHI_notification1",
                                        "type": "Office365Email",
                                        "dependsOn": [],
                                        "policy": {
                                            "timeout": "0.12:00:00",
                                            "retry": 0,
                                            "retryIntervalInSeconds": 30,
                                            "secureOutput": false,
                                            "secureInput": false
                                        },
                                        "typeProperties": {
                                            "to": "jay.reddy@zionclouds.com",
                                            "subject": "PHI/PII not detection",
                                            "body": "<p>Hi Jay,</p>\n<p>PHI/PII not detected</p>"
                                        },
                                        "externalReferences": {
                                            "connection": "eedc7b74-01d7-4524-bf31-98ecead7fc5f"
                                        }
                                    }
                                ],
                                "ifTrueActivities": [
                                    {
                                        "name": "PII_PHI_notification",
                                        "type": "Office365Email",
                                        "dependsOn": [],
                                        "policy": {
                                            "timeout": "0.12:00:00",
                                            "retry": 0,
                                            "retryIntervalInSeconds": 30,
                                            "secureOutput": false,
                                            "secureInput": false
                                        },
                                        "typeProperties": {
                                            "to": "jay.reddy@zionclouds.com",
                                            "subject": "PHI/PII detected",
                                            "body": "<p>Hi Jay,</p>\n<p>PII/PHI detected</p>\n<p>@{item()}</p>"
                                        },
                                        "externalReferences": {
                                            "connection": "eedc7b74-01d7-4524-bf31-98ecead7fc5f"
                                        }
                                    }
                                ]
                            }
                        },
                        {
                            "name": "curated Data",
                            "type": "RefreshDataflow",
                            "dependsOn": [
                                {
                                    "activity": "If Condition1",
                                    "dependencyConditions": [
                                        "Succeeded"
                                    ]
                                }
                            ],
                            "policy": {
                                "timeout": "0.12:00:00",
                                "retry": 0,
                                "retryIntervalInSeconds": 30,
                                "secureOutput": false,
                                "secureInput": false
                            },
                            "typeProperties": {
                                "dataflowId": "2c7b952e-3ba0-45b3-b668-586b6bf5e14f",
                                "workspaceId": "91ff9e14-fec6-4d76-ba4e-ba401c7a3f70",
                                "notifyOption": "NoNotification",
                                "dataflowType": "DataflowFabric"
                            }
                        }
                    ]
                }
            },
            {
                "name": "SetEmptyFileArray",
                "type": "SetVariable",
                "dependsOn": [
                    {
                        "activity": "GetProcessedFileNames",
                        "dependencyConditions": [
                            "Succeeded"
                        ]
                    }
                ],
                "policy": {
                    "secureOutput": false,
                    "secureInput": false
                },
                "typeProperties": {
                    "variableName": "ProcessedFileNames",
                    "value": {
                        "value": "[]",
                        "type": "Expression"
                    }
                }
            },
            {
                "name": "FilterNewFiles",
                "type": "Filter",
                "dependsOn": [
                    {
                        "activity": "ForEach1",
                        "dependencyConditions": [
                            "Succeeded"
                        ]
                    }
                ],
                "typeProperties": {
                    "items": {
                        "value": "@activity('Get Metadata').output.childItems",
                        "type": "Expression"
                    },
                    "condition": {
                        "value": "@not(contains(variables('ProcessedFileNames'), item().name))",
                        "type": "Expression"
                    }
                }
            },
            {
                "name": "ForEach1",
                "type": "ForEach",
                "dependsOn": [
                    {
                        "activity": "SetEmptyFileArray",
                        "dependencyConditions": [
                            "Succeeded"
                        ]
                    }
                ],
                "typeProperties": {
                    "items": {
                        "value": "@activity('GetProcessedFileNames').output.resultSets[0].rows",
                        "type": "Expression"
                    },
                    "activities": [
                        {
                            "name": "Set variable1",
                            "type": "SetVariable",
                            "dependsOn": [],
                            "policy": {
                                "secureOutput": false,
                                "secureInput": false
                            },
                            "typeProperties": {
                                "variableName": "ProcessedFileNames",
                                "value": {
                                    "value": "@item().FileName",
                                    "type": "Expression"
                                }
                            }
                        }
                    ]
                }
            },
            {
                "name": "GetProcessedFileNames",
                "type": "Script",
                "dependsOn": [
                    {
                        "activity": "Get Metadata",
                        "dependencyConditions": [
                            "Succeeded"
                        ]
                    }
                ],
                "policy": {
                    "timeout": "0.12:00:00",
                    "retry": 0,
                    "retryIntervalInSeconds": 30,
                    "secureOutput": false,
                    "secureInput": false
                },
                "typeProperties": {
                    "scripts": [
                        {
                            "type": "Query",
                            "text": {
                                "value": "SELECT [FileName] FROM [PII_PHI_lakehouse].[dbo].[processedfiles] WHERE Status = 'Done'",
                                "type": "Expression"
                            }
                        }
                    ],
                    "scriptBlockExecutionTimeout": "02:00:00",
                    "database": "claimsauth"
                },
                "externalReferences": {
                    "connection": "fd7dd7e4-4330-43af-ae8a-d15f9318b440"
                }
            }
        ],
        "variables": {
            "v_fileName": {
                "type": "String"
            },
            "ProcessedFileNames": {
                "type": "String"
            },
            "SetEmptyFileArray": {
                "type": "String"
            },
            "v_ProcessedFileNames": {
                "type": "String"
            }
        }
    }
}
"""
# ============================================================================


# ============================================================================
# API HELPER FUNCTIONS
# ============================================================================
async def get_access_token() -> str:
    """Get Azure AD access token for Fabric API"""
    try:
        import msal
    except ImportError:
        print("Error: 'msal' package not found. Please install it using: pip install msal")
        raise

    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        client_credential=CLIENT_SECRET
    )
    result = app.acquire_token_for_client(scopes=[FABRIC_SCOPE])
    if "access_token" not in result:
        raise RuntimeError(f"Authentication failed: {result.get('error_description', result)}")
    return result["access_token"]


async def poll_operation_status(token: str, operation_id: str, max_attempts: int = 30):
    """Poll operation status until completion"""
    url = f"{FABRIC_BASE_URL}/operations/{operation_id}"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(max_attempts):
            await asyncio.sleep(2)

            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                operation_data = response.json()
                status = operation_data.get("status")

                if status == "Succeeded":
                    print(f"      ✓ Operation completed successfully")
                    return operation_data
                elif status == "Failed":
                    error = operation_data.get("error", {})
                    raise RuntimeError(f"Operation failed: {error}")
                elif status in ["Running", "NotStarted"]:
                    # Still processing, continue polling
                    continue
                else:
                    print(f"      Unknown status: {status}")
                    continue
            elif response.status_code == 202:
                # Still processing
                continue
            else:
                print(f"      Unexpected status code: {response.status_code}")
                continue

        raise RuntimeError(f"Operation polling timeout after {max_attempts} attempts")


async def find_workspace(token: str, workspace_name: str) -> Optional[dict]:
    """Find workspace by name"""
    url = f"{FABRIC_BASE_URL}/workspaces"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        workspaces = response.json().get("value", [])
        for ws in workspaces:
            if ws.get("displayName") == workspace_name:
                return ws
    return None


async def find_item_in_workspace(token: str, workspace_id: str, item_type: str, item_name: str) -> Optional[dict]:
    """Find an item (Lakehouse, Notebook, etc.) by name and type"""
    url = f"{FABRIC_BASE_URL}/workspaces/{workspace_id}/items"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"type": item_type}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        items = response.json().get("value", [])
        for item in items:
            if item.get("displayName") == item_name:
                return item
    return None


async def create_fabric_item(token: str, workspace_id: str, item_type: str, item_name: str, lakehouse_id: str = None) -> dict:
    """
    Create a new, empty Fabric item.
    """
    url = f"{FABRIC_BASE_URL}/workspaces/{workspace_id}/items"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    payload = {
        "displayName": item_name,
        "type": item_type
    }
    
    # --- FIX: REMOVED logic from here ---
    # We create a simple item, THEN attach/update.

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 409: # Conflict, item already exists
            print(f"   ! Item '{item_name}' already exists (Conflict 409). Finding it...")
            return await find_item_in_workspace(token, workspace_id, item_type, item_name)
        response.raise_for_status()
        return response.json()


async def get_or_create_item(token: str, workspace_id: str, item_type: str, item_name: str, lakehouse_id: str = None) -> dict:
    """Find an item, or create it if it doesn't exist."""
    print(f"   - Checking for {item_type} '{item_name}'...")
    item = await find_item_in_workspace(token, workspace_id, item_type, item_name)
    if item:
        print(f"   ✓ Found {item_type}: {item.get('id')}")
        # --- We will attach lakehouse during the definition update ---
        return item
    
    print(f"   ! {item_type} not found. Creating '{item_name}'...")
    # --- MODIFICATION ---
    # 1. Create a SIMPLE item first (no lakehouse_id passed)
    item = await create_fabric_item(token, workspace_id, item_type, item_name)
    print(f"   ✓ Created {item_type}: {item.get('id')}")

    # --- We will attach lakehouse during the definition update ---
    return item

# --- REMOVED 'update_notebook_lakehouse_attachment' function ---
# This logic is now handled by get_notebook_ipynb_content


async def update_item_definition(token: str, workspace_id: str, item_id: str, payload_str: str):
    """Upload a definition (Notebook, Pipeline) to a Fabric item"""

    payload_bytes = payload_str.encode("utf-8")
    encoded_payload = base64.b64encode(payload_bytes).decode("ascii")

    # Determine the correct path based on content type
    # Fabric Python notebooks use .py, pipelines use .json
    if payload_str.startswith("# Fabric notebook source"):
        content_path = "notebook-content.py"
    else:
        content_path = "pipeline-content.json"

    update_payload = {
        "definition": {
            "parts": [
                {
                    "path": content_path,
                    "payload": encoded_payload,
                    "payloadType": "InlineBase64"
                }
            ]
        }
    }

    url = f"{FABRIC_BASE_URL}/workspaces/{workspace_id}/items/{item_id}/updateDefinition"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, data=json.dumps(update_payload))
        if response.status_code not in [200, 202]:
            print(f"   ❌ Update failed with status {response.status_code}")
            print(f"   Response: {response.text}")
        response.raise_for_status()

        # Poll operation if async
        operation_id = response.headers.get("x-ms-operation-id")
        if operation_id and response.status_code == 202:
            print(f"   Operation ID: {operation_id}")
            print(f"   Waiting for operation to complete...")
            await poll_operation_status(token, operation_id)

        print(f"   ✓ Definition updated for item {item_id}")


# --- MODIFIED 'get_notebook_ipynb_content' ---
def get_notebook_ipynb_content(python_source: str, lakehouse_id: str) -> str:
    """
    Converts raw Python script into Fabric Python notebook format.
    This format includes the required prologue and lakehouse metadata.
    """

    # Create Fabric Python notebook format with proper prologue
    fabric_py_content = f"""# Fabric notebook source

# METADATA ********************

# META {{
# META   "dependencies": {{
# META     "lakehouse": {{
# META       "default_lakehouse": "{lakehouse_id}",
# META       "default_lakehouse_name": "",
# META       "default_lakehouse_workspace_id": ""
# META     }}
# META   }}
# META }}

# CELL ********************

{python_source}
"""

    return fabric_py_content


async def get_warehouse_sql_endpoint(token: str, workspace_id: str, warehouse_id: str) -> str:
    """Get warehouse SQL endpoint from properties"""
    url = f"{FABRIC_BASE_URL}/workspaces/{workspace_id}/warehouses/{warehouse_id}"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()

        warehouse_props = response.json()
        sql_endpoint = warehouse_props.get("properties", {}).get("connectionString")

        if not sql_endpoint:
            raise RuntimeError(f"Could not find SQL endpoint for warehouse {warehouse_id}")

        return sql_endpoint


async def create_or_get_warehouse_connection(
    token: str,
    connection_name: str,
    sql_endpoint: str,
    database_name: str
) -> Dict[str, Any]:
    """Create or get existing SQL connection to warehouse"""

    # First, check if connection already exists
    list_url = f"{FABRIC_BASE_URL}/connections"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # List existing connections
        list_response = await client.get(list_url, headers=headers)
        list_response.raise_for_status()

        connections = list_response.json().get("value", [])
        for conn in connections:
            if conn.get("displayName") == connection_name:
                print(f"   ✓ Found existing connection: {conn.get('id')}")
                return conn

        # Connection doesn't exist, create it
        print(f"   ! Connection '{connection_name}' not found. Creating...")

        payload = {
            "connectivityType": "ShareableCloud",
            "displayName": connection_name,
            "connectionDetails": {
                "type": "SQL",  # Must be uppercase!
                "creationMethod": "Sql",
                "parameters": [
                    {
                        "dataType": "Text",
                        "name": "server",
                        "value": sql_endpoint
                    },
                    {
                        "dataType": "Text",
                        "name": "database",
                        "value": database_name
                    }
                ]
            },
            "privacyLevel": "Organizational",
            "credentialDetails": {
                "singleSignOnType": "None",
                "connectionEncryption": "NotEncrypted",
                "skipTestConnection": False,
                "credentials": {
                    "credentialType": "ServicePrincipal",
                    "servicePrincipalClientId": CLIENT_ID,
                    "servicePrincipalSecret": CLIENT_SECRET,
                    "tenantId": TENANT_ID
                }
            }
        }

        create_response = await client.post(list_url, headers=headers, data=json.dumps(payload))

        if create_response.status_code not in [200, 201]:
            print(f"   ❌ Connection creation failed: {create_response.text}")
            create_response.raise_for_status()

        connection = create_response.json()
        print(f"   ✓ Created connection: {connection.get('id')}")
        return connection


def remove_external_references(obj):
    """Recursively remove all 'externalReferences' from a JSON object"""
    if isinstance(obj, dict):
        if "externalReferences" in obj:
            del obj["externalReferences"]
        for value in obj.values():
            remove_external_references(value)
    elif isinstance(obj, list):
        for item in obj:
            remove_external_references(item)


# --- MODIFIED 'modify_pipeline_definition' ---
def modify_pipeline_definition(
    template_str: str,
    new_workspace_id: str,
    new_lakehouse_id: str,
    new_notebook_id: str,
    warehouse_connection_id: str
) -> str:
    """
    Modifies the pipeline JSON to use all new, automated items.
    FIXED: Includes required storeSettings for Get Metadata to prevent UI errors.
    """
    print("   - Modifying pipeline template...")

    # Load into Python dict for structural changes
    data = json.loads(template_str)

    # --- HELPER: Recursive ID replacement ---
    # We do this on the loaded dict to avoid breaking generic strings
    def replace_ids(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    # Replace known placeholder IDs
                    if "91ff9e14-fec6-4d76-ba4e-ba401c7a3f70" in value:
                         obj[key] = value.replace("91ff9e14-fec6-4d76-ba4e-ba401c7a3f70", new_workspace_id)
                    if "ac63e579-02e7-4989-b6dc-7b0cbd5eefef" in value:
                         obj[key] = value.replace("ac63e579-02e7-4989-b6dc-7b0cbd5eefef", new_lakehouse_id)
                    if "adf61e58-6f63-4a99-97bf-3f9c4990ca8b" in value:
                         obj[key] = value.replace("adf61e58-6f63-4a99-97bf-3f9c4990ca8b", new_notebook_id)
                else:
                    replace_ids(value)
        elif isinstance(obj, list):
            for item in obj:
                replace_ids(item)

    # Initial pass to update all standard IDs in the template
    replace_ids(data)

    # --- 1. CLEANUP: Remove ONLY Email and old Dataflow activities ---
    print("   - Removing Email and old Dataflow activities...")
    activities_to_remove = [
        "PII_PHI_notification1",
        "PII_PHI_notification",
        "curated Data",
        "If Condition1"
    ]

    # Filter main activities list
    data["properties"]["activities"] = [
        act for act in data["properties"]["activities"]
        if act["name"] not in activities_to_remove
    ]

    # Filter activities inside the 'forEach' loop
    foreach_activity = next(act for act in data["properties"]["activities"] if act["name"] == "forEach")
    foreach_activity["typeProperties"]["activities"] = [
        act for act in foreach_activity["typeProperties"]["activities"]
        if act["name"] not in activities_to_remove
    ]

    # --- 2. UPDATE: Get Metadata Activity (CRITICAL FIX) ---
    print(f"   - Rebuilding 'Get Metadata' activity with correct settings")
    get_metadata_activity = next(act for act in data["properties"]["activities"] if act["name"] == "Get Metadata")
    
    # Completely replace typeProperties to ensure valid structure
    get_metadata_activity["typeProperties"] = {
        "fieldList": ["childItems"],
        "storeSettings": {
            "type": "LakehouseReadSettings",
            "recursive": True,
            "enablePartitionDiscovery": False
        },
        "datasetSettings": {
            "type": "Binary",
            "linkedService": {
                "name": LAKEHOUSE_NAME,
                "properties": {
                    "type": "Lakehouse",
                    "typeProperties": {
                        "workspaceId": new_workspace_id,
                        "artifactId": new_lakehouse_id,
                        "rootFolder": "Files"
                    }
                }
            },
            "typeProperties": {
                "location": {
                    "type": "LakehouseLocation",
                    "folderPath": "bronze"
                }
            }
        }
    }

    # --- 3. UPDATE: Script Activity (Warehouse Connection) ---
    print(f"   - Updating 'GetProcessedFileNames' Script activity with warehouse connection")
    script_activity = next(act for act in data["properties"]["activities"] if act["name"] == "GetProcessedFileNames")
    # Update SQL Query and Database
    script_activity["typeProperties"]["scripts"][0]["text"]["value"] = f"SELECT [FileName] FROM [dbo].[{TABLE_NAME}] WHERE Status = 'Done'"
    script_activity["typeProperties"]["database"] = WAREHOUSE_NAME
    # Add Warehouse Connection Reference
    script_activity["externalReferences"] = {
        "connection": warehouse_connection_id
    }

    print("   ✓ Pipeline modification complete!")
    return json.dumps(data)

# ============================================================================
# MAIN DEPLOYMENT FLOW
# ============================================================================
async def main():
    """Main deployment flow"""

    print("\n" + "="*80)
    print("  STANDALONE PII/PHI SOLUTION DEPLOYMENT (Hybrid)")
    print("="*80)

    try:
        # Step 1: Authenticate
        print("\n1. Authenticating...")
        token = await get_access_token()
        print("   ✓ Access token obtained")

        # Step 2: Find workspace
        print(f"\n2. Finding workspace '{WORKSPACE_NAME}'...")
        workspace = await find_workspace(token, WORKSPACE_NAME)
        if not workspace:
            raise RuntimeError(f"Workspace '{WORKSPACE_NAME}' not found")
        workspace_id = workspace.get("id")
        print(f"   ✓ Found workspace: {workspace_id}")

        # Step 3: Find Lakehouse
        print(f"\n3. Finding Lakehouse '{LAKEHOUSE_NAME}'...")
        lakehouse = await find_item_in_workspace(token, workspace_id, "Lakehouse", LAKEHOUSE_NAME)
        if not lakehouse:
            raise RuntimeError(f"Lakehouse '{LAKEHOUSE_NAME}' not found. Please create it first.")
        lakehouse_id = lakehouse.get("id")
        print(f"   ✓ Found Lakehouse: {lakehouse_id}")
        
        # Step 4: Find Warehouse
        print(f"\n4. Finding Warehouse '{WAREHOUSE_NAME}'...")
        warehouse = await find_item_in_workspace(token, workspace_id, "Warehouse", WAREHOUSE_NAME)
        if not warehouse:
            raise RuntimeError(f"Warehouse '{WAREHOUSE_NAME}' not found. Please create it and the '{TABLE_NAME}' table first.")
        warehouse_id = warehouse.get("id")
        print(f"   ✓ Found Warehouse: {warehouse_id}")
        print(f"   (Assuming table '{TABLE_NAME}' already exists in this Warehouse)")

        # Step 4.5: Get Warehouse SQL Endpoint and Create Connection
        print(f"\n4.5. Creating Warehouse SQL Connection...")
        print(f"   - Getting warehouse SQL endpoint...")
        warehouse_sql_endpoint = await get_warehouse_sql_endpoint(token, workspace_id, warehouse_id)
        print(f"   ✓ SQL Endpoint: {warehouse_sql_endpoint}")

        print(f"   - Creating/Getting SQL connection 'Warehouse_jay_reddy'...")
        warehouse_connection = await create_or_get_warehouse_connection(
            token=token,
            connection_name="Warehouse_jay_reddy",
            sql_endpoint=warehouse_sql_endpoint,
            database_name=WAREHOUSE_NAME
        )
        warehouse_connection_id = warehouse_connection.get("id")
        print(f"   ✓ Warehouse connection ready: {warehouse_connection_id}")

        # Step 5: Create and Define Notebook
        print(f"\n5. Deploying Notebook '{NOTEBOOK_NAME}'...")
        # Find or create the notebook
        notebook = await get_or_create_item(token, workspace_id, "Notebook", NOTEBOOK_NAME)
        notebook_id = notebook.get("id")
        
        print("   ...Waiting 3s for notebook item to provision...")
        await asyncio.sleep(3)
        
        print(f"   - Converting Python script to .ipynb format (and attaching lakehouse)...")
        # --- FIX: Pass lakehouse_id here ---
        notebook_definition = get_notebook_ipynb_content(NOTEBOOK_PYTHON_SOURCE, lakehouse_id)
        
        print(f"   - Uploading Notebook definition...")
        await update_item_definition(token, workspace_id, notebook_id, notebook_definition)
        print(f"   ✓ Notebook '{NOTEBOOK_NAME}' deployed.")

        # Step 6: Create and Define Pipeline
        print(f"\n6. Deploying Pipeline '{PIPELINE_NAME}'...")
        pipeline = await get_or_create_item(token, workspace_id, "DataPipeline", PIPELINE_NAME)
        pipeline_id = pipeline.get("id")

        print("   ...Waiting 3s for pipeline item to provision...")
        await asyncio.sleep(3)
        
        print(f"   - Preparing final pipeline definition...")
        final_pipeline_def = modify_pipeline_definition(
            template_str=PIPELINE_TEMPLATE_JSON,
            new_workspace_id=workspace_id,
            new_lakehouse_id=lakehouse_id,
            new_notebook_id=notebook_id,
            warehouse_connection_id=warehouse_connection_id
        )

        # Save for debugging
        print("   - Saving modified pipeline to debug_pipeline.json...")
        with open("debug_pipeline.json", "w") as f:
            f.write(json.dumps(json.loads(final_pipeline_def), indent=4))

        print(f"   - Uploading Pipeline definition...")
        await update_item_definition(token, workspace_id, pipeline_id, final_pipeline_def)
        print(f"   ✓ Pipeline '{PIPELINE_NAME}' deployed.")

        # Success summary
        print("\n" + "="*80)
        print("  ✅ SOLUTION DEPLOYMENT SUCCESSFUL")
        print("="*80)
        print(f"\n  Workspace:   {WORKSPACE_NAME}")
        print(f"  Lakehouse:   {LAKEHOUSE_NAME} (for Files)")
        print(f"  Warehouse:   {WAREHOUSE_NAME} (for Logs)")
        print(f"  Connection:  Warehouse_jay_reddy (ID: {warehouse_connection_id})")
        print(f"  Notebook:    {NOTEBOOK_NAME} (ID: {notebook_id})")
        print(f"  Pipeline:    {PIPELINE_NAME} (ID: {pipeline_id})")
        print("\n  ✅ PIPELINE DEPLOYED WITH FILE FILTERING!")
        print("  The pipeline flow:")
        print("    1. Script activity queries warehouse for processed files")
        print("    2. GetMetadata lists all files in bronze/")
        print("    3. Filter removes already-processed files")
        print("    4. ForEach processes each new file with notebook")
        print("       └─ Reads from Files/bronze/, writes to Files/silver/")
        print("\n  Next steps:")
        print(f"  1. Open Fabric UI → {WORKSPACE_NAME} workspace")
        print(f"  2. Refresh your browser to see the notebook code")
        print(f"  3. Place 'prior_authorization_data.csv' in '{LAKEHOUSE_NAME}' → 'Files/priorauths/'")
        print(f"  4. Place new claim CSVs in '{LAKEHOUSE_NAME}' → 'Files/bronze/'")
        print(f"  5. (Notebook will automatically write results to '{LAKEHOUSE_NAME}' → 'Files/silver/')")
        print(f"  6. Run the '{PIPELINE_NAME}' pipeline to test")
        print("\n" + "="*80)

    except Exception as e:
        print("\n" + "="*80)
        print("  ❌ DEPLOYMENT FAILED")
        print("="*80)
        import traceback
        traceback.print_exc()
        print(f"\n  Error: {e}")
        print("\n" + "="*80)
        raise


if __name__ == "__main__":
    # Ensure you have the required packages:
    # pip install httpx msal
    asyncio.run(main())

    