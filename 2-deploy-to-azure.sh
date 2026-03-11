#!/bin/bash

# =============================================================================
# Deploy Docker Images from ACR to Azure Container Apps
# =============================================================================

set -e  # Exit on error

# Load configuration
source ./deploy-config.sh

echo "=========================================="
echo "Deploying to Azure Container Apps"
echo "=========================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "Environment: $CONTAINER_ENV_NAME"
echo "Region: $REGION"
echo "=========================================="

# =============================================================================
# Step 1: Ensure Resource Group Exists
# =============================================================================
echo ""
echo "Step 1: Creating Resource Group (if not exists)..."
az group create --name $RESOURCE_GROUP --location $REGION || echo "Resource group already exists"

# =============================================================================
# Step 2: Enable ACR Admin Access
# =============================================================================
echo ""
echo "Step 2: Enabling ACR admin access..."
az acr update --name $BACKEND_ACR_NAME --admin-enabled true
if [ "$FRONTEND_ACR_NAME" != "$BACKEND_ACR_NAME" ]; then
    az acr update --name $FRONTEND_ACR_NAME --admin-enabled true
fi

# Get ACR credentials
BACKEND_ACR_USERNAME=$(az acr credential show --name $BACKEND_ACR_NAME --query 'username' -o tsv)
BACKEND_ACR_PASSWORD=$(az acr credential show --name $BACKEND_ACR_NAME --query 'passwords[0].value' -o tsv)

FRONTEND_ACR_USERNAME=$(az acr credential show --name $FRONTEND_ACR_NAME --query 'username' -o tsv)
FRONTEND_ACR_PASSWORD=$(az acr credential show --name $FRONTEND_ACR_NAME --query 'passwords[0].value' -o tsv)

# =============================================================================
# Step 3: Create Container Apps Environment
# =============================================================================
echo ""
echo "Step 3: Creating Container Apps Environment..."
if ! az containerapp env show --name $CONTAINER_ENV_NAME --resource-group $RESOURCE_GROUP > /dev/null 2>&1; then
    az containerapp env create \
        --name $CONTAINER_ENV_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $REGION
    echo "✅ Container Apps Environment created"
else
    echo "Container Apps Environment already exists"
fi

# =============================================================================
# Step 4: Deploy Backend Container
# =============================================================================
echo ""
echo "Step 4: Deploying Backend Container..."

BACKEND_IMAGE="$BACKEND_ACR_NAME.azurecr.io/$BACKEND_IMAGE_NAME:$IMAGE_TAG"

if ! az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP > /dev/null 2>&1; then
    echo "Creating new backend container app..."
    az containerapp create \
        --name "$BACKEND_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --environment "$CONTAINER_ENV_NAME" \
        --image "$BACKEND_IMAGE" \
        --cpu 1.0 \
        --memory 2.0Gi \
        --ingress external \
        --target-port 8080 \
        --min-replicas 1 \
        --max-replicas 3 \
        --registry-server "$BACKEND_ACR_NAME.azurecr.io" \
        --registry-username "$BACKEND_ACR_USERNAME" \
        --registry-password "$BACKEND_ACR_PASSWORD" \
        --env-vars \
            ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
            AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
            AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
            AZURE_OPENAI_DEPLOYMENT="$AZURE_OPENAI_DEPLOYMENT" \
            AZURE_OPENAI_API_VERSION="$AZURE_OPENAI_API_VERSION" \
            FABRIC_CLIENT_ID="$FABRIC_CLIENT_ID" \
            FABRIC_TENANT_ID="$FABRIC_TENANT_ID" \
            FABRIC_CLIENT_SECRET="$FABRIC_CLIENT_SECRET" \
            DISABLE_AUTH="$DISABLE_AUTH"
else
    echo "Updating existing backend container app..."
    az containerapp update \
        --name "$BACKEND_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --image "$BACKEND_IMAGE"
fi

# Get Backend URL
BACKEND_URL=$(az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)
echo "✅ Backend deployed successfully!"
echo "Backend URL: https://$BACKEND_URL"

# =============================================================================
# Step 5: Deploy Frontend Container
# =============================================================================
echo ""
echo "Step 5: Deploying Frontend Container..."

FRONTEND_IMAGE="$FRONTEND_ACR_NAME.azurecr.io/$FRONTEND_IMAGE_NAME:$IMAGE_TAG"

if ! az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP > /dev/null 2>&1; then
    echo "Creating new frontend container app..."
    az containerapp create \
        --name "$FRONTEND_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --environment "$CONTAINER_ENV_NAME" \
        --image "$FRONTEND_IMAGE" \
        --cpu 0.5 \
        --memory 1.0Gi \
        --ingress external \
        --target-port 8080 \
        --min-replicas 1 \
        --max-replicas 3 \
        --registry-server "$FRONTEND_ACR_NAME.azurecr.io" \
        --registry-username "$FRONTEND_ACR_USERNAME" \
        --registry-password "$FRONTEND_ACR_PASSWORD"
else
    echo "Updating existing frontend container app..."
    az containerapp update \
        --name "$FRONTEND_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --image "$FRONTEND_IMAGE"
fi

# Get Frontend URL
FRONTEND_URL=$(az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)
echo "✅ Frontend deployed successfully!"
echo "Frontend URL: https://$FRONTEND_URL"

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo "Backend URL:  https://$BACKEND_URL"
echo "Frontend URL: https://$FRONTEND_URL"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: You may need to rebuild the frontend with the correct backend URL:"
echo "1. Edit deploy-config.sh and set BACKEND_URL=https://$BACKEND_URL"
echo "2. Run: ./3-rebuild-frontend.sh"
echo "=========================================="
