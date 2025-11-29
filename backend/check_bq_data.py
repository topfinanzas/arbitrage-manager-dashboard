"""
Check BigQuery Data
Queries the metrics table for specific date to verify spend.
"""
import os
from google.cloud import bigquery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_data():
    print("🔍 Checking BigQuery Data for Nov 28...")
    
    project_id = os.getenv('GCP_PROJECT_ID')
    dataset_id = os.getenv('BIGQUERY_DATASET', 'arbitrage')
    table_id = f"{project_id}.{dataset_id}.metrics"
    
    client = bigquery.Client(project=project_id)
    
    query = f"""
    SELECT 
        date,
        SUM(spend) as total_spend,
        SUM(revenue) as total_revenue,
        COUNT(*) as records
    FROM `{table_id}`
    WHERE date = '2025-11-28'
    GROUP BY date
    """
    
    try:
        results = client.query(query).result()
        found = False
        for row in results:
            found = True
            print(f"✅ Data for {row.date}:")
            print(f"   Spend:   ${row.total_spend:.2f}")
            print(f"   Revenue: ${row.total_revenue:.2f}")
            print(f"   Records: {row.records}")
            
        if not found:
            print("❌ No data found for 2025-11-28")
            
    except Exception as e:
        print(f"❌ Query failed: {e}")

if __name__ == "__main__":
    check_data()
