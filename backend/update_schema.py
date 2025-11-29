from google.cloud import bigquery
import os
import time

client = bigquery.Client()
dataset = os.getenv('BIGQUERY_DATASET', 'arbitrage')
table_id = f"{client.project}.{dataset}.metrics"

print(f"🗑️  Resetting table {table_id} with NEW SCHEMA...")

create_table_sql = f"""
CREATE OR REPLACE TABLE `{table_id}` (
    campaign_id STRING,
    campaign_name STRING,
    ad_set_id STRING NOT NULL,
    ad_set_name STRING,
    ad_id STRING,
    ad_name STRING,
    market STRING,
    date DATE NOT NULL,
    spend FLOAT64,
    link_clicks INT64,
    meta_cpc FLOAT64,
    meta_ctr FLOAT64,
    searches INT64,
    purchases INT64,
    revenue FLOAT64,
    widget_clicks INT64,
    widget_searches INT64,
    profit FLOAT64,
    roas FLOAT64
)
PARTITION BY date
"""

client.query(create_table_sql).result()
print("✅ Table recreated successfully with new columns.")
