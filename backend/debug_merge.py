"""
Debug script to see which System1 ad groups are not matching Meta ad sets
"""
from meta_client import MetaAdsClient
from system1_client import System1Client
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Fetch yesterday's data
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

print(f"🔍 Analyzing data for {yesterday}\n")

# 1. Fetch Meta data
meta_client = MetaAdsClient(
    os.getenv('META_ACCESS_TOKEN'),
    os.getenv('META_AD_ACCOUNT_ID')
)
meta_data = meta_client.get_adsets_insights(yesterday, yesterday)
meta_adset_ids = set(item['ad_set_id'] for item in meta_data)

print(f"📱 Meta Ad Sets: {len(meta_adset_ids)}")
for adset_id in sorted(meta_adset_ids):
    print(f"   - {adset_id}")

# 2. Fetch System1 data
system1_client = System1Client()
system1_data = system1_client.get_revenue_data(yesterday, yesterday)

# Group by ad_group_id
from collections import defaultdict
system1_by_adgroup = defaultdict(float)
for record in system1_data:
    system1_by_adgroup[record['ad_group_id']] += record['revenue']

print(f"\n💰 System1 Ad Groups: {len(system1_by_adgroup)}")
for adgroup_id, revenue in sorted(system1_by_adgroup.items(), key=lambda x: -x[1]):
    match = "✅" if adgroup_id in meta_adset_ids else "❌"
    print(f"   {match} {adgroup_id}: ${revenue:.2f}")

# Summary
matched_revenue = sum(rev for aid, rev in system1_by_adgroup.items() if aid in meta_adset_ids)
unmatched_revenue = sum(rev for aid, rev in system1_by_adgroup.items() if aid not in meta_adset_ids)

print(f"\n📊 Revenue Breakdown:")
print(f"   ✅ Matched (will appear in dashboard): ${matched_revenue:.2f}")
print(f"   ❌ Unmatched (lost in merge): ${unmatched_revenue:.2f}")
print(f"   📈 Total System1: ${matched_revenue + unmatched_revenue:.2f}")
