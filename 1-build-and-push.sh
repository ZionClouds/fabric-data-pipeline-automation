#!/bin/bash

# =============================================================================
# Build and Push Docker Images to Azure Container Registry
# =============================================================================

set -e  # Exit on error

# Load configuration
source ./deploy-config.sh

echo "=========================================="
echo "Building and Pushing Docker Images to ACR"
echo "=========================================="
echo "Backend ACR: $BACKEND_ACR_NAME"
echo "Frontend ACR: $FRONTEND_ACR_NAME"
echo "Image Tag: $IMAGE_TAG"
echo "=========================================="

# =============================================================================
# Step 1: Azure Login
# =============================================================================
echo ""
echo "Step 1: Azure Login"
az login

# =============================================================================
# Step 2: Build and Push Backend Image
# =============================================================================
echo ""
echo "Step 2: Building Backend Docker Image..."
cd backend

# Build the image
docker build -f Dockerfile.new -t $BACKEND_ACR_NAME.azurecr.io/$BACKEND_IMAGE_NAME:$IMAGE_TAG .
docker tag $BACKEND_ACR_NAME.azurecr.io/$BACKEND_IMAGE_NAME:$IMAGE_TAG $BACKEND_ACR_NAME.azurecr.io/$BACKEND_IMAGE_NAME:latest

echo "Backend image built successfully!"

# Login to backend ACR
echo "Logging into Backend ACR..."
az acr login --name $BACKEND_ACR_NAME

# Push the image
echo "Pushing Backend image to ACR..."
docker push $BACKEND_ACR_NAME.azurecr.io/$BACKEND_IMAGE_NAME:$IMAGE_TAG
docker push $BACKEND_ACR_NAME.azurecr.io/$BACKEND_IMAGE_NAME:latest

echo "✅ Backend image pushed successfully!"
echo "Image: $BACKEND_ACR_NAME.azurecr.io/$BACKEND_IMAGE_NAME:$IMAGE_TAG"

cd ..

# =============================================================================
# Step 3: Build and Push Frontend Image
# =============================================================================
echo ""
echo "Step 3: Building Frontend Docker Image..."
cd frontend

# Ask for backend URL if not set (or we'll update it later)
if [ -z "$BACKEND_URL" ]; then
    echo "⚠️  BACKEND_URL not set. You'll need to rebuild frontend after deploying backend."
    BACKEND_URL="http://localhost:8080"  # Placeholder
fi

# Build the image
docker build -f Dockerfile.new \
    --build-arg REACT_APP_API_URL=$BACKEND_URL \
    --build-arg REACT_APP_WORKSPACE_API_URL=$BACKEND_URL \
    -t $FRONTEND_ACR_NAME.azurecr.io/$FRONTEND_IMAGE_NAME:$IMAGE_TAG .

docker tag $FRONTEND_ACR_NAME.azurecr.io/$FRONTEND_IMAGE_NAME:$IMAGE_TAG $FRONTEND_ACR_NAME.azurecr.io/$FRONTEND_IMAGE_NAME:latest

echo "Frontend image built successfully!"

# Login to frontend ACR (skip if same as backend)
if [ "$FRONTEND_ACR_NAME" != "$BACKEND_ACR_NAME" ]; then
    echo "Logging into Frontend ACR..."
    az acr login --name $FRONTEND_ACR_NAME
fi

# Push the image
echo "Pushing Frontend image to ACR..."
docker push $FRONTEND_ACR_NAME.azurecr.io/$FRONTEND_IMAGE_NAME:$IMAGE_TAG
docker push $FRONTEND_ACR_NAME.azurecr.io/$FRONTEND_IMAGE_NAME:latest

echo "✅ Frontend image pushed successfully!"
echo "Image: $FRONTEND_ACR_NAME.azurecr.io/$FRONTEND_IMAGE_NAME:$IMAGE_TAG"

cd ..

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "=========================================="
echo "✅ All Images Built and Pushed Successfully!"
echo "=========================================="
echo "Backend:  $BACKEND_ACR_NAME.azurecr.io/$BACKEND_IMAGE_NAME:$IMAGE_TAG"
echo "Frontend: $FRONTEND_ACR_NAME.azurecr.io/$FRONTEND_IMAGE_NAME:$IMAGE_TAG"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Run: ./2-deploy-to-azure.sh to deploy containers to Azure Container Apps"
echo "   OR"
echo "2. Pull and run these images anywhere you want"
echo "=========================================="
