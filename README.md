# Arbitrage Dashboard

Real-time dashboard for traffic arbitrage campaign analytics, integrating Meta Ads and System1 data.

## 🏗️ Architecture

- **Backend:** FastAPI (Python) on Google Cloud Run
- **Frontend:** React + Recharts on Firebase Hosting
- **Database:** BigQuery (analytics) + Cloud SQL (transactional)
- **Orchestration:** Cloud Scheduler (hourly sync)

## 📁 Project Structure

```
arbitrage-dashboard/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── meta_client.py          # Meta Ads API integration
│   ├── system1_client.py       # System1 data client
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Container image
│   └── .env.template           # Environment variables template
├── frontend/
│   └── (React app - to be created)
├── gcp-config/
│   ├── bigquery_schema.sql     # Database schema
│   └── deploy.sh               # Deployment script
└── docs/
    └── (Documentation)
```

## 🚀 Quick Start

### Prerequisites

1. Google Cloud Project with billing enabled
2. Meta Ads API access token
3. System1 API credentials (or CSV files)

### Setup

1. **Clone and navigate:**
   ```bash
   cd arbitrage-dashboard/backend
   ```

2. **Configure environment:**
   ```bash
   cp .env.template .env
   # Edit .env with your credentials
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run locally:**
   ```bash
   python main.py
   ```
   API will be available at `http://localhost:8080`

### Deploy to GCP

1. **Set up BigQuery:**
   ```bash
   # Create dataset
   bq mk --dataset your-project:arbitrage
   
   # Create tables
   bq query --use_legacy_sql=false < gcp-config/bigquery_schema.sql
   ```

2. **Store secrets:**
   ```bash
   echo -n "your_meta_token" | gcloud secrets create meta-access-token --data-file=-
   echo -n "your_system1_key" | gcloud secrets create system1-api-key --data-file=-
   ```

3. **Deploy backend:**
   ```bash
   cd gcp-config
   # Edit deploy.sh with your project ID
   ./deploy.sh
   ```

## 📊 API Endpoints

- `GET /` - Health check
- `GET /api/kpis` - Global KPIs (spend, revenue, ROAS)
- `GET /api/campaigns` - List all campaigns with filters
- `GET /api/campaigns/{id}` - Campaign detail with history
- `GET /api/alerts` - Campaigns requiring attention
- `POST /api/sync` - Trigger data synchronization

## 🔑 Environment Variables

See `.env.template` for all required variables.

Key variables:
- `META_ACCESS_TOKEN` - Meta Ads API token
- `META_AD_ACCOUNT_ID` - Ad account ID (without 'act_')
- `GCP_PROJECT_ID` - Google Cloud project ID
- `BIGQUERY_DATASET` - BigQuery dataset name

## 📈 Next Steps

1. Test Meta Ads integration with your account
2. Set up Cloud Scheduler for hourly sync
3. Build React frontend
4. Configure alerts and notifications

## 📝 Documentation

See `/docs` folder for detailed documentation on:
- API integration guides
- Data schema
- Deployment procedures
- Troubleshooting

## 💰 Estimated Costs

- Cloud Run: $0-5/month
- BigQuery: $0-10/month
- Cloud SQL: $9/month
- **Total: ~$10-25/month**

## 🆘 Support

For issues or questions, refer to the implementation plan in the parent directory.
