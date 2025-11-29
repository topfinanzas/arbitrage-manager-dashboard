"""
Setup New Environment
Initializes the BigQuery dataset and table in the new project.
"""
import os
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, Conflict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_environment():
    print("🚀 Setting up new GCP environment...")
    
    project_id = os.getenv('GCP_PROJECT_ID')
    dataset_id = os.getenv('BIGQUERY_DATASET', 'arbitrage')
    location = os.getenv('GCP_REGION', 'us-central1')
    
    if not project_id:
        print("❌ Error: GCP_PROJECT_ID not found in .env")
        return

    print(f"   Project: {project_id}")
    print(f"   Dataset: {dataset_id}")
    
    client = bigquery.Client(project=project_id, location=location)
    
    # 1. Create Dataset
    dataset_ref = f"{project_id}.{dataset_id}"
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = location
    
    try:
        client.create_dataset(dataset, timeout=30)
        print(f"✅ Created dataset: {dataset_ref}")
    except Conflict:
        print(f"ℹ️  Dataset {dataset_ref} already exists")
    except Exception as e:
        print(f"❌ Failed to create dataset: {e}")
        return

    # 2. Create Table
    table_ref = f"{dataset_ref}.metrics"
    
    # Delete table if exists to ensure schema update
    try:
        client.delete_table(table_ref, not_found_ok=True)
        print(f"🗑️  Deleted existing table {table_ref} to update schema")
    except Exception as e:
        print(f"⚠️  Could not delete table: {e}")

    schema = [
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("campaign_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("campaign_name", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("ad_group_id", "STRING", mode="NULLABLE"), # Mapped from ad_set_id
        bigquery.SchemaField("ad_group_name", "STRING", mode="NULLABLE"), # Mapped from ad_set_name
        bigquery.SchemaField("ad_set_id", "STRING", mode="NULLABLE"), # Keep original field name too
        bigquery.SchemaField("ad_set_name", "STRING", mode="NULLABLE"), # Keep original field name too
        bigquery.SchemaField("ad_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("ad_name", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("market", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("spend", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("impressions", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("clicks", "INTEGER", mode="NULLABLE"), # Generic clicks
        bigquery.SchemaField("link_clicks", "INTEGER", mode="NULLABLE"), # Specific link clicks
        bigquery.SchemaField("revenue", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("sessions", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("searches", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("purchases", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("clicks_paid", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("widget_clicks", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("widget_searches", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("meta_cpc", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("meta_ctr", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("profit", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("roas", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("last_updated", "TIMESTAMP", mode="NULLABLE"),
    ]
    
    table = bigquery.Table(table_ref, schema=schema)
    # Partition by date for performance
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="date"
    )
    
    try:
        client.create_table(table)
        print(f"✅ Created table: {table_ref}")
    except Conflict:
        print(f"ℹ️  Table {table_ref} already exists")
    except Exception as e:
        print(f"❌ Failed to create table: {e}")

if __name__ == "__main__":
    setup_environment()
