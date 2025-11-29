"""
Data Integration Script
Merges Meta Ads cost data with System1 revenue data
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from meta_client import MetaAdsClient
from system1_client import System1Client

load_dotenv()

def merge_campaign_data(date_from=None, date_to=None, system1_csv_path=None):
    """
    Merge Meta Ads and System1 data
    
    Args:
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        system1_csv_path: Path to System1 CSV file
        
    Returns:
        List of merged campaign records
    """
    # Default to yesterday if not specified
    if not date_from or not date_to:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        date_from = date_from or yesterday
        date_to = date_to or yesterday
    
    print(f"📅 Fetching data for: {date_from} to {date_to}")
    print("="*60)
    
    # 1. Fetch Meta Ads data (at Ad Level)
    print("\n1️⃣ Fetching Meta Ads data (Ad Level)...")
    meta_client = MetaAdsClient(
        access_token=os.getenv("META_ACCESS_TOKEN"),
        ad_account_id=os.getenv("META_AD_ACCOUNT_ID")
    )
    
    # Fetch at 'ad' level to get full hierarchy
    meta_data = meta_client.get_adsets_insights(date_from, date_to, level='ad')
    print(f"✅ Fetched {len(meta_data)} ads from Meta")
    
    # 2. Fetch System1 data (at Ad Group/Ad Set Level)
    print("\n2️⃣ Fetching System1 data...")
    system1_client = System1Client()
    
    # Try API first
    if system1_client.has_api:
        system1_data = system1_client.get_revenue_data(date_from, date_to)
    elif system1_csv_path and os.path.exists(system1_csv_path):
        print("⚠️  System1 API not configured. Using CSV fallback.")
        system1_data = system1_client.parse_csv_file(system1_csv_path)
        print(f"✅ Parsed {len(system1_data)} records from System1 CSV")
    else:
        print("⚠️  No System1 API keys or CSV file provided. Revenue will be $0.")
        system1_data = []
    
    # 3. Create lookup dictionary for System1 data
    system1_lookup = {}
    total_system1_raw_revenue = 0.0
    
    for record in system1_data:
        key = (record['ad_group_id'], record['date'])
        system1_lookup[key] = record
        total_system1_raw_revenue += record.get('revenue', 0.0)
        
    print(f"\n💰 Total System1 Raw Revenue (Pre-merge): ${total_system1_raw_revenue:.2f}")
    
    # 4. Merge data and Attribute Revenue
    print("\n3️⃣ Merging data and attributing revenue...")
    merged_data = []
    
    # Group Meta ads by Ad Set and Date to calculate shares
    adset_groups = {}
    for record in meta_data:
        key = (record['ad_set_id'], record['date'])
        if key not in adset_groups:
            adset_groups[key] = {
                'total_clicks': 0,
                'ads': []
            }
        adset_groups[key]['total_clicks'] += record['link_clicks']
        adset_groups[key]['ads'].append(record)
        
    # Process each Ad Set group
    for (ad_set_id, date), group in adset_groups.items():
        # Look up System1 data for this Ad Set
        system1_record = system1_lookup.get((ad_set_id, date), {})
        
        s1_revenue = system1_record.get('revenue', 0.0)
        s1_widget_clicks = system1_record.get('widget_clicks', 0)
        s1_widget_searches = system1_record.get('widget_searches', 0)
        
        total_clicks = group['total_clicks']
        
        # Distribute System1 metrics to ads
        for meta_record in group['ads']:
            link_clicks = meta_record['link_clicks']
            
            # Calculate share of attribution (based on link clicks)
            # If no clicks, use equal share or 0? Using 0 for now to be conservative.
            share = (link_clicks / total_clicks) if total_clicks > 0 else 0.0
            
            # Attribute revenue and widget clicks
            revenue = s1_revenue * share
            widget_clicks = int(s1_widget_clicks * share)
            widget_searches = int(s1_widget_searches * share)
            
            spend = meta_record['spend']
            profit = revenue - spend
            roas = ((revenue / spend) - 1) if spend > 0 else 0.0
            
            widget_ctr = (widget_clicks / link_clicks) if link_clicks > 0 else 0.0
            rpc = (revenue / widget_clicks) if widget_clicks > 0 else 0.0
            
            # Determine market
            ad_set_name = meta_record['ad_set_name']
            market = 'BR' if 'BRA_' in ad_set_name else ('MX' if 'MEX_' in ad_set_name else 'OTHER')
            
            merged_record = {
                'campaign_id': meta_record.get('campaign_id'),
                'campaign_name': meta_record.get('campaign_name'),
                'ad_set_id': ad_set_id,
                'ad_set_name': ad_set_name,
                'ad_id': meta_record.get('ad_id'),
                'ad_name': meta_record.get('ad_name'),
                'market': market,
                'date': date,
                'spend': spend,
                'revenue': revenue,
                'profit': profit,
                'roas': roas,
                'link_clicks': link_clicks,
                'widget_clicks': widget_clicks,
                'widget_searches': widget_searches,
                'searches': meta_record.get('searches', 0),
                'purchases': meta_record.get('purchases', 0),
                'meta_cpc': meta_record['cpc'],
                'meta_ctr': meta_record.get('ctr', 0.0),
                'widget_ctr': widget_ctr,
                'rpc': rpc
            }
            
            merged_data.append(merged_record)
    
    # Track which System1 records were matched
    matched_system1_keys = set(adset_groups.keys())
    
    # 5. Handle System1 orphan revenue (tracking issues like {{adset.id}})
    orphan_count = 0
    orphan_revenue = 0.0
    orphan_widget_clicks = 0
    orphan_widget_searches = 0
    
    # Collect orphan records
    orphan_records = []
    for (ad_group_id, date), system1_record in system1_lookup.items():
        if (ad_group_id, date) not in matched_system1_keys:
            revenue = system1_record.get('revenue', 0.0)
            
            # Check if this is a tracking issue (placeholder or invalid ID)
            is_tracking_issue = (
                ad_group_id in ['{{adset.id}}', '\\N', '', 'null', 'undefined'] or
                not ad_group_id.isdigit()  # Meta IDs are numeric
            )
            
            if revenue > 0 and is_tracking_issue:
                orphan_count += 1
                orphan_revenue += revenue
                orphan_widget_clicks += system1_record.get('widget_clicks', 0)
                orphan_widget_searches += system1_record.get('widget_searches', 0)
                orphan_records.append((date, system1_record))
    
    # Distribute orphan revenue to active ad sets on the same date
    if orphan_revenue > 0:
        print(f"\n⚠️  Found ${orphan_revenue:.2f} orphan revenue from {orphan_count} System1 records")
        print(f"   Distributing proportionally to active ad sets...")
        
        # Group orphans by date
        orphan_by_date = {}
        for date, record in orphan_records:
            if date not in orphan_by_date:
                orphan_by_date[date] = {
                    'revenue': 0.0,
                    'widget_clicks': 0,
                    'widget_searches': 0
                }
            orphan_by_date[date]['revenue'] += record.get('revenue', 0.0)
            orphan_by_date[date]['widget_clicks'] += record.get('widget_clicks', 0)
            orphan_by_date[date]['widget_searches'] += record.get('widget_searches', 0)
        
        # Distribute to merged_data records
        for date, orphan_metrics in orphan_by_date.items():
            # Find all records for this date
            date_records = [r for r in merged_data if r['date'] == date]
            
            if not date_records:
                print(f"   ⚠️  No Meta records for {date}, skipping orphan distribution")
                continue
            
            # Calculate total clicks for this date (for proportional distribution)
            total_clicks = sum(r['link_clicks'] for r in date_records)
            
            if total_clicks == 0:
                # If no clicks, distribute equally
                share_per_record = 1.0 / len(date_records)
                print(f"   📊 {date}: Distributing ${orphan_metrics['revenue']:.2f} equally across {len(date_records)} records")
            else:
                print(f"   📊 {date}: Distributing ${orphan_metrics['revenue']:.2f} by click share ({total_clicks} total clicks)")
            
            # Add orphan revenue to each record proportionally
            for record in date_records:
                if total_clicks > 0:
                    share = record['link_clicks'] / total_clicks
                else:
                    share = share_per_record
                
                # Add proportional revenue
                additional_revenue = orphan_metrics['revenue'] * share
                additional_widget_clicks = int(orphan_metrics['widget_clicks'] * share)
                additional_widget_searches = int(orphan_metrics['widget_searches'] * share)
                
                record['revenue'] += additional_revenue
                record['widget_clicks'] += additional_widget_clicks
                record['widget_searches'] += additional_widget_searches
                
                # Recalculate derived metrics
                record['profit'] = record['revenue'] - record['spend']
                record['roas'] = ((record['revenue'] / record['spend']) - 1) if record['spend'] > 0 else 0.0
                record['widget_ctr'] = (record['widget_clicks'] / record['link_clicks']) if record['link_clicks'] > 0 else 0.0
                record['rpc'] = (record['revenue'] / record['widget_clicks']) if record['widget_clicks'] > 0 else 0.0
    
    # 6. Handle legitimate orphans (real ad set IDs that Meta doesn't have)
    legitimate_orphan_count = 0
    for (ad_group_id, date), system1_record in system1_lookup.items():
        if (ad_group_id, date) not in matched_system1_keys:
            revenue = system1_record.get('revenue', 0.0)
            
            # Check if this is a legitimate orphan (valid ID format but not in Meta)
            is_legitimate = (
                ad_group_id.isdigit() and 
                ad_group_id not in ['{{adset.id}}', '\\N', '', 'null', 'undefined']
            )
            
            if revenue > 0 and is_legitimate:
                legitimate_orphan_count += 1
                widget_clicks = system1_record.get('widget_clicks', 0)
                
                # Create orphan record for legitimate unmatched ad sets
                orphan_record = {
                    'campaign_id': 'UNKNOWN',
                    'campaign_name': 'Unknown Campaign',
                    'ad_set_id': ad_group_id,
                    'ad_set_name': f"[S1 Only] {ad_group_id}",
                    'ad_id': 'UNKNOWN',
                    'ad_name': 'Unknown Ad',
                    'market': 'OTHER',
                    'date': date,
                    'spend': 0.0,
                    'revenue': revenue,
                    'profit': revenue,
                    'roas': 0.0,
                    'link_clicks': 0,
                    'widget_clicks': widget_clicks,
                    'widget_searches': system1_record.get('widget_searches', 0),
                    'searches': 0,
                    'purchases': 0,
                    'meta_cpc': 0.0,
                    'meta_ctr': 0.0,
                    'widget_ctr': 0.0,
                    'rpc': (revenue / widget_clicks) if widget_clicks > 0 else 0.0
                }
                
                merged_data.append(orphan_record)
    
    print(f"\n✅ Merged {len(meta_data)} Meta records")
    if orphan_revenue > 0:
        print(f"💰 Distributed ${orphan_revenue:.2f} orphan revenue (tracking issues)")
    if legitimate_orphan_count > 0:
        print(f"📋 Added {legitimate_orphan_count} legitimate orphan records (ad sets not in Meta)")
    print(f"📊 Total merged records: {len(merged_data)}")
    
    return merged_data


def print_summary(merged_data):
    """Print summary statistics"""
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    total_spend = sum(r['spend'] for r in merged_data)
    total_revenue = sum(r['revenue'] for r in merged_data)
    total_profit = total_revenue - total_spend
    avg_roas = (total_revenue / total_spend) if total_spend > 0 else 0.0
    
    print(f"\n💰 Financial Metrics:")
    print(f"   Total Spend:    ${total_spend:,.2f}")
    print(f"   Total Revenue:  ${total_revenue:,.2f}")
    print(f"   Total Profit:   ${total_profit:,.2f}")
    print(f"   Avg ROAS:       {avg_roas:.2f}x")
    
    # Top 5 by ROAS
    sorted_by_roas = sorted(merged_data, key=lambda x: x['roas'], reverse=True)
    print(f"\n🏆 Top 5 Campaigns by ROAS:")
    for i, record in enumerate(sorted_by_roas[:5], 1):
        print(f"   {i}. {record['ad_set_name'][:40]}")
        print(f"      ROAS: {record['roas']:.2f}x | Spend: ${record['spend']:.2f} | Revenue: ${record['revenue']:.2f}")
    
    # Bottom 5 by ROAS
    print(f"\n⚠️  Bottom 5 Campaigns by ROAS:")
    for i, record in enumerate(sorted_by_roas[-5:], 1):
        print(f"   {i}. {record['ad_set_name'][:40]}")
        print(f"      ROAS: {record['roas']:.2f}x | Spend: ${record['spend']:.2f} | Revenue: ${record['revenue']:.2f}")


def ingest_to_bigquery(merged_data, reset_table=False):
    """
    Ingest merged data into BigQuery
    """
    from google.cloud import bigquery
    import time
    
    client = bigquery.Client(project=os.getenv('GCP_PROJECT_ID'))
    dataset = os.getenv('BIGQUERY_DATASET', 'arbitrage')
    table_id = f"{client.project}.{dataset}.metrics"

    if reset_table:
        print(f"\n🗑️  Resetting table {table_id}...")
        create_table_sql = f"""
        CREATE OR REPLACE TABLE `{table_id}` (
            campaign_id STRING,
            campaign_name STRING,
            ad_set_id STRING NOT NULL,
            ad_set_name STRING,
            ad_id STRING,
            ad_name STRING,
            market STRING,
            date DATE NOT NULL,
            spend FLOAT64,
            link_clicks INT64,
            meta_cpc FLOAT64,
            meta_ctr FLOAT64,
            searches INT64,
            purchases INT64,
            revenue FLOAT64,
            widget_clicks INT64,
            widget_searches INT64,
            profit FLOAT64,
            roas FLOAT64
        )
        PARTITION BY date
        """
        client.query(create_table_sql).result()
        print("✅ Table recreated successfully.")
        time.sleep(5)  # Wait for propagation

    if not merged_data:
        print("⚠️  No data to ingest.")
        return

    print(f"\n4️⃣ Ingesting {len(merged_data)} records to BigQuery...")
    
    # Batch inserts
    batch_size = 50
    inserted_count = 0
    
    for i in range(0, len(merged_data), batch_size):
        batch = merged_data[i:i+batch_size]
        values = []
        for row in batch:
            # Format values for SQL - escape single quotes and backslashes
            campaign_id = str(row.get('campaign_id', '')).replace('\\', '\\\\').replace("'", "\\'")
            campaign_name = str(row.get('campaign_name', '')).replace('\\', '\\\\').replace("'", "\\'")
            ad_set_id = str(row['ad_set_id']).replace('\\', '\\\\').replace("'", "\\'")
            ad_set_name = str(row['ad_set_name']).replace('\\', '\\\\').replace("'", "\\'")
            ad_id = str(row.get('ad_id', '')).replace('\\', '\\\\').replace("'", "\\'")
            ad_name = str(row.get('ad_name', '')).replace('\\', '\\\\').replace("'", "\\'")
            market = str(row['market']).replace("'", "\\'")
            
            val = (
                f"'{campaign_id}'",
                f"'{campaign_name}'",
                f"'{ad_set_id}'",
                f"'{ad_set_name}'",
                f"'{ad_id}'",
                f"'{ad_name}'",
                f"'{market}'",
                f"'{row['date']}'",
                str(row['spend']),
                str(row['link_clicks']),
                str(row['meta_cpc']),
                str(row.get('meta_ctr', 0.0)), 
                str(row.get('searches', 0)),
                str(row.get('purchases', 0)),
                str(row['revenue']),
                str(row['widget_clicks']),
                str(row.get('widget_searches', 0)),
                str(row['profit']),
                str(row['roas'])
            )
            values.append(f"({','.join(val)})")
        
        insert_sql = f"""
        INSERT INTO `{table_id}` 
        (campaign_id, campaign_name, ad_set_id, ad_set_name, ad_id, ad_name, market, date, spend, link_clicks, meta_cpc, meta_ctr, searches, purchases, revenue, widget_clicks, widget_searches, profit, roas)
        VALUES {','.join(values)}
        """
        
        try:
            client.query(insert_sql).result()
            inserted_count += len(batch)
            print(f"  Inserted batch {i//batch_size + 1} ({len(batch)} rows)...")
        except Exception as e:
            print(f"❌ Error inserting batch {i//batch_size + 1}: {e}")
            
    print(f"✅ Successfully ingested {inserted_count} records.")


if __name__ == "__main__":
    # Example usage
    print("🚀 Arbitrage Data Integration")
    print("="*60)
    
    # Path to your System1 CSV file
    system1_csv = "../../Reportes_25.11.25/syndication_rsoc_online_ad_widget_hourly.202511252108.35zFHqblPPXnIRz2MDAvz16xDma.csv"
    
    # Merge data for last 7 days
    date_to = datetime.now().strftime('%Y-%m-%d')
    date_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # If today is included, System1 might not have data yet, but we'll try
    # The script handles missing System1 data gracefully now
    
    print(f"📅 Fetching data from {date_from} to {date_to}")
    
    merged_data = merge_campaign_data(
        date_from=date_from,
        date_to=date_to,
        system1_csv_path=system1_csv
    )
    
    # Print summary
    print_summary(merged_data)
    
    # Ingest to BigQuery (Resetting table to remove synthetic data)
    ingest_to_bigquery(merged_data, reset_table=True)
    
    print("\n✅ Integration test complete!")
