# utils/email.py - Fixed version without circular import
from flask import render_template, current_app
from flask_mail import Message
from threading import Thread

# Don't import mail from app - use current_app instead

def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            # Get mail instance from app
            mail = app.extensions.get('mail')
            if mail:
                mail.send(msg)
                return True
            else:
                print("Mail extension not initialized")
                return False
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

def send_email(subject, recipients, template, **kwargs):
    """Send email using Flask-Mail"""
    try:
        app = current_app._get_current_object()
        
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=render_template(template, **kwargs),
            sender=app.config.get('MAIL_DEFAULT_SENDER')
        )
        
        # Send asynchronously
        thread = Thread(target=send_async_email, args=(app, msg))
        thread.start()
        
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_verification_email(email, token):
    """Send email verification link"""
    subject = "Verify Your Email - VCH"
    template = "email/verify_email.html"
    kwargs = {
        'token': token,
        'app_name': current_app.config.get('APP_NAME', 'VCH')
    }
    return send_email(subject, [email], template, **kwargs)

def send_password_reset_email(email, token):
    """Send password reset link"""
    subject = "Reset Your Password - VCH"
    template = "email/reset_password.html"
    kwargs = {
        'token': token,
        'app_name': current_app.config.get('APP_NAME', 'VCH')
    }
    return send_email(subject, [email], template, **kwargs)

def send_welcome_email(email, username):
    """Send welcome email"""
    subject = "Welcome to VCH!"
    template = "email/welcome.html"
    kwargs = {
        'username': username,
        'app_name': current_app.config.get('APP_NAME', 'VCH')
    }
    return send_email(subject, [email], template, **kwargs)

def send_deposit_confirmation_email(email, amount, transaction_id):
    """Send deposit confirmation email"""
    subject = f"Deposit Confirmed - KSH {amount:,.2f}"
    template = "email/deposit_confirmation.html"
    kwargs = {
        'amount': amount,
        'transaction_id': transaction_id,
        'app_name': current_app.config.get('APP_NAME', 'VCH')
    }
    return send_email(subject, [email], template, **kwargs)

def send_withdrawal_confirmation_email(email, amount, transaction_id):
    """Send withdrawal confirmation email"""
    subject = f"Withdrawal Confirmed - KSH {amount:,.2f}"
    template = "email/withdrawal_confirmation.html"
    kwargs = {
        'amount': amount,
        'transaction_id': transaction_id,
        'app_name': current_app.config.get('APP_NAME', 'VCH')
    }
    return send_email(subject, [email], template, **kwargs)