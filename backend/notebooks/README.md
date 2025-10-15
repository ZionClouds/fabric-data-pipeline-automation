# Fabric Pipeline Notebooks

This directory contains production-ready Jupyter notebooks for the medallion architecture data pipeline.

## Notebooks

### 1. nb_load_bronze_amazon_products.ipynb
**Bronze Layer** - Load raw data from Azure Blob Storage

- Connects to Azure Blob Storage (fabricsatest123/fabric/amazon.csv)
- Reads CSV with schema inference
- Adds audit columns (ingestion_timestamp, source_file, source_system)
- Writes to Delta table: `bronze_amazon_products`

### 2. nb_amazon_silver_transform.ipynb
**Silver Layer** - Clean and transform data

- Reads from `bronze_amazon_products`
- Data quality checks (null counts, duplicates)
- Data cleaning (trim whitespace, standardize text)
- Filters invalid records
- Adds silver layer metadata
- Writes to: `silver_amazon_products`

### 3. nb_amazon_gold_aggregation.ipynb
**Gold Layer** - Business aggregations

- Reads from `silver_amazon_products`
- Creates category-level statistics
- Calculates business metrics (avg price, counts, etc.)
- Adds gold layer metadata
- Writes to: `gold_amazon_products`

## Usage

These notebooks can be:
1. Uploaded directly to Fabric workspace
2. Referenced in pipeline Notebook Activities
3. Used as templates for other data pipelines

## Data Flow

```
Azure Blob Storage (amazon.csv)
    ↓
Bronze Layer (bronze_amazon_products)
    ↓
Silver Layer (silver_amazon_products)
    ↓
Gold Layer (gold_amazon_products)
```
