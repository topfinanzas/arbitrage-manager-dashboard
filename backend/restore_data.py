"""
Restore Data
Restores data from the JSON backup to the new BigQuery table.
"""
import os
import json
import glob
from google.cloud import bigquery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def restore_data():
    print("🚀 Starting data restoration...")
    
    # Find latest backup
    backup_files = glob.glob('backups/metrics_backup_*.json')
    if not backup_files:
        print("❌ No backup files found in backups/ directory")
        return
        
    latest_backup = max(backup_files, key=os.path.getctime)
    print(f"   Using backup file: {latest_backup}")
    
    # Load data
    with open(latest_backup, 'r') as f:
        data = json.load(f)
        
    if not data:
        print("⚠️  Backup file is empty")
        return
        
    print(f"   Records to restore: {len(data)}")
    
    # Initialize client
    project_id = os.getenv('GCP_PROJECT_ID')
    dataset_id = os.getenv('BIGQUERY_DATASET', 'arbitrage')
    location = os.getenv('GCP_REGION', 'us-central1')
    table_id = 'metrics'
    full_table_id = f"{project_id}.{dataset_id}.{table_id}"
    
    print(f"   Target table: {full_table_id}")
    print(f"   Location: {location}")
    
    client = bigquery.Client(project=project_id, location=location)
    
    # Insert data using Load Job (Batch) instead of Streaming
    # This is more robust for migration and avoids some 404 issues with streaming on new tables
    
    # Fetch existing table schema to ensure compatibility
    table = client.get_table(full_table_id)
    schema = table.schema
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        schema=schema, # Use the actual table schema
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND
    )
    
    try:
        job = client.load_table_from_json(data, full_table_id, job_config=job_config)
        print(f"   Job {job.job_id} started...")
        
        job.result()  # Waits for the job to complete.
        
        print(f"✅ Successfully restored {len(data)} records to {full_table_id}")
            
    except Exception as e:
        print(f"❌ Restoration failed: {e}")
        if hasattr(e, 'errors'):
            print(f"   Errors: {e.errors}")

if __name__ == "__main__":
    restore_data()
