from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import abort
from flask_login import current_user
import re
import hashlib
import hmac

def generate_verification_token(email):
    """Generate a verification token for email"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-verification')

def verify_verification_token(token, expiration=3600):
    """Verify a verification token"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='email-verification',
            max_age=expiration
        )
        return email
    except Exception:
        return None

def generate_reset_token(email):
    """Generate a password reset token"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset')

def verify_reset_token(token, expiration=3600):
    """Verify a password reset token"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='password-reset',
            max_age=expiration
        )
        return email
    except Exception:
        return None

def hash_password(password):
    """Hash a password"""
    return generate_password_hash(password)

def verify_password(password, hashed):
    """Verify a password against its hash"""
    return check_password_hash(hashed, password)

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        # Check if user is admin (first user for now)
        # In production, add is_admin field to User
        if current_user.id != 1:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def sanitize_input(text):
    """Sanitize user input to prevent XSS"""
    if not text:
        return text
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    # Remove script tags
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
    # Escape special characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    return text

def generate_csrf_token():
    """Generate a CSRF token"""
    import uuid
    return uuid.uuid4().hex

def validate_csrf_token(token, session_token):
    """Validate a CSRF token"""
    return hmac.compare_digest(str(token), str(session_token))