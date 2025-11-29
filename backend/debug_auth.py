"""
Debug Auth
Checks the current authenticated identity for Google Cloud.
"""
import os
import google.auth
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

def check_auth():
    print("🔍 Checking Google Cloud Authentication...")
    
    try:
        credentials, project = google.auth.default()
        print(f"✅ Credentials found.")
        print(f"   Project from credentials: {project}")
        
        if hasattr(credentials, 'service_account_email'):
            print(f"   Service Account: {credentials.service_account_email}")
        elif hasattr(credentials, 'signer_email'):
             print(f"   Signer Email: {credentials.signer_email}")
        else:
            print("   User Credentials (ADC) detected.")
            
        # Try to list datasets to verify permissions
        target_project = os.getenv('GCP_PROJECT_ID')
        print(f"   Target Project from .env: {target_project}")
        
        client = bigquery.Client(project=target_project)
        print(f"   Attempting to list datasets in project: {client.project}")
        datasets = list(client.list_datasets())
        print(f"✅ Successfully listed {len(datasets)} datasets.")
        
    except Exception as e:
        print(f"❌ Authentication check failed: {e}")

if __name__ == "__main__":
    check_auth()
