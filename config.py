import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///vch.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # App Settings
    APP_NAME = os.getenv('APP_NAME', 'VCH')
    APP_URL = os.getenv('APP_URL', 'http://localhost:5000')
    
    # Mail
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # SMS
    SMS_API_KEY = os.getenv('SMS_API_KEY')
    SMS_USERNAME = os.getenv('SMS_USERNAME')
    SMS_SENDER_ID = os.getenv('SMS_SENDER_ID', 'VCH')
    
    # M-Pesa Configuration
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
    # Admin name for deposits
    ADMIN_NAME = os.getenv('ADMIN_NAME', 'WINNY LANGAT')
    
    # Admin phone number for deposits (formatted for display)
    ADMIN_MPESA_NUMBER = os.getenv('ADMIN_MPESA_NUMBER', '0753796259')
    
    # Admin phone number for M-Pesa (formatted for API - with country code)
    ADMIN_MPESA_NUMBER_API = os.getenv('ADMIN_MPESA_NUMBER_API', '254753796259')
    
    # Require admin verification for manual M-Pesa deposits
    DEPOSIT_VERIFICATION_REQUIRED = os.getenv('DEPOSIT_VERIFICATION_REQUIRED', 'True') == 'True'
    
    # Time (in minutes) after which pending deposits are considered stale
    DEPOSIT_STALE_MINUTES = int(os.getenv('DEPOSIT_STALE_MINUTES', '60'))
    
    # =============================================
    
    # Redis/Celery
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Security
    BCRYPT_ROUNDS = 12
    REMEMBER_COOKIE_DURATION = 30
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Wallet Settings
    MINIMUM_WITHDRAWAL = 100
    MAXIMUM_WITHDRAWAL = 50000
    WITHDRAWAL_FEE = 0
    
    # Referral Settings
    REFERRAL_BONUS_PERCENTAGE = 10
    REFERRAL_COMMISSION_PERCENTAGE = 2
    
    # Rental Settings
    DAILY_EARNING_RATE = 0.05
    
    # Servicing Settings
    SERVICE_EARNING = 50
    
    # Agent Levels
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
            'perks': ['team_dinner']
        }
    }

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    MPESA_ENVIRONMENT = 'sandbox'
    
    # Development M-Pesa settings
    MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL', 'https://your-domain.com/payments/mpesa/callback')
    
    # Development admin settings - convert to string
    ADMIN_NAME = str(os.getenv('ADMIN_NAME', 'WINNY LANGAT'))
    ADMIN_MPESA_NUMBER = str(os.getenv('ADMIN_MPESA_NUMBER', '0753796259'))
    ADMIN_MPESA_NUMBER_API = str(os.getenv('ADMIN_MPESA_NUMBER_API', '254753796259'))
    DEPOSIT_VERIFICATION_REQUIRED = True
    
    # For local testing with ngrok, override callback URL
    @property
    def MPESA_CALLBACK_URL(self):
        ngrok_url = os.getenv('NGROK_URL')
        if ngrok_url:
            return f'{ngrok_url}/payments/mpesa/callback'
        return 'https://your-domain.com/payments/mpesa/callback'

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    MPESA_ENVIRONMENT = 'production'
    
    # Production M-Pesa settings - must be set in .env
    MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL')
    
    # Security - force HTTPS in production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'
    
    # Production admin settings - convert to string
    ADMIN_NAME = str(os.getenv('ADMIN_NAME', 'WINNY LANGAT'))
    ADMIN_MPESA_NUMBER = str(os.getenv('ADMIN_MPESA_NUMBER', '0753796259'))
    ADMIN_MPESA_NUMBER_API = str(os.getenv('ADMIN_MPESA_NUMBER_API', '254753796259'))
    DEPOSIT_VERIFICATION_REQUIRED = True
    
    # Validate admin number is set in production
    @property
    def ADMIN_MPESA_NUMBER(self):
        value = os.getenv('ADMIN_MPESA_NUMBER')
        if not value:
            raise ValueError("ADMIN_MPESA_NUMBER must be set in production")
        return str(value)

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

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}