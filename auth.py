from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
import re

from models import db, User, Notification, ActivityLog
from forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm
from utils.email import send_verification_email, send_password_reset_email
from utils.sms import send_sms
from utils.security import generate_verification_token, verify_verification_token


auth_bp = Blueprint('auth', __name__)

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

def validate_phone_number(phone):
    """Validate phone number format"""
    # Format the phone number first
    formatted = format_phone_number(phone)
    if not formatted:
        return None, "Phone number is required"
    
    # Check if it's a valid Kenyan number (254 + 9 digits)
    # Accept numbers starting with 2547 or 2541 (Safaricom and other networks)
    if not re.match(r'^254[17]\d{8}$', formatted):
        return None, "Invalid phone number. Must be a valid Kenyan number (e.g., 254712345678)"
    
    return formatted, None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('auth/login.html', form=form)
            
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.now(timezone.utc)
            
            # Log activity
            log = ActivityLog(
                user_id=user.id,
                action='login',
                description=f'User logged in from IP: {request.remote_addr}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(log)
            db.session.commit()
            
            flash(f'Welcome back, {user.username}!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Validate and format phone number (form already does this, but double-check)
        phone, error = validate_phone_number(form.phone.data)
        if error:
            flash(error, 'danger')
            return render_template('auth/register.html', form=form)
        
        # Check if email already exists
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash('Email already registered. Please use a different email or login.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Check if phone already exists
        if User.query.filter_by(phone=phone).first():
            flash('Phone number already registered. Please use a different number.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Create user
        user = User(
            username=form.username.data,
            email=form.email.data.lower(),
            phone=phone,
            full_name=form.username.data
        )
        user.set_password(form.password.data)
        
        # Handle referral
        if form.referral_code.data:
            referrer = User.query.filter_by(referral_code=form.referral_code.data.upper()).first()
            if referrer:
                user.referred_by = referrer.id
                # Update referrer's count
                referrer.referral_count += 1
                # Update referrer's agent level
                referrer.update_agent_level()
                db.session.add(referrer)
        
        # Generate verification token
        token = generate_verification_token(user.email)
        
        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating account: {str(e)}', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Send welcome email
        try:
            send_verification_email(user.email, token)
        except Exception as e:
            print(f"Error sending verification email: {e}")
        
        # Send welcome SMS
        try:
            welcome_message = f"Welcome to VCH! Your account has been created. Please verify your email to get started."
            send_sms(user.phone, welcome_message)
        except Exception as e:
            print(f"Error sending welcome SMS: {e}")
        
        # Create notification
        try:
            notification = Notification(
                user_id=user.id,
                title='Welcome to VCH!',
                message='Thank you for joining VCH. Complete your profile and start earning today!'
            )
            db.session.add(notification)
            db.session.commit()
        except Exception as e:
            print(f"Error creating notification: {e}")
        
        flash('Account created successfully! Please check your email to verify your account.', 'success')
        return redirect(url_for('auth.login'))
    
    # If form validation fails, flash errors for display
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                field_name = field.replace('_', ' ').title()
                flash(f'{field_name}: {error}', 'danger')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/verify/<token>')
def verify_email(token):
    email = verify_verification_token(token)
    if not email:
        flash('Invalid or expired verification link', 'danger')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('auth.login'))
    
    if user.is_verified:
        flash('Email already verified', 'info')
        return redirect(url_for('auth.login'))
    
    try:
        user.is_verified = True
        db.session.commit()
        
        # Send welcome bonus notification
        notification = Notification(
            user_id=user.id,
            title='Email Verified!',
            message='Your email has been verified. Start renting cars and earning today!'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('Email verified successfully! You can now login.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error verifying email. Please try again.', 'danger')
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = generate_verification_token(user.email)
            try:
                send_password_reset_email(user.email, token)
                flash('Password reset link sent to your email', 'success')
            except Exception as e:
                flash('Error sending reset email. Please try again.', 'danger')
        else:
            flash('Email not found. Please check and try again.', 'danger')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_verification_token(token)
    if not email:
        flash('Invalid or expired reset link', 'danger')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('auth.login'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        try:
            user.set_password(form.password.data)
            db.session.commit()
            flash('Password reset successfully! Please login with your new password.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Error resetting password. Please try again.', 'danger')
    
    return render_template('auth/reset_password.html', form=form, token=token)

@auth_bp.route('/resend-verification')
@login_required
def resend_verification():
    if current_user.is_verified:
        flash('Your email is already verified', 'info')
        return redirect(url_for('dashboard'))
    
    token = generate_verification_token(current_user.email)
    try:
        send_verification_email(current_user.email, token)
        flash('Verification email sent successfully!', 'success')
    except Exception as e:
        flash('Error sending verification email. Please try again.', 'danger')
    
    return redirect(url_for('dashboard'))