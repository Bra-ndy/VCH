import os 
import sys 
import logging 
from dotenv import load_dotenv 
 
logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__) 
 
load_dotenv() 
 
print("=" * 50) 
print("TESTING STK PUSH DIRECTLY") 
print("=" * 50) 
 
try: 
    from flask import Flask 
    app = Flask(__name__) 
    app.config['MPESA_CONSUMER_KEY'] = os.getenv('MPESA_CONSUMER_KEY') 
    app.config['MPESA_CONSUMER_SECRET'] = os.getenv('MPESA_CONSUMER_SECRET') 
    app.config['MPESA_PASSKEY'] = os.getenv('MPESA_PASSKEY') 
    app.config['MPESA_SHORTCODE'] = os.getenv('MPESA_SHORTCODE', '174379') 
    app.config['MPESA_CALLBACK_URL'] = os.getenv('MPESA_CALLBACK_URL', 'http://localhost:5000/payments/mpesa/callback') 
    app.config['MPESA_ENVIRONMENT'] = os.getenv('MPESA_ENVIRONMENT', 'sandbox') 
    print(f"Environment: {app.config['MPESA_ENVIRONMENT']}") 
    print(f"Shortcode: {app.config['MPESA_SHORTCODE']}") 
    print(f"Callback URL: {app.config['MPESA_CALLBACK_URL']}") 
    print(f"Consumer Key Set: {bool(app.config['MPESA_CONSUMER_KEY'])}") 
    print(f"Consumer Secret Set: {bool(app.config['MPESA_CONSUMER_SECRET'])}") 
    print(f"Passkey Set: {bool(app.config['MPESA_PASSKEY'])}") 
    from utils.mpesa import MpesaAPI 
    with app.app_context(): 
        mpesa = MpesaAPI() 
        phone = '254708374149' 
        amount = 10 
        account_ref = 'TEST123' 
        description = 'Test payment' 
        print(f"\nInitiating STK Push:") 
        print(f"  Phone: {phone}") 
        print(f"  Amount: KSH {amount}") 
        print(f"  Reference: {account_ref}") 
        result = mpesa.stk_push(phone, amount, account_ref, description) 
        print(f"\nResult:") 
        print(f"  Success: {result.get('success')}") 
        if result.get('success'): 
            print(f"  Checkout Request ID: {result.get('checkout_request_id')}") 
            print(f"  Merchant Request ID: {result.get('merchant_request_id')}") 
            print(f"  Response Code: {result.get('response_code')}") 
            print(f"  Response Description: {result.get('response_description')}") 
            print(f"\n? STK Push sent successfully!") 
        else: 
            print(f"  Error: {result.get('error')}") 
            print(f"  Response: {result.get('response')}") 
            print(f"\n? STK Push failed!") 
except Exception as e: 
    print(f"\n? ERROR: {e}") 
    import traceback 
    traceback.print_exc() 
 
print("\n" + "=" * 50) 
print("Tell me what you see in the output above.") 
print("=" * 50) 
