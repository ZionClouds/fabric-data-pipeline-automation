#!/bin/bash

# Create Azure AI Search service
az search service create \
  --name fabricdocs-search \
  --resource-group uic-omi-dlake-prod-fab-rg \
  --sku basic \
  --location eastus

# Get the API key
az search admin-key show \
  --resource-group uic-omi-dlake-prod-fab-rg \
  --service-name fabricdocs-search \
  --query primaryKey \
  --output tsv

echo "Azure AI Search created! Now configure web crawler in Azure Portal."
