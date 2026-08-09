from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string

db = SQLAlchemy()

# Helper functions
def generate_id(prefix='', length=8):
    """Generate a random ID with optional prefix"""
    chars = string.digits + string.ascii_uppercase
    random_part = ''.join(random.choices(chars, k=length))
    return f"{prefix}{random_part}" if prefix else random_part

def generate_referral_code():
    """Generate a unique referral code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# User Model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Profile
    full_name = db.Column(db.String(100))
    avatar = db.Column(db.String(200))
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Referral
    referral_code = db.Column(db.String(8), unique=True, nullable=False)
    referred_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    referral_count = db.Column(db.Integer, default=0)
    
    # Agent Level
    agent_level = db.Column(db.String(20), default='none')  # none, junior, level1, level2
    agent_salary_earned = db.Column(db.Float, default=0.0)
    
    # Wallet
    balance = db.Column(db.Float, default=0.0)
    total_deposited = db.Column(db.Float, default=0.0)
    total_withdrawn = db.Column(db.Float, default=0.0)
    total_earned = db.Column(db.Float, default=0.0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    
    # Relations
    referrals = db.relationship('User', backref=db.backref('referrer', remote_side=[id]), lazy='dynamic')
    rentals = db.relationship('Rental', backref='user', lazy='dynamic')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic')
    service_history = db.relationship('ServiceHistory', backref='user', lazy='dynamic')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.user_id:
            self.user_id = generate_id('VCH', 8)
        if not self.referral_code:
            self.referral_code = generate_referral_code()
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_referral_link(self):
        return f"/auth/register?ref={self.referral_code}"
    
    def update_agent_level(self):
        """Update user's agent level based on referral count"""
        from config import Config
        
        if self.referral_count >= Config.AGENT_LEVELS['level2']['members']:
            self.agent_level = 'level2'
        elif self.referral_count >= Config.AGENT_LEVELS['level1']['members']:
            self.agent_level = 'level1'
        elif self.referral_count >= Config.AGENT_LEVELS['junior']['members']:
            self.agent_level = 'junior'
        else:
            self.agent_level = 'none'
    
    def get_agent_salary(self):
        from config import Config
        level_config = Config.AGENT_LEVELS.get(self.agent_level)
        return level_config['salary'] if level_config else 0
    
    def __repr__(self):
        return f'<User {self.username}>'

# Vehicle Model
class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(200))
    
    # Pricing
    rental_price = db.Column(db.Float, nullable=False)  # Total rental cost
    daily_earning = db.Column(db.Float, nullable=False)
    rental_period = db.Column(db.Integer, default=30)  # Days
    
    # Profit
    total_profit = db.Column(db.Float)  # Total profit over rental period
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_available = db.Column(db.Boolean, default=True)
    
    # Metadata
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)  # For ordering by price
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.rental_price and self.daily_earning and self.rental_period:
            self.total_profit = self.daily_earning * self.rental_period - self.rental_price
    
    def calculate_profit(self):
        """Calculate profit for this vehicle"""
        return (self.daily_earning * self.rental_period) - self.rental_price
    
    def __repr__(self):
        return f'<Vehicle {self.name}>'

# Rental Model
class Rental(db.Model):
    __tablename__ = 'rentals'
    
    id = db.Column(db.Integer, primary_key=True)
    rental_id = db.Column(db.String(50), unique=True, nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    
    # Rental details
    amount = db.Column(db.Float, nullable=False)
    daily_earning = db.Column(db.Float, nullable=False)
    total_profit = db.Column(db.Float, nullable=False)
    
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Status: active, completed, cancelled
    status = db.Column(db.String(20), default='active')
    
    # Earnings tracking
    days_elapsed = db.Column(db.Integer, default=0)
    total_earned = db.Column(db.Float, default=0.0)
    last_earning_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    vehicle = db.relationship('Vehicle', backref='rentals')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.rental_id:
            self.rental_id = generate_id('RENT', 10)
        if not self.end_date and self.start_date:
            self.end_date = self.start_date + timedelta(days=30)
    
    def is_expired(self):
        """Check if rental period has expired"""
        return datetime.utcnow() >= self.end_date
    
    def days_remaining(self):
        """Get days remaining in rental period"""
        if self.is_expired():
            return 0
        return (self.end_date - datetime.utcnow()).days
    
    def calculate_daily_earning(self):
        """Calculate daily earning for this rental"""
        return self.daily_earning
    
    def __repr__(self):
        return f'<Rental {self.rental_id}>'

# Transaction Model
class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(50), unique=True, nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Transaction details
    type = db.Column(db.String(20), nullable=False)  # deposit, withdrawal, rental_earning, service_earning, referral_bonus, agent_salary
    amount = db.Column(db.Float, nullable=False)
    fee = db.Column(db.Float, default=0.0)
    net_amount = db.Column(db.Float, nullable=False)
    
    # Reference
    reference = db.Column(db.String(100))
    description = db.Column(db.String(200))
    
    # Status: pending, completed, failed, cancelled
    status = db.Column(db.String(20), default='pending')
    
    # Payment details (for deposits)
    payment_method = db.Column(db.String(50))
    payment_reference = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.transaction_id:
            self.transaction_id = generate_id('TXN', 12)
    
    def __repr__(self):
        return f'<Transaction {self.transaction_id}>'

# Service History Model
class ServiceHistory(db.Model):
    __tablename__ = 'service_history'
    
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.String(50), unique=True, nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Service details
    type = db.Column(db.String(20), default='daily_servicing')  # daily_servicing
    earning = db.Column(db.Float, default=50.0)
    
    # Dates
    service_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.service_id:
            self.service_id = generate_id('SRV', 10)
    
    def __repr__(self):
        return f'<Service {self.service_id}>'

# Referral Bonus Model
class ReferralBonus(db.Model):
    __tablename__ = 'referral_bonuses'
    
    id = db.Column(db.Integer, primary_key=True)
    
    referrer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referred_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Bonus details
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), default='signup_bonus')  # signup_bonus, commission
    
    # Status
    is_paid = db.Column(db.Boolean, default=False)
    paid_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    referrer = db.relationship('User', foreign_keys=[referrer_id], backref='referral_bonuses_given')
    referred = db.relationship('User', foreign_keys=[referred_id], backref='referral_bonuses_received')
    
    def __repr__(self):
        return f'<ReferralBonus {self.id}>'

# Notification Model
class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.String(50), unique=True, nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Notification details
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')  # info, success, warning, error
    
    # Read status
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    
    # Link/action
    link = db.Column(db.String(200))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.notification_id:
            self.notification_id = generate_id('NOTIF', 10)
    
    def __repr__(self):
        return f'<Notification {self.notification_id}>'

# Activity Log Model
class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(200))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='activities')
    
    def __repr__(self):
        return f'<ActivityLog {self.id}>'