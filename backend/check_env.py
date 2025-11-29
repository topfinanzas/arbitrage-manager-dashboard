import os
from dotenv import load_dotenv

load_dotenv()
print(f"GCP_PROJECT_ID: {os.getenv('GCP_PROJECT_ID')}")
