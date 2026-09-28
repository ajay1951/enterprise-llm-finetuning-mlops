#!/bin/bash
set -e

echo "Deploying ForgeLLM to EC2..."

# Variables
ECR_REGISTRY=$1
GIT_SHA=$2
AWS_REGION=${3:-us-east-1}

if [ -z "$ECR_REGISTRY" ] || [ -z "$GIT_SHA" ]; then
    echo "Usage: ./deploy.sh <ecr_registry> <git_sha> [aws_region]"
    exit 1
fi

export ECR_REGISTRY=$ECR_REGISTRY
export GIT_SHA=$GIT_SHA
export AWS_REGION=$AWS_REGION

# Authenticate with ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Pull new images
docker-compose -f docker-compose.prod.yml pull

# Start new containers
docker-compose -f docker-compose.prod.yml up -d

# Verify health
echo "Waiting for API to be ready..."
sleep 10
curl -f http://localhost:8000/api/v1/health || (echo "Health check failed!" && exit 1)

echo "Deployment of $GIT_SHA successful!"
