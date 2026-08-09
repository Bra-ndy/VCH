from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, DecimalField, SelectField, TextAreaField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, ValidationError, Regexp
from flask_wtf.file import FileField, FileAllowed, FileRequired
from models import User
import re

# Helper function to format phone number
def format_phone_number(phone):
    """Format phone number to standard format with country code"""
    # Remove any non-digit characters
    phone = re.sub(r'\D', '', str(phone))
    
    # If empty, return None
    if not phone:
        return None
    
    # If it starts with 0, remove it and add 254
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    # If it has 9 digits, add 254 prefix
    elif len(phone) == 9:
        phone = '254' + phone
    # If it has 10 digits and doesn't start with 254, assume it has 0 prefix
    elif len(phone) == 10 and not phone.startswith('254'):
        phone = '254' + phone[1:]
    # If it already has 254 prefix, keep it
    elif phone.startswith('254'):
        phone = phone
    # Otherwise, prepend 254
    else:
        phone = '254' + phone
    
    return phone

def validate_phone_number(form, field):
    """Validate phone number format"""
    phone = field.data
    if not phone:
        raise ValidationError('Phone number is required')
    
    # Remove any non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # Check if it's a valid Kenyan number
    # Accept formats: 0703338493, 703338493, 254703338493, +254703338493
    if not re.match(r'^0?\d{9}$|^254\d{9}$', phone):
        raise ValidationError('Invalid phone number. Must be a valid Kenyan number (e.g., 0703338493 or 254703338493)')
    
    # Format the phone number to standard format
    formatted = format_phone_number(phone)
    field.data = formatted
    
    # Check if phone already exists
    if User.query.filter_by(phone=formatted).first():
        raise ValidationError('Phone number already registered')

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80),
        Regexp('^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers and underscore')
    ])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[
        DataRequired(),
        validate_phone_number
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters'),
        Regexp('^(?=.*[A-Za-z])(?=.*\\d).+$', message='Password must contain at least one letter and one number')
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    referral_code = StringField('Referral Code', validators=[Optional(), Length(max=8)])
    agree_terms = BooleanField('I agree to the Terms and Conditions', validators=[DataRequired()])
    
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken')
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered')
    
    def validate_referral_code(self, field):
        if field.data:
            referrer = User.query.filter_by(referral_code=field.data.upper()).first()
            if not referrer:
                raise ValidationError('Invalid referral code')

class ForgotPasswordForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8),
        Regexp('^(?=.*[A-Za-z])(?=.*\\d).+$', message='Password must contain at least one letter and one number')
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])

class DepositForm(FlaskForm):
    amount = DecimalField('Amount (KSH)', validators=[
        DataRequired(),
        NumberRange(min=10, max=100000, message='Amount must be between 10 and 100,000 KSH')
    ])
    payment_method = SelectField('Payment Method', choices=[
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer')
    ], validators=[DataRequired()])
    phone = StringField('M-Pesa Phone Number', validators=[
        Optional(),
        Regexp('^[0-9]+$', message='Phone number must contain only digits')
    ])

class WithdrawForm(FlaskForm):
    amount = DecimalField('Amount (KSH)', validators=[
        DataRequired(),
        NumberRange(min=100, max=50000, message='Amount must be between 100 and 50,000 KSH')
    ])
    phone = StringField('Phone Number', validators=[
        DataRequired(),
        Regexp('^[0-9]+$', message='Phone number must contain only digits')
    ])

class CarRentalForm(FlaskForm):
    vehicle_id = IntegerField('Vehicle ID', validators=[DataRequired()])
    rental_period = SelectField('Rental Period', choices=[
        (30, '30 Days')
    ], coerce=int, validators=[DataRequired()])

class ServiceForm(FlaskForm):
    service_type = SelectField('Service Type', choices=[
        ('daily_servicing', 'Daily Servicing')
    ], validators=[DataRequired()])

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[
        DataRequired(),
        validate_phone_number
    ])
    full_name = StringField('Full Name')
    avatar = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Only images are allowed')
    ])

class AdminUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[
        DataRequired(),
        validate_phone_number
    ])
    password = PasswordField('Password', validators=[Optional(), Length(min=8)])
    is_active = BooleanField('Active')
    is_verified = BooleanField('Verified')
    agent_level = SelectField('Agent Level', choices=[
        ('none', 'None'),
        ('junior', 'Junior Agent'),
        ('level1', 'Level 1 Agent'),
        ('level2', 'Level 2 Agent')
    ])

class AdminVehicleForm(FlaskForm):
    name = StringField('Car Name', validators=[DataRequired()])
    brand = StringField('Brand', validators=[DataRequired()])
    rental_price = DecimalField('Rental Price (KSH)', validators=[DataRequired(), NumberRange(min=0)])
    daily_earning = DecimalField('Daily Earning (KSH)', validators=[DataRequired(), NumberRange(min=0)])
    rental_period = IntegerField('Rental Period (Days)', validators=[DataRequired(), NumberRange(min=1)])
    description = TextAreaField('Description')
    image = FileField('Car Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Only images are allowed')
    ])
    is_active = BooleanField('Active')
    is_available = BooleanField('Available')
    sort_order = IntegerField('Sort Order', default=0)

class AdminSettingsForm(FlaskForm):
    site_name = StringField('Site Name')
    referral_bonus = DecimalField('Referral Bonus %', validators=[NumberRange(min=0, max=100)])
    referral_commission = DecimalField('Referral Commission %', validators=[NumberRange(min=0, max=100)])
    min_withdrawal = DecimalField('Minimum Withdrawal', validators=[NumberRange(min=0)])
    max_withdrawal = DecimalField('Maximum Withdrawal', validators=[NumberRange(min=0)])
    service_earning = DecimalField('Daily Service Earning', validators=[NumberRange(min=0)])