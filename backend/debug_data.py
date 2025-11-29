from google.cloud import bigquery
import os

client = bigquery.Client()
dataset = os.getenv('BIGQUERY_DATASET', 'arbitrage')
table_id = f"{client.project}.{dataset}.metrics"

print(f"🔍 Checking data in {table_id}...")
print("="*80)

# Check all records for today
query = f"""
SELECT 
    campaign_id,
    campaign_name,
    ad_set_id,
    ad_set_name,
    ad_id,
    ad_name,
    spend,
    revenue,
    profit,
    date
FROM `{table_id}`
WHERE date = '2025-11-27'
ORDER BY revenue DESC
"""

results = client.query(query).result()

print(f"\n📊 Records for 2025-11-27:\n")
print(f"{'Campaign ID':<20} {'Ad Set ID':<20} {'Ad ID':<20} {'Spend':>10} {'Revenue':>10}")
print("-"*80)

for row in results:
    print(f"{str(row.campaign_id):<20} {str(row.ad_set_id):<20} {str(row.ad_id):<20} ${row.spend:>9.2f} ${row.revenue:>9.2f}")

print("\n" + "="*80)

# Check for UNKNOWN records
unknown_query = f"""
SELECT COUNT(*) as count, SUM(revenue) as total_revenue
FROM `{table_id}`
WHERE date = '2025-11-27'
  AND (campaign_id = 'UNKNOWN' OR ad_id = 'UNKNOWN')
"""

unknown_results = client.query(unknown_query).result()
for row in unknown_results:
    print(f"\n⚠️  UNKNOWN Records: {row.count} rows with ${row.total_revenue:.2f} revenue")

# Check for NULL IDs
null_query = f"""
SELECT 
    COUNT(*) as count,
    SUM(revenue) as total_revenue,
    SUM(spend) as total_spend
FROM `{table_id}`
WHERE date = '2025-11-27'
  AND (campaign_id IS NULL OR ad_id IS NULL)
"""

null_results = client.query(null_query).result()
for row in null_results:
    print(f"⚠️  NULL ID Records: {row.count} rows with ${row.total_revenue:.2f} revenue, ${row.total_spend:.2f} spend")
