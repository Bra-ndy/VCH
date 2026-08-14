import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

class Config:
    # =============================================
    # DATABASE - Production Ready with PostgreSQL
    # =============================================
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database URL with PostgreSQL support
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # If using PostgreSQL, fix the URL format (Render uses postgres://)
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    # Fallback for development
    if not SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/vch.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Production Connection Pool Settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,              # Max connections in pool
        'max_overflow': 40,           # Extra connections when pool is full
        'pool_timeout': 30,           # Wait time for connection
        'pool_recycle': 300,          # Recycle connections every 5 minutes
        'pool_pre_ping': True,        # Check connection before using
        'echo_pool': False,           # Don't log pool events
    }
    
    # =============================================
    # APP SETTINGS
    # =============================================
    APP_NAME = os.getenv('APP_NAME', 'VCH')
    APP_URL = os.getenv('APP_URL', 'http://localhost:5000')
    
    # =============================================
    # LOGGING - Production Ready
    # =============================================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/vch.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 10))
    
    # =============================================
    # MAIL SETTINGS
    # =============================================
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # =============================================
    # SMS SETTINGS
    # =============================================
    SMS_API_KEY = os.getenv('SMS_API_KEY')
    SMS_USERNAME = os.getenv('SMS_USERNAME')
    SMS_SENDER_ID = os.getenv('SMS_SENDER_ID', 'VCH')
    
    # =============================================
    # M-PESA CONFIGURATION
    # =============================================
    MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
    MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')
    MPESA_PASSKEY = os.getenv('MPESA_PASSKEY')
    MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE', '174379')
    MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL', 'https://your-domain.com/payments/mpesa/callback')
    MPESA_ENVIRONMENT = os.getenv('MPESA_ENVIRONMENT', 'sandbox')
    
    # M-Pesa API URLs
    @property
    def MPESA_BASE_URL(self):
        if self.MPESA_ENVIRONMENT == 'sandbox':
            return 'https://sandbox.safaricom.co.ke'
        return 'https://api.safaricom.co.ke'
    
    # M-Pesa API Endpoints
    MPESA_OAUTH_URL = '/oauth/v1/generate?grant_type=client_credentials'
    MPESA_STK_PUSH_URL = '/mpesa/stkpush/v1/processrequest'
    MPESA_STK_QUERY_URL = '/mpesa/stkpushquery/v1/query'
    MPESA_C2B_REGISTER_URL = '/mpesa/c2b/v1/registerurl'
    MPESA_B2C_URL = '/mpesa/b2c/v1/paymentrequest'
    MPESA_ACCOUNT_BALANCE_URL = '/mpesa/accountbalance/v1/query'
    MPESA_TRANSACTION_STATUS_URL = '/mpesa/transactionstatus/v1/query'
    MPESA_REVERSAL_URL = '/mpesa/reversal/v1/request'
    
    # =============================================
    # ADMIN DEPOSIT SETTINGS
    # =============================================
    ADMIN_NAME = os.getenv('ADMIN_NAME', 'WINNY LANGAT')
    ADMIN_MPESA_NUMBER = os.getenv('ADMIN_MPESA_NUMBER', '0753796259')
    ADMIN_MPESA_NUMBER_API = os.getenv('ADMIN_MPESA_NUMBER_API', '254753796259')
    DEPOSIT_VERIFICATION_REQUIRED = os.getenv('DEPOSIT_VERIFICATION_REQUIRED', 'True') == 'True'
    DEPOSIT_STALE_MINUTES = int(os.getenv('DEPOSIT_STALE_MINUTES', '60'))
    
    # =============================================
    # REDIS/CELERY
    # =============================================
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # =============================================
    # SECURITY
    # =============================================
    BCRYPT_ROUNDS = 12
    REMEMBER_COOKIE_DURATION = 30
    
    # Session settings for production
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_FILE_DIR = '/tmp/flask_session'
    
    # =============================================
    # UPLOAD SETTINGS
    # =============================================
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # =============================================
    # WALLET SETTINGS
    # =============================================
    MINIMUM_WITHDRAWAL = 100
    MAXIMUM_WITHDRAWAL = 50000
    WITHDRAWAL_FEE = 0
    
    # =============================================
    # REFERRAL SETTINGS
    # =============================================
    REFERRAL_BONUS_AMOUNT = 150.0      # KSH 150 for referrer
    REFERRAL_WELCOME_BONUS = 50.0      # KSH 50 for new user
    REFERRAL_BONUS_PERCENTAGE = 15     # 15% of friend's first purchase
    REFERRAL_COMMISSION_PERCENTAGE = 2  # 2% daily commission on feed income
    
    # =============================================
    # RENTAL SETTINGS
    # =============================================
    DAILY_EARNING_RATE = 0.05
    
    # =============================================
    # SERVICING SETTINGS
    # =============================================
    SERVICE_AMOUNT = 5.0               # KSH 5 per day (changed from 50)
    
    # =============================================
    # AGENT LEVELS
    # =============================================
    AGENT_LEVELS = {
        'junior': {
            'members': 20,
            'salary': 20000,
            'perks': []
        },
        'level1': {
            'members': 50,
            'salary': 50000,
            'perks': ['team_dinner']
        },
        'level2': {
            'members': 100,
            'salary': 100000,
            'perks': ['team_dinner', 'bonus']
        }
    }


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    MPESA_ENVIRONMENT = 'sandbox'
    
    # Development M-Pesa settings
    MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL', 'https://your-domain.com/payments/mpesa/callback')
    
    # Development admin settings
    ADMIN_NAME = str(os.getenv('ADMIN_NAME', 'WINNY LANGAT'))
    ADMIN_MPESA_NUMBER = str(os.getenv('ADMIN_MPESA_NUMBER', '0753796259'))
    ADMIN_MPESA_NUMBER_API = str(os.getenv('ADMIN_MPESA_NUMBER_API', '254753796259'))
    DEPOSIT_VERIFICATION_REQUIRED = True
    
    # CSRF Configuration - Disabled for development
    WTF_CSRF_ENABLED = False
    WTF_CSRF_SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # For local testing with ngrok, override callback URL
    @property
    def MPESA_CALLBACK_URL(self):
        ngrok_url = os.getenv('NGROK_URL')
        if ngrok_url:
            return f'{ngrok_url}/payments/mpesa/callback'
        return 'https://your-domain.com/payments/mpesa/callback'
    
    # Development database - use SQLite for speed
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///instance/vch.db')
    
    # Remove connection pooling for SQLite
    SQLALCHEMY_ENGINE_OPTIONS = {}


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    MPESA_ENVIRONMENT = 'production'
    
    # Production database - must use PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Validate database URL is set in production
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL must be set in production")
    
    # Fix PostgreSQL URL format
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    # Production connection pool settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'max_overflow': 40,
        'pool_timeout': 30,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'echo_pool': False,
    }
    
    # Production M-Pesa settings - must be set in .env
    MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL')
    if not MPESA_CALLBACK_URL:
        raise ValueError("MPESA_CALLBACK_URL must be set in production")
    
    # Security - force HTTPS in production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'
    
    # Production admin settings
    ADMIN_NAME = str(os.getenv('ADMIN_NAME', 'WINNY LANGAT'))
    ADMIN_MPESA_NUMBER = str(os.getenv('ADMIN_MPESA_NUMBER'))
    if not ADMIN_MPESA_NUMBER:
        raise ValueError("ADMIN_MPESA_NUMBER must be set in production")
    ADMIN_MPESA_NUMBER_API = str(os.getenv('ADMIN_MPESA_NUMBER_API', '254753796259'))
    DEPOSIT_VERIFICATION_REQUIRED = True
    
    # CSRF Configuration - Enabled for production
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.getenv('SECRET_KEY')
    if not WTF_CSRF_SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in production")
    
    # Session settings for production
    SESSION_FILE_DIR = '/tmp/flask_session'
    
    # Logging for production
    LOG_LEVEL = 'INFO'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MPESA_ENVIRONMENT = 'sandbox'
    MPESA_CONSUMER_KEY = 'test_key'
    MPESA_CONSUMER_SECRET = 'test_secret'
    MPESA_PASSKEY = 'test_passkey'
    MPESA_SHORTCODE = '174379'
    ADMIN_NAME = 'WINNY LANGAT'
    ADMIN_MPESA_NUMBER = '0753796259'
    ADMIN_MPESA_NUMBER_API = '254753796259'
    DEPOSIT_VERIFICATION_REQUIRED = False
    
    # Disable connection pooling for tests
    SQLALCHEMY_ENGINE_OPTIONS = {}


# =============================================
# CONFIGURATION DICTIONARY
# =============================================
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


# =============================================
# HELPER FUNCTIONS
# =============================================
def get_config():
    """Get the current configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])


def is_production():
    """Check if running in production mode"""
    return os.getenv('FLASK_ENV', 'development') == 'production'


def is_development():
    """Check if running in development mode"""
    return os.getenv('FLASK_ENV', 'development') == 'development'


def get_database_url():
    """Get the database URL with proper formatting"""
    url = os.getenv('DATABASE_URL')
    if url and url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url or 'sqlite:///instance/vch.db'