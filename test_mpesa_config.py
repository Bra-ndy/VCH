import os 
from dotenv import load_dotenv 
 
load_dotenv() 
 
print("=" * 50) 
print("M-PESA CONFIGURATION CHECK") 
print("=" * 50) 
 
env_file = '.env' 
if os.path.exists(env_file): 
    print(f"? .env file found") 
else: 
    print(f"? .env file NOT found in {os.getcwd()}") 
 
consumer_key = os.getenv('MPESA_CONSUMER_KEY') 
consumer_secret = os.getenv('MPESA_CONSUMER_SECRET') 
passkey = os.getenv('MPESA_PASSKEY') 
shortcode = os.getenv('MPESA_SHORTCODE') 
callback_url = os.getenv('MPESA_CALLBACK_URL') 
environment = os.getenv('MPESA_ENVIRONMENT') 
 
print(f"\nMPESA_CONSUMER_KEY: {'? Set' if consumer_key and consumer_key != 'your_consumer_key_here' else '? Missing'}") 
if consumer_key and consumer_key != 'your_consumer_key_here': 
    print(f"  Value: {consumer_key[:10]}...") 
 
print(f"MPESA_CONSUMER_SECRET: {'? Set' if consumer_secret and consumer_secret != 'your_consumer_secret_here' else '? Missing'}") 
if consumer_secret and consumer_secret != 'your_consumer_secret_here': 
    print(f"  Value: {consumer_secret[:10]}...") 
 
print(f"MPESA_PASSKEY: {'? Set' if passkey and passkey != 'your_passkey_here' else '? Missing'}") 
if passkey and passkey != 'your_passkey_here': 
    print(f"  Value: {passkey[:10]}...") 
 
print(f"MPESA_SHORTCODE: {shortcode or '? Missing'}") 
print(f"MPESA_CALLBACK_URL: {callback_url or '? Missing'}") 
print(f"MPESA_ENVIRONMENT: {environment or '? Missing (default: sandbox)'}") 
 
print("\n" + "=" * 50) 
print("Please check the output above and tell me what you see.") 
print("=" * 50) 
