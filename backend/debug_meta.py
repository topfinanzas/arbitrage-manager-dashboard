"""
Analyze if we can match System1 data to Meta data by other means
"""
import os
from dotenv import load_dotenv
from meta_client import MetaAdsClient

load_dotenv()

print("🔍 Fetching Meta Ads data for 2025-11-27...")
print("="*80)

meta_client = MetaAdsClient(
    access_token=os.getenv("META_ACCESS_TOKEN"),
    ad_account_id=os.getenv("META_AD_ACCOUNT_ID")
)

meta_data = meta_client.get_adsets_insights('2025-11-27', '2025-11-27', level='ad')

print(f"\n📊 Meta Ads ({len(meta_data)} ads):\n")
print(f"{'Campaign ID':<20} {'Ad Set ID':<20} {'Ad ID':<20} {'Ad Set Name':<40}")
print("-"*120)

for record in meta_data:
    print(f"{record.get('campaign_id', 'N/A'):<20} {record.get('ad_set_id', 'N/A'):<20} {record.get('ad_id', 'N/A'):<20} {record.get('ad_set_name', 'N/A'):<40}")

print("\n" + "="*80)
print(f"\n💡 Analysis:")
print(f"   - Total Meta ads: {len(meta_data)}")
print(f"   - Unique Ad Sets: {len(set(r['ad_set_id'] for r in meta_data))}")
print(f"   - Unique Campaigns: {len(set(r.get('campaign_id') for r in meta_data if r.get('campaign_id')))}")

# Show unique ad set IDs
unique_adsets = set(r['ad_set_id'] for r in meta_data)
print(f"\n📋 Unique Ad Set IDs from Meta:")
for adset_id in sorted(unique_adsets):
    print(f"   - {adset_id}")
