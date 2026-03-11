#!/bin/bash

# =============================================================================
# Rebuild and Redeploy Frontend with Correct Backend URL
# =============================================================================

set -e  # Exit on error

# Load configuration
source ./deploy-config.sh

echo "=========================================="
echo "Rebuilding Frontend with Backend URL"
echo "=========================================="

# Get current backend URL
BACKEND_URL=$(az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)

if [ -z "$BACKEND_URL" ]; then
    echo "❌ Error: Backend URL not found. Make sure backend is deployed first."
    exit 1
fi

BACKEND_URL="https://$BACKEND_URL"
echo "Backend URL: $BACKEND_URL"
echo ""

# New image tag
NEW_IMAGE_TAG="$(date +%Y%m%d-%H%M%S)"

# =============================================================================
# Rebuild Frontend Image
# =============================================================================
echo "Step 1: Rebuilding Frontend Image..."
cd frontend

docker build -f Dockerfile.new \
    --build-arg REACT_APP_API_URL=$BACKEND_URL \
    --build-arg REACT_APP_WORKSPACE_API_URL=$BACKEND_URL \
    -t $FRONTEND_ACR_NAME.azurecr.io/$FRONTEND_IMAGE_NAME:$NEW_IMAGE_TAG .

docker tag $FRONTEND_ACR_NAME.azurecr.io/$FRONTEND_IMAGE_NAME:$NEW_IMAGE_TAG $FRONTEND_ACR_NAME.azurecr.io/$FRONTEND_IMAGE_NAME:latest

echo "✅ Frontend image rebuilt"

# =============================================================================
# Push to ACR
# =============================================================================
echo ""
echo "Step 2: Pushing to ACR..."
az acr login --name $FRONTEND_ACR_NAME
docker push $FRONTEND_ACR_NAME.azurecr.io/$FRONTEND_IMAGE_NAME:$NEW_IMAGE_TAG
docker push $FRONTEND_ACR_NAME.azurecr.io/$FRONTEND_IMAGE_NAME:latest

echo "✅ Frontend image pushed"

cd ..

# =============================================================================
# Update Container App
# =============================================================================
echo ""
echo "Step 3: Updating Frontend Container App..."

az containerapp update \
    --name "$FRONTEND_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --image "$FRONTEND_ACR_NAME.azurecr.io/$FRONTEND_IMAGE_NAME:$NEW_IMAGE_TAG"

# Get Frontend URL
FRONTEND_URL=$(az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)

echo ""
echo "=========================================="
echo "✅ Frontend Updated Successfully!"
echo "=========================================="
echo "Frontend URL: https://$FRONTEND_URL"
echo "Backend URL:  $BACKEND_URL"
echo "=========================================="
