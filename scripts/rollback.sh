#!/bin/bash
set -e

echo "Rolling back ForgeLLM to previous version..."

# Variables
ECR_REGISTRY=$1
PREVIOUS_GIT_SHA=$2
AWS_REGION=${3:-us-east-1}

if [ -z "$ECR_REGISTRY" ] || [ -z "$PREVIOUS_GIT_SHA" ]; then
    echo "Usage: ./rollback.sh <ecr_registry> <previous_git_sha> [aws_region]"
    exit 1
fi

# A rollback is simply a deployment of an older known-good SHA
./scripts/deploy.sh $ECR_REGISTRY $PREVIOUS_GIT_SHA $AWS_REGION

echo "Rollback to $PREVIOUS_GIT_SHA successful!"
