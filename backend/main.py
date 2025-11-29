"""
Arbitrage Dashboard - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import os
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from google.cloud import bigquery
from google_sheets_service import GoogleSheetsService

app = FastAPI(
    title="Arbitrage Dashboard API",
    description="API for traffic arbitrage campaign analytics",
    version="1.0.0"
)

# CORS configuration for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DATA MODELS
# ============================================================================

class CampaignMetrics(BaseModel):
    ad_set_id: str
    ad_set_name: str
    market: str
    spend: float
    revenue: float
    profit: float
    roas: float
    link_clicks: int
    monetized_clicks: int
    meta_cpc: float
    widget_ctr: float
    rpc: float
    date: date

class CampaignSummary(BaseModel):
    ad_set_id: str
    ad_set_name: str
    market: str
    total_spend: float
    total_revenue: float
    total_profit: float
    avg_roas: float
    status: str  # "profitable", "break-even", "loss"

class GlobalKPIs(BaseModel):
    total_spend: float
    total_revenue: float
    total_profit: float
    avg_roas: float
    total_campaigns: int
    profitable_campaigns: int
    # Engagement KPIs
    total_searches: int = 0
    cost_per_search: float = 0.0
    total_purchases: int = 0
    cost_per_purchase: float = 0.0
    avg_widget_ctr: float = 0.0
    total_widget_clicks: int = 0
    avg_rpc: float = 0.0

class GlobalKPIsWithComparison(BaseModel):
    primary: GlobalKPIs
    comparison: Optional[GlobalKPIs] = None

class CampaignPerformanceRow(BaseModel):
    """Performance data for campaign/adset/ad level"""
    id: str  # campaign_id, ad_set_id, or ad_id depending on level
    name: str  # campaign_name, ad_set_name, or ad_name
    spend: float
    revenue: float
    profit: float
    roas: float
    visitors: int  # Meta link clicks
    eventos_busqueda: int  # searches
    costo_busqueda: float  # cost per search
    eventos_compra: int  # purchases
    costo_compra: float  # cost per purchase
    widget_ctr: float
    clicks_pagos: int  # widget_clicks
    rpc_prom: float  # average RPC

class CampaignPerformanceResponse(BaseModel):
    level: str  # "campaign", "adset", or "ad"
    data: List[CampaignPerformanceRow]
    total_rows: int

class CurrentMetrics(BaseModel):
    cpc: float
    rpc: float
    widget_ctr: float
    spend: float

# ============================================================================
# BIGQUERY CLIENT
# ============================================================================

bigquery_client = None

# BigQuery client is initialized in the startup event at the bottom of the file
bigquery_client = None

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Arbitrage Dashboard API",
        "version": "1.0.0"
    }

@app.get("/api/kpis")
async def get_global_kpis(
    start_date: str,
    end_date: str,
    comparison_start: Optional[str] = None,
    comparison_end: Optional[str] = None
):
    """
    Get global KPIs for the dashboard with optional comparison period
    
    Query params:
    - start_date: Start date for primary period (YYYY-MM-DD)
    - end_date: End date for primary period (YYYY-MM-DD)
    - comparison_start: Start date for comparison period (YYYY-MM-DD, optional)
    - comparison_end: End date for comparison period (YYYY-MM-DD, optional)
    
    Returns:
    - If comparison dates provided: { primary: {...}, comparison: {...} }
    - Otherwise: { total_spend, total_revenue, ... }
    """
    
    print(f"🔍 Requesting KPIs for: {start_date} to {end_date}")
    print(f"   Comparison: {comparison_start} to {comparison_end}")
    print(f"   BigQuery Client Status: {'Initialized' if bigquery_client else 'None'}")
    
    if not bigquery_client:
        print("⚠️  Returning fallback data because BigQuery client is None")
        # Fallback data if BigQuery is not available
        primary_kpis = GlobalKPIs(
            total_spend=450.23,
            total_revenue=89.12,
            total_profit=-361.11,
            avg_roas=0.20,
            total_campaigns=12,
            profitable_campaigns=0
        )
        
        if comparison_start and comparison_end:
            comparison_kpis = GlobalKPIs(
                total_spend=380.50,
                total_revenue=75.30,
                total_profit=-305.20,
                avg_roas=0.198,
                total_campaigns=12,
                profitable_campaigns=0
            )
            return {"primary": primary_kpis, "comparison": comparison_kpis}
        
        return primary_kpis
    
    try:
        dataset = os.getenv('BIGQUERY_DATASET', 'arbitrage')
        print(f"   Querying dataset: {dataset}")
        
        # Query for primary period
        # We calculate Profit and ROAS dynamically for consistency
        primary_query = f"""
        SELECT
            SUM(spend) as total_spend,
            SUM(revenue) as total_revenue,
            (SUM(revenue) - SUM(spend)) as total_profit,
            (SAFE_DIVIDE(SUM(revenue), SUM(spend)) - 1) as avg_roas,
            COUNT(DISTINCT ad_set_id) as total_campaigns,
            COUNTIF((revenue - spend) > 0) as profitable_campaigns,
            SUM(searches) as total_searches,
            SAFE_DIVIDE(SUM(spend), SUM(searches)) as cost_per_search,
            SUM(purchases) as total_purchases,
            SAFE_DIVIDE(SUM(spend), SUM(purchases)) as cost_per_purchase,
            SAFE_DIVIDE(SUM(widget_clicks), SUM(link_clicks)) as avg_widget_ctr,
            SUM(widget_clicks) as total_widget_clicks,
            SAFE_DIVIDE(SUM(revenue), SUM(widget_clicks)) as avg_rpc
        FROM `{bigquery_client.project}.{dataset}.metrics`
        WHERE date >= @start_date AND date <= @end_date
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            ]
        )
        
        primary_result = bigquery_client.query(primary_query, job_config=job_config).result()
        primary_row = list(primary_result)[0]
        
        primary_kpis = GlobalKPIs(
            total_spend=float(primary_row.total_spend or 0),
            total_revenue=float(primary_row.total_revenue or 0),
            total_profit=float(primary_row.total_profit or 0),
            avg_roas=float(primary_row.avg_roas or 0),
            total_campaigns=int(primary_row.total_campaigns or 0),
            profitable_campaigns=int(primary_row.profitable_campaigns or 0),
            total_searches=int(primary_row.total_searches or 0),
            cost_per_search=float(primary_row.cost_per_search or 0),
            total_purchases=int(primary_row.total_purchases or 0),
            cost_per_purchase=float(primary_row.cost_per_purchase or 0),
            avg_widget_ctr=float(primary_row.avg_widget_ctr or 0),
            total_widget_clicks=int(primary_row.total_widget_clicks or 0),
            avg_rpc=float(primary_row.avg_rpc or 0)
        )
        
        # Query for comparison period if provided
        if comparison_start and comparison_end:
            comparison_query = f"""
            SELECT
                SUM(spend) as total_spend,
                SUM(revenue) as total_revenue,
                (SUM(revenue) - SUM(spend)) as total_profit,
                (SAFE_DIVIDE(SUM(revenue), SUM(spend)) - 1) as avg_roas,
                COUNT(DISTINCT ad_set_id) as total_campaigns,
                COUNTIF((revenue - spend) > 0) as profitable_campaigns,
                SUM(searches) as total_searches,
                SAFE_DIVIDE(SUM(spend), SUM(searches)) as cost_per_search,
                SUM(purchases) as total_purchases,
                SAFE_DIVIDE(SUM(spend), SUM(purchases)) as cost_per_purchase,
                SAFE_DIVIDE(SUM(widget_clicks), SUM(link_clicks)) as avg_widget_ctr,
                SUM(widget_clicks) as total_widget_clicks,
                SAFE_DIVIDE(SUM(revenue), SUM(widget_clicks)) as avg_rpc
            FROM `{bigquery_client.project}.{dataset}.metrics`
            WHERE date >= @comparison_start AND date <= @comparison_end
            """
            
            comparison_job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("comparison_start", "DATE", comparison_start),
                    bigquery.ScalarQueryParameter("comparison_end", "DATE", comparison_end),
                ]
            )
            
            comparison_result = bigquery_client.query(comparison_query, job_config=comparison_job_config).result()
            comparison_row = list(comparison_result)[0]
            
            comparison_kpis = GlobalKPIs(
                total_spend=float(comparison_row.total_spend or 0),
                total_revenue=float(comparison_row.total_revenue or 0),
                total_profit=float(comparison_row.total_profit or 0),
                avg_roas=float(comparison_row.avg_roas or 0),
                total_campaigns=int(comparison_row.total_campaigns or 0),
                profitable_campaigns=int(comparison_row.profitable_campaigns or 0),
                total_searches=int(comparison_row.total_searches or 0),
                cost_per_search=float(comparison_row.cost_per_search or 0),
                total_purchases=int(comparison_row.total_purchases or 0),
                cost_per_purchase=float(comparison_row.cost_per_purchase or 0),
                avg_widget_ctr=float(comparison_row.avg_widget_ctr or 0),
                total_widget_clicks=int(comparison_row.total_widget_clicks or 0),
                avg_rpc=float(comparison_row.avg_rpc or 0)
            )
            
            return {"primary": primary_kpis, "comparison": comparison_kpis}
        
        return primary_kpis
        
    except Exception as e:
        print(f"❌ Error querying BigQuery: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

@app.get("/api/campaigns", response_model=CampaignPerformanceResponse)
async def get_campaigns(
    level: str = "adset",  # "campaign", "adset", or "ad"
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """
    Get campaign performance data aggregated by level (campaign, adset, or ad)
    Query params:
    - level: Aggregation level ("campaign", "adset", "ad") - default: "adset"
    - date_from: Start date (YYYY-MM-DD)
    - date_to: End date (YYYY-MM-DD)
    """
    if not bigquery_client:
        # Return empty data if BigQuery is not available
        return CampaignPerformanceResponse(level=level, data=[], total_rows=0)
    
    # Validate level
    if level not in ["campaign", "adset", "ad"]:
        raise HTTPException(status_code=400, detail="Invalid level. Must be 'campaign', 'adset', or 'ad'")
    
    # Default date range: last 7 days ending yesterday
    if not date_from:
        date_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.now().strftime('%Y-%m-%d')
    
    try:
        project_id = bigquery_client.project
        dataset = os.getenv('BIGQUERY_DATASET', 'arbitrage')
        
        # Construct query based on level
        if level == "campaign":
            group_by = "campaign_id, campaign_name"
            select_id = "campaign_id"
            select_name = "campaign_name"
        elif level == "ad":
            group_by = "ad_id, ad_name"
            select_id = "ad_id"
            select_name = "ad_name"
        else:  # adset
            group_by = "ad_set_id, ad_set_name"
            select_id = "ad_set_id"
            select_name = "ad_set_name"
        
        query = f"""
        SELECT
            {select_id} as id,
            {select_name} as name,
            ROUND(SUM(spend), 2) as spend,
            ROUND(SUM(revenue), 2) as revenue,
            ROUND(SUM(profit), 2) as profit,
            ROUND(AVG(roas), 2) as roas,
            SUM(link_clicks) as visitors,
            SUM(searches) as eventos_busqueda,
            ROUND(SAFE_DIVIDE(SUM(spend), SUM(searches)), 2) as costo_busqueda,
            SUM(purchases) as eventos_compra,
            ROUND(SAFE_DIVIDE(SUM(spend), SUM(purchases)), 2) as costo_compra,
            ROUND(AVG(SAFE_DIVIDE(widget_clicks, widget_searches)) * 100, 2) as widget_ctr,
            SUM(widget_clicks) as clicks_pagos,
            ROUND(SAFE_DIVIDE(SUM(revenue), SUM(widget_clicks)), 2) as rpc_prom
        FROM `{project_id}.{dataset}.metrics`
        WHERE date >= '{date_from}'
          AND date <= '{date_to}'
          AND {select_id} IS NOT NULL  -- Filter out nulls
        GROUP BY {group_by}
        ORDER BY spend DESC
        """
        
        print(f"🔍 Executing query for {level} level: {date_from} to {date_to}")
        
        query_job = bigquery_client.query(query)
        results = query_job.result()
        
        data = []
        for row in results:
            data.append(CampaignPerformanceRow(
                id=row.id or "UNKNOWN",
                name=row.name or "Unknown",
                spend=row.spend or 0.0,
                revenue=row.revenue or 0.0,
                profit=row.profit or 0.0,
                roas=row.roas or 0.0,
                visitors=row.visitors or 0,
                eventos_busqueda=row.eventos_busqueda or 0,
                costo_busqueda=row.costo_busqueda or 0.0,
                eventos_compra=row.eventos_compra or 0,
                costo_compra=row.costo_compra or 0.0,
                widget_ctr=row.widget_ctr or 0.0,
                clicks_pagos=row.clicks_pagos or 0,
                rpc_prom=row.rpc_prom or 0.0
            ))
        
        print(f"✅ Returned {len(data)} rows for {level} level")
        
        return CampaignPerformanceResponse(
            level=level,
            data=data,
            total_rows=len(data)
        )
        
    except Exception as e:
        print(f"❌ Error querying campaigns: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

@app.get("/api/campaigns/{ad_set_id}", response_model=List[CampaignMetrics])
async def get_campaign_detail(ad_set_id: str, days: int = 30):
    """
    Get detailed metrics for a specific campaign
    Path params:
    - ad_set_id: Ad Set ID
    Query params:
    - days: Number of days of history (default: 30)
    """
    # TODO: Implement BigQuery query for time series
    return []

@app.get("/api/alerts")
async def get_alerts():
    """
    Get campaigns that require attention
    Returns campaigns with:
    - ROAS < 0.7x
    - Spend > $100 and ROAS < 1.0x
    - Widget CTR < 10%
    """
    # TODO: Implement alert logic
    return {
        "critical": [],
        "warning": [],
        "info": []
    }

@app.get("/api/analytics/current-metrics", response_model=CurrentMetrics)
async def get_current_metrics():
    """
    Get current weighted average metrics from the last 7 days
    to seed the Scenario Builder
    """
    if not bigquery_client:
        # Fallback if BigQuery is not initialized
        return CurrentMetrics(
            cpc=0.15,
            rpc=0.08,
            widget_ctr=25.0,
            spend=500.0
        )
    
    dataset = os.getenv("BIGQUERY_DATASET", "arbitrage")
    query = f"""
        SELECT
            SUM(spend) as total_spend,
            SUM(link_clicks) as total_link_clicks,
            SUM(widget_clicks) as total_widget_clicks,
            SUM(revenue) as total_revenue
        FROM `{bigquery_client.project}.{dataset}.metrics`
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    """
    
    try:
        query_job = bigquery_client.query(query)
        results = query_job.result()
        
        for row in results:
            total_spend = row.total_spend or 0
            total_link_clicks = row.total_link_clicks or 0
            total_widget_clicks = row.total_widget_clicks or 0
            total_revenue = row.total_revenue or 0
            
            # Calculate weighted averages
            cpc = total_spend / total_link_clicks if total_link_clicks > 0 else 0.15
            rpc = total_revenue / total_widget_clicks if total_widget_clicks > 0 else 0.08
            widget_ctr = (total_widget_clicks / total_link_clicks * 100) if total_link_clicks > 0 else 25.0
            avg_daily_spend = total_spend / 7 if total_spend > 0 else 500.0
            
            return CurrentMetrics(
                cpc=round(cpc, 2),
                rpc=round(rpc, 2),
                widget_ctr=round(widget_ctr, 1),
                spend=round(avg_daily_spend, 0)
            )
            
    except Exception as e:
        print(f"Error fetching current metrics: {e}")
        # Return defaults on error
        return CurrentMetrics(
            cpc=0.15,
            rpc=0.08,
            widget_ctr=25.0,
            spend=500.0
        )

@app.post("/api/sync")
async def trigger_sync():
    """
    Manually trigger data synchronization from Meta and System1
    This endpoint will be called by Cloud Scheduler
    """
    # TODO: Implement sync logic
    return {
        "status": "started",
        "message": "Data synchronization initiated",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# GOOGLE SHEETS OAUTH ENDPOINTS
# ============================================================================

# In-memory token storage (for development - use database in production)
user_tokens = {}

sheets_service = GoogleSheetsService()

@app.get("/api/auth/google")
async def google_auth():
    """Initiate Google OAuth flow"""
    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Get authorization URL
    auth_url = sheets_service.get_authorization_url(state=state)
    
    return {"auth_url": auth_url, "state": state}

@app.get("/api/auth/google/callback")
async def google_callback(code: str, state: str):
    """Handle OAuth callback from Google"""
    try:
        # Exchange code for token
        token_data = sheets_service.exchange_code_for_token(code)
        
        # Store token (use session ID in production)
        session_id = secrets.token_urlsafe(16)
        user_tokens[session_id] = token_data
        
        # Redirect back to frontend with session ID
        frontend_url = "http://localhost:5173"
        return RedirectResponse(
            url=f"{frontend_url}?auth_success=true&session_id={session_id}"
        )
    except Exception as e:
        print(f"❌ OAuth callback error: {e}")
        return RedirectResponse(
            url=f"http://localhost:5173?auth_error=true&message={str(e)}"
        )

class ExportRequest(BaseModel):
    session_id: str
    date_from: str
    date_to: str

@app.post("/api/export-to-sheets")
async def export_to_sheets(request: ExportRequest):
    """
    Export campaign performance data to Google Sheets
    Creates a spreadsheet with 3 sheets: Campaigns, Ad Groups, Ads
    """
    try:
        # Get user token
        if request.session_id not in user_tokens:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated. Please authorize with Google first."
            )
        
        token_data = user_tokens[request.session_id]
        
        # Fetch data for all three levels
        campaigns_response = await get_campaigns(
            level="campaign",
            date_from=request.date_from,
            date_to=request.date_to
        )
        
        adgroups_response = await get_campaigns(
            level="adset",
            date_from=request.date_from,
            date_to=request.date_to
        )
        
        ads_response = await get_campaigns(
            level="ad",
            date_from=request.date_from,
            date_to=request.date_to
        )
        
        # Format data for sheets
        def format_for_sheets(data: List[CampaignPerformanceRow]) -> List[Dict[str, Any]]:
            return [
                {
                    'ID': row.id,
                    'Name': row.name,
                    'Spend': row.spend,
                    'Revenue': row.revenue,
                    'Profit': row.profit,
                    'ROAS': f"{row.roas * 100:.1f}%",
                    'Searches': row.eventos_busqueda,
                    'Cost/Search': row.costo_busqueda,
                    'Purchases': row.eventos_compra,
                    'Cost/Purchase': row.costo_compra,
                    'Widget CTR': f"{row.widget_ctr:.2f}%",
                    'Widget Clicks': row.clicks_pagos,
                    'RPC': row.rpc_prom,
                }
                for row in data
            ]
        
        sheets_data = {
            'Campaigns': format_for_sheets(campaigns_response.data),
            'Ad Groups': format_for_sheets(adgroups_response.data),
            'Ads': format_for_sheets(ads_response.data),
        }
        
        # Create spreadsheet
        title = f"Campaign Performance {request.date_from} to {request.date_to}"
        spreadsheet_url = sheets_service.create_spreadsheet(
            token_data=token_data,
            title=title,
            sheets_data=sheets_data
        )
        
        return {
            "success": True,
            "spreadsheet_url": spreadsheet_url,
            "message": "Spreadsheet created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Export error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create spreadsheet: {str(e)}"
        )

# ============================================================================
# STARTUP / SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    print("🚀 Arbitrage Dashboard API starting...")
    global bigquery_client
    try:
        project_id = os.getenv('GCP_PROJECT_ID')
        bigquery_client = bigquery.Client(project=project_id)
        print(f"✅ BigQuery client initialized (Project: {bigquery_client.project})")
    except Exception as e:
        print(f"⚠️ Failed to initialize BigQuery client: {e}")
        bigquery_client = None

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Arbitrage Dashboard API shutting down...")
    # Close connections if needed

