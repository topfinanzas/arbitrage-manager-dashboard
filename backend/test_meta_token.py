"""
Test Meta API token and permissions
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID")

print("🔍 Testing Meta API Connection...")
print(f"Ad Account ID: {AD_ACCOUNT_ID}")
print(f"Token (first 20 chars): {ACCESS_TOKEN[:20]}...")

# Test 1: Verify token is valid
print("\n1️⃣ Testing token validity...")
url = "https://graph.facebook.com/v21.0/me"
params = {'access_token': ACCESS_TOKEN}

try:
    response = requests.get(url, params=params)
    response.raise_for_status()
    user_data = response.json()
    print(f"✅ Token is valid! User: {user_data.get('name', 'Unknown')}")
except Exception as e:
    print(f"❌ Token validation failed: {e}")
    exit(1)

# Test 2: Check token permissions
print("\n2️⃣ Checking token permissions...")
url = "https://graph.facebook.com/v21.0/me/permissions"
params = {'access_token': ACCESS_TOKEN}

try:
    response = requests.get(url, params=params)
    response.raise_for_status()
    permissions = response.json()
    
    granted_perms = [p['permission'] for p in permissions.get('data', []) if p.get('status') == 'granted']
    print(f"✅ Granted permissions: {', '.join(granted_perms)}")
    
    required = ['ads_read', 'ads_management']
    missing = [p for p in required if p not in granted_perms]
    
    if missing:
        print(f"⚠️  Missing permissions: {', '.join(missing)}")
        print("   You need to re-generate the token with these permissions.")
    else:
        print("✅ All required permissions are granted!")
        
except Exception as e:
    print(f"❌ Permission check failed: {e}")

# Test 3: List accessible ad accounts
print("\n3️⃣ Listing accessible ad accounts...")
url = "https://graph.facebook.com/v21.0/me/adaccounts"
params = {
    'access_token': ACCESS_TOKEN,
    'fields': 'id,name,account_status'
}

try:
    response = requests.get(url, params=params)
    response.raise_for_status()
    accounts = response.json()
    
    if accounts.get('data'):
        print(f"✅ Found {len(accounts['data'])} accessible ad account(s):")
        for acc in accounts['data']:
            acc_id = acc['id'].replace('act_', '')
            status = acc.get('account_status', 'unknown')
            print(f"   - {acc.get('name')} (ID: {acc_id}, Status: {status})")
            
            if acc_id == AD_ACCOUNT_ID:
                print(f"   ✅ This matches your configured account!")
    else:
        print("❌ No ad accounts accessible with this token")
        print("   Make sure the token has access to the ad account.")
        
except Exception as e:
    print(f"❌ Ad account listing failed: {e}")

print("\n" + "="*60)
print("SUMMARY:")
print("="*60)
print(f"Configured Ad Account: {AD_ACCOUNT_ID}")
print("\nIf your account is NOT in the list above, you need to:")
print("1. Make sure you're logged in with the correct Facebook account")
print("2. Re-generate the token while selecting the correct ad account")
print("3. Or ask the ad account owner to grant you access")
