"""
Test System1 API connection with both portals
"""
from dotenv import load_dotenv
load_dotenv()

from system1_client import System1Client
from datetime import datetime, timedelta

print("🧪 Testing System1 API Integration")
print("="*60)

# Initialize client (will load API keys from .env)
client = System1Client()

print(f"\n📋 Configuration:")
print(f"   API URL: {client.api_url}")
print(f"   Number of API keys: {len(client.api_keys)}")
print(f"   Has API: {client.has_api}")

if not client.has_api:
    print("\n❌ System1 API not configured properly")
    print("   Check your .env file")
    exit(1)

# Test with last 7 days
date_to = datetime.now().strftime('%Y-%m-%d')
date_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

print(f"\n📅 Requesting data for: {date_from} to {date_to}")
print("="*60)

try:
    data = client.get_revenue_data(date_from, date_to)
    
    if data:
        print(f"\n✅ SUCCESS! Retrieved {len(data)} records")
        
        # Show summary
        total_revenue = sum(r['revenue'] for r in data)
        total_clicks = sum(r['widget_clicks'] for r in data)
        
        print(f"\n📊 Summary:")
        print(f"   Total Revenue: ${total_revenue:.2f}")
        print(f"   Total Widget Clicks: {total_clicks:,}")
        
        # Show top 5 by revenue
        sorted_data = sorted(data, key=lambda x: x['revenue'], reverse=True)
        print(f"\n🏆 Top 5 Ad Groups by Revenue:")
        for i, record in enumerate(sorted_data[:5], 1):
            print(f"   {i}. Ad Group {record['ad_group_id']} ({record['date']}): ${record['revenue']:.2f}")
    else:
        print("\n⚠️  No data returned")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
