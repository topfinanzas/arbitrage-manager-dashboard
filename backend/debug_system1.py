"""
Debug System1 data to see what ad_group_ids it's reporting
"""
import os
from dotenv import load_dotenv
from system1_client import System1Client
from datetime import datetime

load_dotenv()

system1_client = System1Client()

print("🔍 Fetching System1 data for 2025-11-27...")
print("="*80)

if system1_client.has_api:
    system1_data = system1_client.get_revenue_data('2025-11-27', '2025-11-27')
    
    print(f"\n📊 System1 Records ({len(system1_data)} total):\n")
    print(f"{'Ad Group ID':<25} {'Date':<12} {'Revenue':>10} {'Widget Clicks':>15}")
    print("-"*80)
    
    for record in system1_data:
        print(f"{record['ad_group_id']:<25} {record['date']:<12} ${record['revenue']:>9.2f} {record['widget_clicks']:>15}")
    
    print("\n" + "="*80)
    print(f"\n💰 Total Revenue: ${sum(r['revenue'] for r in system1_data):.2f}")
else:
    print("⚠️  System1 API not configured")
