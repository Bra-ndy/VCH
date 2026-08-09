import requests 
import base64 
import os 
from dotenv import load_dotenv 
 
load_dotenv() 
 
print("=" * 50) 
print("TESTING M-PESA API CONNECTION") 
print("=" * 50) 
 
consumer_key = os.getenv('MPESA_CONSUMER_KEY') 
consumer_secret = os.getenv('MPESA_CONSUMER_SECRET') 
environment = os.getenv('MPESA_ENVIRONMENT', 'sandbox') 
 
print(f"Environment: {environment}") 
 
if environment == 'sandbox': 
    base_url = 'https://sandbox.safaricom.co.ke' 
else: 
    base_url = 'https://api.safaricom.co.ke' 
 
print(f"Base URL: {base_url}") 
 
try: 
    url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials" 
    auth_string = f"{consumer_key}:{consumer_secret}" 
    auth_bytes = auth_string.encode('ascii') 
    auth_base64 = base64.b64encode(auth_bytes).decode('ascii') 
    headers = {'Authorization': f'Basic {auth_base64}'} 
    print(f"\nRequest URL: {url}") 
    print(f"Authorization: Basic {auth_base64[:20]}...") 
    response = requests.get(url, headers=headers, timeout=30) 
    print(f"\nResponse Status Code: {response.status_code}") 
    if response.status_code == 200: 
        data = response.json() 
        access_token = data.get('access_token') 
        expires_in = data.get('expires_in') 
        print("\n? SUCCESS! Access token obtained:") 
        print(f"  Access Token: {access_token[:20]}...") 
        print(f"  Expires In: {expires_in} seconds") 
        print(f"  Full Response: {data}") 
    else: 
        print(f"\n? FAILED! Error response:") 
        print(f"  Status: {response.status_code}") 
        print(f"  Response: {response.text}") 
except Exception as e: 
    print(f"\n? ERROR: {e}") 
    import traceback 
    traceback.print_exc() 
 
print("\n" + "=" * 50) 
print("Tell me what you see in the output above.") 
print("=" * 50) 
