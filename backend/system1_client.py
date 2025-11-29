"""
System1 Data Client
Handles data extraction from System1 platform
"""
import csv
import os
from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict
import requests

class System1Client:
    """Client for System1 revenue data"""
    
    def __init__(self, api_keys: Optional[List[str]] = None, api_url: Optional[str] = None):
        """
        Initialize System1 client
        
        Args:
            api_keys: List of System1 API keys (for multiple portals)
            api_url: System1 API base URL
        """
        self.api_url = api_url or os.getenv("SYSTEM1_API_URL")
        
        # Load API keys from environment if not provided
        if not api_keys:
            api_keys = []
            key1 = os.getenv("SYSTEM1_API_KEY_1")
            key2 = os.getenv("SYSTEM1_API_KEY_2")
            if key1:
                api_keys.append(key1)
            if key2:
                api_keys.append(key2)
        
        self.api_keys = api_keys
        self.has_api = bool(self.api_keys and self.api_url)

    
    def get_revenue_data(
        self,
        date_from: str,
        date_to: str
    ) -> List[Dict]:
        """
        Fetch revenue data from System1 (all portals)
        
        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            
        Returns:
            List of revenue records (combined from all portals)
        """
        if self.has_api:
            all_data = []
            for i, api_key in enumerate(self.api_keys, 1):
                portal_name = os.getenv(f"SYSTEM1_PORTAL_{i}_NAME", f"Portal {i}")
                print(f"\n📊 Fetching data from {portal_name}...")
                data = self._fetch_from_api(date_from, date_to, api_key)
                
                # Calculate portal stats
                portal_revenue = sum(r['revenue'] for r in data)
                print(f"   ✅ {portal_name}: {len(data)} records | ${portal_revenue:.2f}")
                
                all_data.extend(data)
            
            print(f"\n✅ Total records from all portals: {len(all_data)}")
            return all_data
        else:
            # Fallback: Manual CSV upload
            print("⚠️  System1 API not configured. Use parse_csv_file() method instead.")
            return []
    
    def _fetch_from_api(self, date_from: str, date_to: str, api_key: str) -> List[Dict]:
        """
        Fetch data from System1 API using async report system
        
        System1 API workflow:
        1. Request report → get report_id
        2. Poll status endpoint until ready
        3. Download report data
        
        Args:
            date_from: Start date
            date_to: End date
            api_key: API key for this specific portal
        """
        import time
        from datetime import datetime
        
        # Calculate days between dates
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        days = (date_to_obj - date_from_obj).days + 1
        
        # Step 1: Request report
        print(f"📊 Requesting System1 report for {days} days ending {date_to}...")
        
        report_url = f"{self.api_url}/partner/v1/report"
        params = {
            'report_type': 'syndication_rsoc_online_ad_widget_daily',
            'days': days,
            'date': date_to,
            'auth_key': api_key
        }
        
        try:
            response = requests.post(report_url, params=params)
            response.raise_for_status()
            report_data = response.json()
            report_id = report_data.get('report_id')
            
            if not report_id:
                print("❌ No report_id received from System1")
                return []
            
            print(f"✅ Report requested. ID: {report_id}")
            
            # Step 2: Poll status endpoint
            status_url = f"{self.api_url}/partner/v1/report/{report_id}/status"
            max_attempts = 20  # 10 minutes max (30s * 20)
            attempt = 0
            
            while attempt < max_attempts:
                attempt += 1
                print(f"⏳ Checking report status (attempt {attempt}/{max_attempts})...")
                
                time.sleep(30)  # Wait 30 seconds between checks
                
                status_response = requests.get(status_url, params={'auth_key': api_key})
                status_response.raise_for_status()
                status_data = status_response.json()
                
                report_status = status_data.get('report_status')
                
                if report_status == 'SUCCESS':
                    print("✅ Report ready!")
                    content_url = status_data.get('content_url')
                    if content_url:
                        # content_url might be relative or absolute
                        if content_url.startswith('http'):
                            download_url = content_url
                        else:
                            download_url = f"{self.api_url}{content_url}"
                            
                        print(f"⬇️  Fetching content from: {download_url}")
                        data_response = requests.get(download_url)
                        data_response.raise_for_status()
                        
                        content = data_response.content
                        
                        # Check if response is HTML (as per docs)
                        if b'<html' in content.lower() or b'<!doctype html' in content.lower():
                            print("📄 Received HTML content, extracting download link...")
                            import re
                            # Try to find href in anchor tag
                            html_str = content.decode('utf-8', errors='ignore')
                            match = re.search(r'href=["\'](.*?)["\']', html_str)
                            if match:
                                file_url = match.group(1)
                                # Handle relative URL in HTML
                                if not file_url.startswith('http'):
                                    # If relative, it might be relative to the download_url or base_url
                                    # Usually these are S3 links or similar, so likely absolute.
                                    # If relative, let's try prepending base URL
                                    file_url = f"{self.api_url}{file_url}"
                                    
                                print(f"🔗 Found actual file URL: {file_url}")
                                file_response = requests.get(file_url)
                                file_response.raise_for_status()
                                content = file_response.content
                            else:
                                print("❌ Could not find download link in HTML response")
                                return []

                        # Check if response is gzip compressed
                        if content[:2] == b'\x1f\x8b':  # gzip magic number
                            import gzip
                            content = gzip.decompress(content)
                            csv_text = content.decode('utf-8')
                        else:
                            csv_text = content.decode('utf-8', errors='replace')
                        
                        # Parse CSV data
                        return self._parse_api_csv_response(csv_text)
                    else:
                        print("❌ No content_url in response")
                        return []
                
                elif report_status == 'FAILED':
                    print(f"❌ Report generation failed")
                    return []
                
                elif report_status in ['PENDING', 'RUNNING']:
                    print(f"   Status: {report_status}... waiting...")
                    continue
                else:
                    print(f"⚠️  Unknown status: {report_status}")
            
            print("❌ Timeout waiting for report")
            return []
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching System1 data: {e}")
            return []
    
    def _parse_api_csv_response(self, csv_text: str) -> List[Dict]:
        """Parse CSV response from System1 API"""
        import csv
        from io import StringIO
        
        hourly_data = []
        reader = csv.DictReader(StringIO(csv_text))
        
        for row in reader:
            hourly_data.append({
                'ad_group_id': row.get('ADGROUP ID', '').strip(),
                'date': row.get('DATA DATE'),
                'hour': int(row.get('DATA HOUR', 0)),
                'revenue': float(row.get('PARTNER NET REVENUE', 0)),
                'widget_clicks': int(row.get('SELLSIDE CLICKS NETWORK', 0)),
                'widget_searches': int(row.get('WIDGET SEARCHES', 0))
            })
        
        return self._aggregate_hourly_data(hourly_data)

    
    def parse_csv_file(self, file_path: str) -> List[Dict]:
        """
        Parse System1 CSV file (hourly data)
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            List of aggregated revenue records (by ad group and date)
        """
        hourly_data = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    hourly_data.append({
                        'ad_group_id': row.get('ADGROUP ID', '').strip(),
                        'date': row.get('DATA DATE'),
                        'hour': int(row.get('DATA HOUR', 0)),
                        'revenue': float(row.get('PARTNER NET REVENUE', 0)),
                        'widget_clicks': int(row.get('SELLSIDE CLICKS NETWORK', 0)),
                        'widget_searches': int(row.get('WIDGET SEARCHES', 0))
                    })
        except Exception as e:
            print(f"❌ Error parsing CSV: {e}")
            return []
        
        # Aggregate by ad_group_id and date
        return self._aggregate_hourly_data(hourly_data)
    
    def _aggregate_hourly_data(self, hourly_data: List[Dict]) -> List[Dict]:
        """
        Aggregate hourly data to daily level
        
        Args:
            hourly_data: List of hourly records
            
        Returns:
            List of daily aggregated records
        """
        # Group by (ad_group_id, date)
        aggregated = defaultdict(lambda: {
            'revenue': 0.0,
            'widget_clicks': 0,
            'widget_searches': 0
        })
        
        for record in hourly_data:
            key = (record['ad_group_id'], record['date'])
            aggregated[key]['revenue'] += record['revenue']
            aggregated[key]['widget_clicks'] += record['widget_clicks']
            aggregated[key]['widget_searches'] += record['widget_searches']
        
        # Convert to list
        result = []
        for (ad_group_id, date), metrics in aggregated.items():
            result.append({
                'ad_group_id': ad_group_id,
                'date': date,
                'revenue': metrics['revenue'],
                'widget_clicks': metrics['widget_clicks'],
                'widget_searches': metrics['widget_searches']
            })
        
        return result


# Example usage
if __name__ == "__main__":
    client = System1Client()
    
    # Example: Parse CSV file
    csv_path = "../../Reportes_25.11.25/syndication_rsoc_online_ad_widget_hourly.202511252108.35zFHqblPPXnIRz2MDAvz16xDma.csv"
    
    data = client.parse_csv_file(csv_path)
    
    print(f"✅ Parsed {len(data)} daily records")
    for record in data[:3]:
        print(f"  - Ad Group {record['ad_group_id']} ({record['date']}): ${record['revenue']:.2f}")
