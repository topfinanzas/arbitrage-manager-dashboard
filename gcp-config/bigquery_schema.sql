-- BigQuery Schema for Arbitrage Dashboard
-- Dataset: arbitrage

-- Main metrics table (partitioned by date for performance)
CREATE TABLE IF NOT EXISTS `arbitrage.metrics` (
  ad_set_id STRING NOT NULL,
  ad_set_name STRING,
  market STRING,  -- BR, MX, etc.
  date DATE NOT NULL,
  
  -- Meta Ads metrics
  spend FLOAT64,
  link_clicks INT64,
  meta_cpc FLOAT64,
  meta_ctr FLOAT64,
  
  -- System1 metrics
  revenue FLOAT64,
  widget_clicks INT64,
  widget_searches INT64,
  
  -- Calculated metrics
  profit FLOAT64,
  roas FLOAT64,
  widget_ctr FLOAT64,  -- widget_clicks / link_clicks
  rpc FLOAT64,  -- revenue / widget_clicks
  
  -- Metadata
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  data_source STRING  -- 'meta', 'system1', 'merged'
)
PARTITION BY date
CLUSTER BY market, ad_set_id
OPTIONS(
  description="Daily campaign metrics with cost and revenue data"
);

-- Campaigns metadata table
CREATE TABLE IF NOT EXISTS `arbitrage.campaigns` (
  ad_set_id STRING NOT NULL,
  ad_set_name STRING,
  market STRING,
  status STRING,  -- ACTIVE, PAUSED
  created_at TIMESTAMP,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
OPTIONS(
  description="Campaign metadata and status"
);

-- Alerts configuration table
CREATE TABLE IF NOT EXISTS `arbitrage.alert_config` (
  alert_id STRING NOT NULL,
  alert_type STRING,  -- 'low_roas', 'high_spend', 'low_ctr'
  threshold_value FLOAT64,
  enabled BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
OPTIONS(
  description="Alert thresholds and configuration"
);

-- View: Latest metrics by campaign (last 7 days)
CREATE OR REPLACE VIEW `arbitrage.campaign_summary_7d` AS
SELECT
  ad_set_id,
  ad_set_name,
  market,
  SUM(spend) as total_spend,
  SUM(revenue) as total_revenue,
  SUM(profit) as total_profit,
  AVG(roas) as avg_roas,
  SUM(link_clicks) as total_visitors,
  SUM(widget_clicks) as total_widget_clicks,
  AVG(widget_ctr) as avg_widget_ctr,
  AVG(rpc) as avg_rpc,
  CASE
    WHEN AVG(roas) >= 1.5 THEN 'excellent'
    WHEN AVG(roas) >= 1.0 THEN 'profitable'
    WHEN AVG(roas) >= 0.7 THEN 'break-even'
    ELSE 'loss'
  END as status
FROM `arbitrage.metrics`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY ad_set_id, ad_set_name, market;

-- View: Daily global KPIs
CREATE OR REPLACE VIEW `arbitrage.daily_kpis` AS
SELECT
  date,
  SUM(spend) as total_spend,
  SUM(revenue) as total_revenue,
  SUM(profit) as total_profit,
  AVG(roas) as avg_roas,
  COUNT(DISTINCT ad_set_id) as active_campaigns
FROM `arbitrage.metrics`
GROUP BY date
ORDER BY date DESC;

-- View: Campaigns requiring attention (alerts)
CREATE OR REPLACE VIEW `arbitrage.alerts` AS
SELECT
  ad_set_id,
  ad_set_name,
  market,
  avg_roas,
  total_spend,
  avg_widget_ctr,
  CASE
    WHEN avg_roas < 0.5 THEN 'critical'
    WHEN avg_roas < 0.7 THEN 'warning'
    WHEN avg_widget_ctr < 0.10 THEN 'info'
    ELSE 'ok'
  END as severity,
  CASE
    WHEN avg_roas < 0.5 THEN 'ROAS crítico (<0.5x) - Pausar inmediatamente'
    WHEN avg_roas < 0.7 THEN 'ROAS bajo (<0.7x) - Revisar urgente'
    WHEN avg_widget_ctr < 0.10 THEN 'Widget CTR bajo (<10%) - Optimizar landing'
    ELSE 'OK'
  END as message
FROM `arbitrage.campaign_summary_7d`
WHERE avg_roas < 0.7 OR avg_widget_ctr < 0.10
ORDER BY avg_roas ASC;
