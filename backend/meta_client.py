"""
Meta Ads API Integration
Fetches campaign data from Meta Marketing API
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class MetaAdsClient:
    """Client for Meta Marketing API"""
    
    BASE_URL = "https://graph.facebook.com/v21.0"
    
    def __init__(self, access_token: str, ad_account_id: str):
        """
        Initialize Meta Ads client
        
        Args:
            access_token: Meta API access token
            ad_account_id: Ad account ID (without 'act_' prefix)
        """
        self.access_token = access_token
        self.ad_account_id = ad_account_id
        self.account_url = f"{self.BASE_URL}/act_{ad_account_id}"
    
    def get_adsets_insights(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        time_increment: int = 1,
        level: str = 'ad'  # Changed default to 'ad' to get full hierarchy
    ) -> List[Dict]:
        """
        Fetch insights (metrics) at specified level
        
        Args:
            date_from: Start date (YYYY-MM-DD). Defaults to yesterday
            date_to: End date (YYYY-MM-DD). Defaults to yesterday
            time_increment: 1 for daily, 'all_days' for total
            level: 'campaign', 'adset', or 'ad'
            
        Returns:
            List of metrics
        """
        # Default to yesterday if not specified
        if not date_from or not date_to:
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            date_from = date_from or yesterday
            date_to = date_to or yesterday
        
        url = f"{self.account_url}/insights"
        
        fields = [
            'campaign_id',
            'campaign_name',
            'adset_id',
            'adset_name',
            'spend',
            'clicks',
            'cpc',
            'ctr',
            'actions',
            'action_values'
        ]
        
        if level == 'ad':
            fields.extend(['ad_id', 'ad_name'])
        
        params = {
            'access_token': self.access_token,
            'level': level,
            'fields': ','.join(fields),
            'time_range': f'{{"since":"{date_from}","until":"{date_to}"}}',
            'time_increment': time_increment,
            'limit': 500
        }
        
        all_data = []
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            all_data.extend(data.get('data', []))
            
            # Handle pagination
            while 'paging' in data and 'next' in data['paging']:
                response = requests.get(data['paging']['next'])
                response.raise_for_status()
                data = response.json()
                all_data.extend(data.get('data', []))
            
            return self._transform_insights(all_data)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching Meta Ads data: {e}")
            if hasattr(e.response, 'text'):
                print(f"   Response: {e.response.text}")
            return []
    
    def _transform_insights(self, raw_data: List[Dict]) -> List[Dict]:
        """
        Transform raw Meta API response to our schema
        
        Args:
            raw_data: Raw API response
            
        Returns:
            Transformed data
        """
        transformed = []
        
        for item in raw_data:
            # Extract actions (purchases, searches, etc.)
            actions = item.get('actions', [])
            purchases = self._extract_action_value(actions, 'omni_purchase')
            searches = self._extract_action_value(actions, 'search')
            
            transformed_item = {
                'campaign_id': item.get('campaign_id'),
                'campaign_name': item.get('campaign_name'),
                'ad_set_id': item.get('adset_id'),
                'ad_set_name': item.get('adset_name'),
                'ad_id': item.get('ad_id'),      # Will be None if level != 'ad'
                'ad_name': item.get('ad_name'),  # Will be None if level != 'ad'
                'date': item.get('date_start'),
                'spend': float(item.get('spend', 0)),
                'link_clicks': int(item.get('clicks', 0)),
                'cpc': float(item.get('cpc', 0)),
                'ctr': float(item.get('ctr', 0)),
                'purchases': purchases,
                'searches': searches
            }
            
            transformed.append(transformed_item)
        
        return transformed
    
    def _extract_action_value(self, actions: List[Dict], action_type: str) -> int:
        """Extract specific action count from actions array"""
        for action in actions:
            if action.get('action_type') == action_type:
                return int(action.get('value', 0))
        return 0
    
    def pause_adset(self, adset_id: str) -> bool:
        """
        Pause an ad set
        
        Args:
            adset_id: Ad set ID to pause
            
        Returns:
            True if successful
        """
        url = f"{self.BASE_URL}/{adset_id}"
        
        params = {
            'access_token': self.access_token,
            'status': 'PAUSED'
        }
        
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error pausing ad set {adset_id}: {e}")
            return False
    
    def update_adset_budget(self, adset_id: str, daily_budget: float) -> bool:
        """
        Update ad set daily budget
        
        Args:
            adset_id: Ad set ID
            daily_budget: New daily budget in cents (e.g., 5000 = $50)
            
        Returns:
            True if successful
        """
        url = f"{self.BASE_URL}/{adset_id}"
        
        params = {
            'access_token': self.access_token,
            'daily_budget': int(daily_budget * 100)  # Convert to cents
        }
        
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error updating budget for {adset_id}: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Load from environment variables
    ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
    AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID")
    
    if not ACCESS_TOKEN or not AD_ACCOUNT_ID:
        print("⚠️  Please set META_ACCESS_TOKEN and META_AD_ACCOUNT_ID environment variables")
    else:
        client = MetaAdsClient(ACCESS_TOKEN, AD_ACCOUNT_ID)
        
        # Fetch yesterday's data
        insights = client.get_adsets_insights()
        
        print(f"✅ Fetched {len(insights)} ad sets")
        for insight in insights[:3]:  # Print first 3
            print(f"  - {insight['ad_set_name']}: ${insight['spend']:.2f}")
