"""Quick check for revenue total in BigQuery"""
from google.cloud import bigquery
import os
from dotenv import load_dotenv

load_dotenv()

client = bigquery.Client()
dataset = os.getenv('BIGQUERY_DATASET', 'arbitrage')
table_id = f"{client.project}.{dataset}.metrics"

query = f"""
SELECT 
    COUNT(*) as total_records,
    SUM(spend) as total_spend,
    SUM(revenue) as total_revenue,
    SUM(profit) as total_profit
FROM `{table_id}`
WHERE date >= '2025-11-20'
"""

result = client.query(query).result()
for row in result:
    print(f"\n✅ BigQuery Verification:")
    print(f"   Total Records: {row.total_records}")
    print(f"   Total Spend:   ${row.total_spend:.2f}")
    print(f"   Total Revenue: ${row.total_revenue:.2f}")
    print(f"   Total Profit:  ${row.total_profit:.2f}")
    print(f"   ROAS:          {(row.total_revenue / row.total_spend):.2f}x" if row.total_spend > 0 else "   ROAS:          N/A")
