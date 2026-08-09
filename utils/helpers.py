from datetime import datetime, timedelta
import random
import string
import re
from flask import current_app

def generate_id(prefix='', length=8):
    """Generate a random ID with optional prefix"""
    chars = string.digits + string.ascii_uppercase
    random_part = ''.join(random.choices(chars, k=length))
    return f"{prefix}{random_part}" if prefix else random_part

def generate_referral_code():
    """Generate a unique referral code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def validate_phone_number(phone):
    """Validate and format phone number"""
    # Remove any non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # Check if it's a Kenyan number
    if len(phone) == 9:
        phone = '254' + phone
    elif len(phone) == 10 and phone.startswith('0'):
        phone = '254' + phone[1:]
    elif len(phone) == 12 and phone.startswith('254'):
        pass
    else:
        return None
    
    # Validate that it's a valid Kenyan number
    if not re.match(r'^254[17]\d{8}$', phone):
        return None
    
    return phone

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def calculate_days_remaining(end_date):
    """Calculate days remaining until end date"""
    if not end_date:
        return 0
    now = datetime.utcnow()
    if now >= end_date:
        return 0
    return (end_date - now).days

def format_currency(amount):
    """Format amount as KSH currency"""
    return f"KSH {amount:,.2f}"

def get_pagination(page, per_page, total):
    """Generate pagination data"""
    total_pages = (total + per_page - 1) // per_page
    return {
        'current_page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None
    }

def truncate_text(text, max_length=100):
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + '...'

def safe_float(value, default=0.0):
    """Safely convert to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Safely convert to int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default