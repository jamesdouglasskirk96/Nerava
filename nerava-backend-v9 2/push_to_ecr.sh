#!/bin/bash
# Script to build and push Docker image to AWS ECR
# Make sure Docker Desktop is running and AWS CLI is installed

set -e  # Exit on error

REGISTRY="566287346479.dkr.ecr.us-east-1.amazonaws.com"
IMAGE_NAME="nerava-backend"
REGION="us-east-1"
FULL_IMAGE_URI="${REGISTRY}/${IMAGE_NAME}:latest"

echo "Step 1: Authenticating Docker client to ECR..."
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${REGISTRY}

echo ""
echo "Step 2: Building Docker image..."
docker build -t ${IMAGE_NAME} .

echo ""
echo "Step 3: Tagging image for ECR..."
docker tag ${IMAGE_NAME}:latest ${FULL_IMAGE_URI}

echo ""
echo "Step 4: Pushing image to ECR..."
docker push ${FULL_IMAGE_URI}

echo ""
echo "✅ Successfully pushed ${FULL_IMAGE_URI}"








