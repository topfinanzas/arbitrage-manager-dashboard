import random
from datetime import datetime, timedelta
from google.cloud import bigquery
import os
from dotenv import load_dotenv

load_dotenv()

def generate_data():
    client = bigquery.Client()
    dataset = os.getenv('BIGQUERY_DATASET', 'arbitrage')
    table_id = f"{client.project}.{dataset}.metrics"

    print(f"Generating data for table: {table_id}")

    rows_to_insert = []
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=60)
    
    markets = ['BR', 'MX', 'US', 'DE']
    campaigns = [f"Campaign_{i}" for i in range(1, 11)]

    # Use SQL DDL to recreate table atomically
    print("Recreating table using DDL...")
    
    create_table_sql = f"""
    CREATE OR REPLACE TABLE `{table_id}` (
        ad_set_id STRING NOT NULL,
        ad_set_name STRING,
        market STRING,
        date DATE NOT NULL,
        spend FLOAT64,
        link_clicks INT64,
        meta_cpc FLOAT64,
        meta_ctr FLOAT64,
        revenue FLOAT64,
        widget_clicks INT64,
        widget_searches INT64,
        profit FLOAT64,
        roas FLOAT64
    )
    PARTITION BY date
    """
    
    client.query(create_table_sql).result()
    print("✅ Table recreated successfully (DDL).")
    
    # Small delay to ensure metadata is ready for streaming API
    import time
    time.sleep(5)

    current_date = start_date
    while current_date <= end_date:
        for campaign in campaigns:
            market = random.choice(markets)
            spend = round(random.uniform(50, 500), 2)
            roas = random.uniform(0.5, 2.5)
            revenue = round(spend * roas, 2)
            profit = round(revenue - spend, 2)
            link_clicks = int(spend / random.uniform(0.1, 0.5))
            meta_cpc = round(spend / link_clicks, 2) if link_clicks > 0 else 0
            widget_clicks = int(link_clicks * random.uniform(0.2, 0.4))
            
            row = {
                "ad_set_id": f"id_{campaign}_{market}",
                "ad_set_name": campaign,
                "market": market,
                "date": current_date.isoformat(),
                "spend": spend,
                "link_clicks": link_clicks,
                "meta_cpc": meta_cpc,
                "meta_ctr": round(random.uniform(1.5, 4.0), 2),
                "revenue": revenue,
                "profit": profit,
                "roas": roas,
                "widget_clicks": widget_clicks,
                "widget_searches": int(widget_clicks * 1.2)
            }
            rows_to_insert.append(row)
        
        current_date += timedelta(days=1)

    # Use SQL INSERT instead of streaming API to avoid "Table not found" errors
    print(f"Inserting {len(rows_to_insert)} rows using SQL...")
    
    # Batch inserts to avoid query size limits (e.g., 50 rows per batch)
    batch_size = 50
    for i in range(0, len(rows_to_insert), batch_size):
        batch = rows_to_insert[i:i+batch_size]
        values = []
        for row in batch:
            # Format values for SQL
            val = (
                f"'{row['ad_set_id']}'",
                f"'{row['ad_set_name']}'",
                f"'{row['market']}'",
                f"'{row['date']}'",
                str(row['spend']),
                str(row['link_clicks']),
                str(row['meta_cpc']),
                str(row['meta_ctr']),
                str(row['revenue']),
                str(row['widget_clicks']),
                str(row['widget_searches']),
                str(row['profit']),
                str(row['roas'])
            )
            values.append(f"({','.join(val)})")
        
        insert_sql = f"""
        INSERT INTO `{table_id}` 
        (ad_set_id, ad_set_name, market, date, spend, link_clicks, meta_cpc, meta_ctr, revenue, widget_clicks, widget_searches, profit, roas)
        VALUES {','.join(values)}
        """
        
        try:
            client.query(insert_sql).result()
            print(f"  Inserted batch {i//batch_size + 1}...")
        except Exception as e:
            print(f"❌ Error inserting batch {i//batch_size + 1}: {e}")
            
    print("✅ Data generation complete.")

if __name__ == "__main__":
    generate_data()
