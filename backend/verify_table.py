"""
Verify Table
Checks if the BigQuery table exists and prints its details.
"""
import os
from google.cloud import bigquery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_table():
    print("🔍 Verifying BigQuery Table...")
    
    project_id = os.getenv('GCP_PROJECT_ID')
    dataset_id = os.getenv('BIGQUERY_DATASET', 'arbitrage')
    table_id = 'metrics'
    location = os.getenv('GCP_REGION', 'us-central1')
    
    client = bigquery.Client(project=project_id, location=location)
    
    full_table_id = f"{project_id}.{dataset_id}.{table_id}"
    print(f"   Looking for: {full_table_id}")
    
    try:
        table = client.get_table(full_table_id)
        print(f"✅ Table found!")
        print(f"   Created: {table.created}")
        print(f"   Location: {table.location}")
        print(f"   Num rows: {table.num_rows}")
        print(f"   Schema fields: {len(table.schema)}")
    except Exception as e:
        print(f"❌ Table verification failed: {e}")

if __name__ == "__main__":
    verify_table()
