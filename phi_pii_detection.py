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
fileName = fileName
SOURCE_CLAIM_FILE_PATH = "Files/claims/{filename}"
SOURCE_PRIOR_AUTH_FILE_PATH = "Files/priorauths/prior_authorization_data.csv"  # Changed from table to CSV
OUTPUT_PATH = "Files/claimpriorauth"
PROCESSED_FILES_TABLE = "processedfiles"  # Table to track processed files
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
    print("STEP 6: UPDATE PROCESSED FILES TABLE")
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

        # Append to table (or create if doesn't exist)
        processed_record.write.mode("append").saveAsTable(PROCESSED_FILES_TABLE)
        print(f"Updated {PROCESSED_FILES_TABLE}: {fileName} -> Done")
    except Exception as e:
        print(f"WARNING: Could not update {PROCESSED_FILES_TABLE}: {e}")

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

mssparkutils.notebook.exit(json.dumps(notebook_output))
