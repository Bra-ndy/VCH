import os
import requests
from flask import current_app

def send_sms(phone, message):
    """Send SMS using Africa's Talking API"""
    try:
        api_key = current_app.config.get('SMS_API_KEY')
        username = current_app.config.get('SMS_USERNAME')
        sender_id = current_app.config.get('SMS_SENDER_ID', 'VCH')
        
        if not api_key or not username:
            print(f"SMS not sent - missing credentials: {message}")
            return False
        
        # Format phone number
        phone = str(phone).strip()
        if not phone.startswith('254'):
            phone = '254' + phone
        
        # Africa's Talking API endpoint
        url = 'https://api.africastalking.com/version1/messaging'
        
        headers = {
            'apiKey': api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'username': username,
            'to': phone,
            'message': message,
            'from': sender_id
        }
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('SMSMessageData', {}).get('Recipients'):
                return True
        
        print(f"SMS sending failed: {response.text}")
        return False
        
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False

def send_verification_sms(phone, code):
    """Send verification code via SMS"""
    message = f"Your VCH verification code is: {code}. Please enter this to verify your account."
    return send_sms(phone, message)

def send_welcome_sms(phone, name):
    """Send welcome SMS"""
    message = f"Welcome to VCH, {name}! Your account has been created. Start earning today!"
    return send_sms(phone, message)

def send_deposit_confirmation(phone, amount, transaction_id):
    """Send deposit confirmation SMS"""
    message = f"VCH: Your deposit of KSH {amount:,.2f} has been received. Transaction ID: {transaction_id}"
    return send_sms(phone, message)

def send_withdrawal_confirmation(phone, amount, transaction_id):
    """Send withdrawal confirmation SMS"""
    message = f"VCH: Your withdrawal of KSH {amount:,.2f} has been processed. Transaction ID: {transaction_id}"
    return send_sms(phone, message)

def send_earnings_notification(phone, amount, source):
    """Send earnings notification SMS"""
    message = f"VCH: You earned KSH {amount:,.2f} from {source}. Keep earning!"
    return send_sms(phone, message)