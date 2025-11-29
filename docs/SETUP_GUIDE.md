# Setup Guide: Arbitrage Dashboard

## Step 1: Configure Meta Ads API

### 1.1 Create Meta App
1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Click "My Apps" → "Create App"
3. Select "Business" type
4. Fill in app details

### 1.2 Get Access Token
1. In your app, go to "Tools" → "Graph API Explorer"
2. Select your ad account
3. Add permissions: `ads_read`, `ads_management`
4. Click "Generate Access Token"
5. **Important:** Convert to long-lived token (60 days):
   ```bash
   curl -G "https://graph.facebook.com/v21.0/oauth/access_token" \
     -d "grant_type=fb_exchange_token" \
     -d "client_id=YOUR_APP_ID" \
     -d "client_secret=YOUR_APP_SECRET" \
     -d "fb_exchange_token=SHORT_LIVED_TOKEN"
   ```

### 1.3 Find Ad Account ID
1. Go to [Meta Ads Manager](https://business.facebook.com/adsmanager/)
2. Look at URL: `act=XXXXXXXXXX` ← This is your Ad Account ID
3. Use the number WITHOUT the `act_` prefix

---

## Step 2: Set Up Google Cloud

### 2.1 Enable APIs
```bash
gcloud services enable run.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 2.2 Create BigQuery Dataset
```bash
bq mk --dataset --location=US arbitrage
```

### 2.3 Create Tables
```bash
cd gcp-config
bq query --use_legacy_sql=false < bigquery_schema.sql
```

### 2.4 Store Secrets
```bash
# Meta Access Token
echo -n "YOUR_META_TOKEN" | gcloud secrets create meta-access-token --data-file=-

# System1 API Key (if available)
echo -n "YOUR_SYSTEM1_KEY" | gcloud secrets create system1-api-key --data-file=-
```

---

## Step 3: Test Locally

### 3.1 Install Dependencies
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3.2 Configure Environment
```bash
cp .env.template .env
# Edit .env with your values
```

### 3.3 Test Meta Integration
```bash
python meta_client.py
```

Expected output:
```
✅ Fetched X ad sets
  - Campaign Name: $XX.XX
  ...
```

### 3.4 Run API
```bash
python main.py
```

Visit: `http://localhost:8080/docs` for interactive API documentation

---

## Step 4: Deploy to Cloud Run

### 4.1 Update Deployment Script
Edit `gcp-config/deploy.sh`:
```bash
PROJECT_ID="your-actual-project-id"
```

### 4.2 Deploy
```bash
cd gcp-config
./deploy.sh
```

### 4.3 Test Deployment
```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe arbitrage-api --region us-central1 --format='value(status.url)')

# Test health endpoint
curl $SERVICE_URL/

# Test KPIs endpoint
curl $SERVICE_URL/api/kpis
```

---

## Step 5: Set Up Automated Sync

### 5.1 Create Cloud Scheduler Job
```bash
# Get Cloud Run service URL
SERVICE_URL=$(gcloud run services describe arbitrage-api --region us-central1 --format='value(status.url)')

# Create hourly sync job
gcloud scheduler jobs create http sync-arbitrage-data \
  --schedule="5 * * * *" \
  --uri="$SERVICE_URL/api/sync" \
  --http-method=POST \
  --location=us-central1 \
  --oidc-service-account-email=YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com
```

### 5.2 Test Manual Sync
```bash
gcloud scheduler jobs run sync-arbitrage-data --location=us-central1
```

---

## Step 6: Verify Data in BigQuery

```bash
# Check if data was loaded
bq query --use_legacy_sql=false '
SELECT 
  date,
  COUNT(*) as campaigns,
  SUM(spend) as total_spend,
  SUM(revenue) as total_revenue
FROM `arbitrage.metrics`
GROUP BY date
ORDER BY date DESC
LIMIT 7
'
```

---

## Troubleshooting

### Error: "Meta API token invalid"
- Token expired (60 days max). Generate a new one.
- Missing permissions. Re-add `ads_read` and `ads_management`.

### Error: "BigQuery table not found"
- Run the schema creation script again.
- Check dataset name matches `.env` configuration.

### Error: "Cloud Run deployment failed"
- Check Docker build logs: `gcloud builds list`
- Verify all secrets exist: `gcloud secrets list`

---

## Next Steps

1. ✅ Backend deployed and syncing data
2. 🔄 Build React frontend
3. 📊 Create visualizations
4. 🔔 Set up alerts (email/Slack)
