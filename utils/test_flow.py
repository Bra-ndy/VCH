# test_mpesa_flow.py
import requests
import json

print("=" * 50)
print("TESTING M-PESA DEPOSIT FLOW")
print("=" * 50)

# Test data
test_data = {
    'phone': '254708374149',
    'amount': 10
}

print(f"\nInitiating deposit with:")
print(f"  Phone: {test_data['phone']}")
print(f"  Amount: KSH {test_data['amount']}")

try:
    # Make the request to your app
    response = requests.post(
        'http://localhost:5000/payments/mpesa/initiate',
        json=test_data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"\n✅ STK Push initiated successfully!")
            print(f"  Checkout Request ID: {data.get('checkout_request_id')}")
            print(f"  Transaction ID: {data.get('transaction_id')}")
            print(f"  Message: {data.get('message')}")
            print(f"\nCheck your phone for the M-Pesa prompt.")
            print(f"View status at: http://localhost:5000/payments/mpesa/status/{data.get('transaction_id')}")
        else:
            print(f"\n❌ Failed: {data.get('error')}")
    else:
        print(f"\n❌ HTTP Error: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("\n❌ Connection Error: Make sure your Flask app is running!")
    print("   Run: python app.py")
except Exception as e:
    print(f"\n❌ Error: {e}")