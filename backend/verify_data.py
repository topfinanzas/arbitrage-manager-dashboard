from google.cloud import bigquery
import os

client = bigquery.Client()
dataset = os.getenv('BIGQUERY_DATASET', 'arbitrage')
project_id = client.project

# Query para verificar datos recientes
query = f"""
SELECT 
    COUNT(DISTINCT ad_set_id) as total_ad_sets,
    MIN(date) as earliest_date,
    MAX(date) as latest_date,
    SUM(spend) as total_spend,
    SUM(revenue) as total_revenue,
    SUM(searches) as total_searches,
    SUM(purchases) as total_purchases,
    SUM(widget_clicks) as total_widget_clicks
FROM `{project_id}.{dataset}.metrics`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
"""

print('📊 Datos en BigQuery (últimos 7 días):')
print('=' * 60)

results = client.query(query).result()
for row in results:
    print(f'Total Ad Sets: {row.total_ad_sets}')
    print(f'Período: {row.earliest_date} a {row.latest_date}')
    print(f'Total Spend (Meta): ${row.total_spend:,.2f}')
    print(f'Total Revenue (System1): ${row.total_revenue:,.2f}')
    print(f'Total Searches (Meta): {row.total_searches:,}')
    print(f'Total Purchases (Meta): {row.total_purchases:,}')
    print(f'Total Widget Clicks (System1): {row.total_widget_clicks:,}')
