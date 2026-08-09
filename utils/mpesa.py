# utils/mpesa.py - Complete fixed version
import requests
import base64
import json
import logging
from datetime import datetime
from flask import current_app
import re

logger = logging.getLogger(__name__)

class MpesaAPI:
    """M-Pesa API Integration Class"""
    
    def __init__(self):
        # Load from config - use direct values
        self.consumer_key = current_app.config.get('MPESA_CONSUMER_KEY')
        self.consumer_secret = current_app.config.get('MPESA_CONSUMER_SECRET')
        self.passkey = current_app.config.get('MPESA_PASSKEY')
        self.shortcode = current_app.config.get('MPESA_SHORTCODE', '174379')
        self.callback_url = current_app.config.get('MPESA_CALLBACK_URL')
        self.environment = current_app.config.get('MPESA_ENVIRONMENT', 'sandbox')
        
        # Set base URL based on environment
        if self.environment == 'sandbox':
            self.base_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.base_url = 'https://api.safaricom.co.ke'
        
        self.access_token = None
        self.token_expiry = None
        
        logger.info(f"M-Pesa initialized with environment: {self.environment}")
        logger.info(f"M-Pesa shortcode: {self.shortcode}")
        logger.info(f"M-Pesa base URL: {self.base_url}")
        logger.info(f"Passkey Set: {bool(self.passkey)}")
        if self.passkey:
            logger.info(f"Passkey length: {len(self.passkey)}")
    
    def get_access_token(self):
        """Get M-Pesa access token"""
        try:
            if self.access_token and self.token_expiry and datetime.now().timestamp() < self.token_expiry:
                return self.access_token
            
            url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            auth = base64.b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth}'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                self.token_expiry = datetime.now().timestamp() + int(data.get('expires_in', 3600))
                logger.info("Access token obtained successfully")
                return self.access_token
            else:
                logger.error(f"Failed to get access token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            return None
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """
        Initiate STK Push (Lipa Na M-Pesa Online)
        """
        try:
            # Validate inputs
            if not self.consumer_key or self.consumer_key == 'your_consumer_key_here':
                return {'success': False, 'error': 'Consumer Key not configured'}
            
            if not self.consumer_secret or self.consumer_secret == 'your_consumer_secret_here':
                return {'success': False, 'error': 'Consumer Secret not configured'}
            
            if not self.passkey or self.passkey == 'your_passkey_here':
                logger.error(f"Passkey is missing or invalid")
                return {'success': False, 'error': 'Passkey not configured'}
            
            # Format phone number
            phone = re.sub(r'\D', '', str(phone_number))
            if phone.startswith('0'):
                phone = '254' + phone[1:]
            elif len(phone) == 9:
                phone = '254' + phone
            elif len(phone) == 10 and not phone.startswith('254'):
                phone = '254' + phone[1:]
            elif phone.startswith('254'):
                phone = phone
            else:
                phone = '254' + phone
            
            # Validate phone number
            if not re.match(r'^254[17]\d{8}$', phone):
                return {'success': False, 'error': f'Invalid phone number: {phone}. Must be a valid Kenyan number.'}
            
            # Get access token
            token = self.get_access_token()
            if not token:
                return {'success': False, 'error': 'Failed to get access token'}
            
            # Generate timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Generate password
            password_str = f"{self.shortcode}{self.passkey}{timestamp}"
            password = base64.b64encode(password_str.encode()).decode()
            
            # For sandbox, use a valid callback URL
            callback_url = 'https://example.com/payments/mpesa/callback'
            
            # Prepare request data
            data = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': int(amount),
                'PartyA': phone,
                'PartyB': self.shortcode,
                'PhoneNumber': phone,
                'CallBackURL': callback_url,
                'AccountReference': str(account_reference)[:12],
                'TransactionDesc': str(transaction_desc)[:20]
            }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            
            logger.info(f"Initiating STK Push for {phone} amount {amount}")
            logger.info(f"Callback URL: {callback_url}")
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            logger.info(f"Response Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"STK Push response: {result}")
                
                if result.get('ResponseCode') == '0':
                    return {
                        'success': True,
                        'checkout_request_id': result.get('CheckoutRequestID'),
                        'merchant_request_id': result.get('MerchantRequestID'),
                        'response_code': result.get('ResponseCode'),
                        'response_description': result.get('ResponseDescription')
                    }
                else:
                    error_msg = result.get('errorMessage', 'Payment failed')
                    if result.get('ResponseCode') == '1032':
                        error_msg = 'Transaction cancelled by user'
                    elif result.get('ResponseCode') == '1037':
                        error_msg = 'User timeout - please try again'
                    
                    return {
                        'success': False,
                        'error': error_msg,
                        'response_code': result.get('ResponseCode'),
                        'response_description': result.get('ResponseDescription')
                    }
            else:
                logger.error(f"STK Push API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'API error: {response.status_code}',
                    'response': response.text
                }
                
        except Exception as e:
            logger.error(f"STK Push error: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def query_status(self, checkout_request_id):
        """Query STK Push transaction status"""
        try:
            token = self.get_access_token()
            if not token:
                return {'success': False, 'error': 'Failed to get access token'}
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            password_str = f"{self.shortcode}{self.passkey}{timestamp}"
            password = base64.b64encode(password_str.encode()).decode()
            
            data = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'CheckoutRequestID': checkout_request_id
            }
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            
            logger.info(f"Querying STK Push status for: {checkout_request_id}")
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Query response: {result}")
                
                result_code = result.get('ResultCode')
                
                if result_code == '0':
                    return {
                        'success': True,
                        'status': 'completed',
                        'result_code': result_code,
                        'result_desc': result.get('ResultDesc'),
                        'amount': result.get('Amount'),
                        'mpesa_receipt': result.get('MpesaReceiptNumber'),
                        'transaction_date': result.get('TransactionDate')
                    }
                elif result_code == '1037':
                    return {
                        'success': True,
                        'status': 'pending',
                        'result_code': result_code,
                        'result_desc': 'Transaction pending user confirmation',
                        'amount': result.get('Amount')
                    }
                elif result_code == '1032':
                    return {
                        'success': True,
                        'status': 'cancelled',
                        'result_code': result_code,
                        'result_desc': 'Transaction cancelled by user'
                    }
                else:
                    return {
                        'success': True,
                        'status': 'failed',
                        'result_code': result_code,
                        'result_desc': result.get('ResultDesc', 'Transaction failed')
                    }
            else:
                return {'success': False, 'error': f'API error: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"Query status error: {e}")
            return {'success': False, 'error': str(e)}