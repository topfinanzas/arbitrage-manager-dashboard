#!/bin/bash
# Deployment script for Cloud Run

set -e

# Configuration
PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
SERVICE_NAME="arbitrage-api"

echo "🚀 Deploying Arbitrage Dashboard API to Cloud Run..."

# Build and deploy
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --project $PROJECT_ID \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID" \
  --set-secrets="META_ACCESS_TOKEN=meta-access-token:latest,SYSTEM1_API_KEY=system1-api-key:latest" \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10

echo "✅ Deployment complete!"
echo "🌐 Service URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)'
