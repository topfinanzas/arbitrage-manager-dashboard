"""
Backup BigQuery Data
Exports all data from the metrics table to a local JSON file.
"""
import os
import json
from datetime import datetime
from google.cloud import bigquery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def backup_data():
    print("🚀 Starting BigQuery data backup...")
    
    # Initialize client
    try:
        client = bigquery.Client()
        project_id = client.project
        dataset_id = os.getenv('BIGQUERY_DATASET', 'arbitrage')
        table_id = 'metrics'
        
        full_table_id = f"{project_id}.{dataset_id}.{table_id}"
        print(f"   Target table: {full_table_id}")
        
        # Query all data
        query = f"SELECT * FROM `{full_table_id}`"
        query_job = client.query(query)
        results = query_job.result()
        
        # Convert to list of dicts
        data = []
        for row in results:
            # Convert row to dict and handle date serialization
            row_dict = dict(row)
            for key, value in row_dict.items():
                if hasattr(value, 'isoformat'):
                    row_dict[key] = value.isoformat()
            data.append(row_dict)
            
        print(f"✅ Fetched {len(data)} records.")
        
        # Create backups directory
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        # Save to JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{backup_dir}/metrics_backup_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"💾 Backup saved to: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

if __name__ == "__main__":
    backup_data()
