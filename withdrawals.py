from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, timezone
from models import db, Transaction, Notification, User
from forms import WithdrawForm
from utils.wallet import process_withdrawal
import logging

withdrawals_bp = Blueprint('withdrawals', __name__, url_prefix='/withdrawals')
logger = logging.getLogger(__name__)

# Withdrawal time restrictions (EAT - UTC+3)
WITHDRAWAL_START_HOUR = 9   # 9 AM
WITHDRAWAL_END_HOUR = 18    # 6 PM
WITHDRAWAL_DAYS = [0, 1, 2, 3, 4]  # Monday (0) to Friday (4)

def can_withdraw():
    """
    Check if withdrawals are currently allowed based on time and day.
    Returns: (can_withdraw, message, next_available)
    """
    now = datetime.now(timezone.utc)
    kenya_time = now + timedelta(hours=3)  # UTC+3 for Kenya
    
    current_hour = kenya_time.hour
    current_day = kenya_time.weekday()  # Monday=0, Sunday=6
    
    # Check if it's a weekday (Monday to Friday)
    if current_day not in WITHDRAWAL_DAYS:
        next_time = get_next_available_time(kenya_time)
        return False, "Withdrawals are only available Monday to Friday. Please try again on a weekday.", next_time
    
    # Check if within business hours (9 AM - 6 PM)
    if current_hour < WITHDRAWAL_START_HOUR or current_hour >= WITHDRAWAL_END_HOUR:
        next_time = get_next_available_time(kenya_time)
        return False, f"Withdrawals are only available from {WITHDRAWAL_START_HOUR}:00 AM to {WITHDRAWAL_END_HOUR}:00 PM (EAT). Please try again during business hours.", next_time
    
    return True, "Withdrawals are currently available.", "Now"

def get_next_available_time(kenya_time):
    """
    Get the next available time for withdrawal.
    """
    current_hour = kenya_time.hour
    current_day = kenya_time.weekday()
    
    # If within business hours and weekday, return now
    if current_day in WITHDRAWAL_DAYS and WITHDRAWAL_START_HOUR <= current_hour < WITHDRAWAL_END_HOUR:
        return "Now"
    
    # If after hours, next day at 9 AM
    if current_hour >= WITHDRAWAL_END_HOUR:
        next_day = kenya_time + timedelta(days=1)
        # If next day is weekend, skip to Monday
        while next_day.weekday() not in WITHDRAWAL_DAYS:
            next_day += timedelta(days=1)
        return f"Tomorrow at {WITHDRAWAL_START_HOUR}:00 AM"
    
    # If before hours, today at 9 AM
    if current_hour < WITHDRAWAL_START_HOUR:
        return f"Today at {WITHDRAWAL_START_HOUR}:00 AM"
    
    # If weekend, next Monday at 9 AM
    days_to_monday = (7 - current_day) % 7
    if days_to_monday == 0:
        days_to_monday = 7
    next_monday = kenya_time + timedelta(days=days_to_monday)
    return f"Monday at {WITHDRAWAL_START_HOUR}:00 AM"

@withdrawals_bp.route('/')
@login_required
def index():
    """Withdrawal page"""
    can_withdraw_now, message, next_available = can_withdraw()
    
    return render_template(
        'wallet/withdraw.html',
        can_withdraw_now=can_withdraw_now,
        message=message,
        next_available=next_available,
        balance=current_user.balance or 0
    )

@withdrawals_bp.route('/request', methods=['POST'])
@login_required
def request_withdrawal():
    """Request a withdrawal"""
    # Check if withdrawals are available
    can_withdraw_now, message, next_available = can_withdraw()
    
    if not can_withdraw_now:
        return jsonify({
            'error': message,
            'next_available': next_available
        }), 400
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid data'}), 400
        
        amount = float(data.get('amount', 0))
        phone = data.get('phone', '')
        
        if amount <= 0:
            return jsonify({'error': 'Invalid amount'}), 400
        
        if amount < 100:
            return jsonify({'error': 'Minimum withdrawal is KSH 100'}), 400
        
        if amount > 50000:
            return jsonify({'error': 'Maximum withdrawal is KSH 50,000'}), 400
        
        if not phone:
            return jsonify({'error': 'Phone number is required'}), 400
        
        # Check if user has enough balance
        if current_user.balance < amount:
            return jsonify({'error': f'Insufficient balance. You have KSH {current_user.balance:,.2f}'}), 400
        
        transaction = process_withdrawal(
            user_id=current_user.id,
            amount=amount,
            phone=phone
        )
        
        # Create notification
        notification = Notification(
            user_id=current_user.id,
            title='Withdrawal Request Submitted 📤',
            message=f'Your withdrawal of KSH {amount:,.2f} has been submitted for processing.',
            type='info'
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'transaction_id': transaction.transaction_id,
            'amount': transaction.amount,
            'status': transaction.status,
            'message': f'Withdrawal of KSH {amount:,.2f} submitted successfully!'
        })
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f'Withdrawal error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@withdrawals_bp.route('/history')
@login_required
def history():
    """Withdrawal history"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    withdrawals = Transaction.query.filter_by(
        user_id=current_user.id,
        type='withdrawal'
    ).order_by(Transaction.created_at.desc())\
     .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('wallet/withdrawal_history.html', withdrawals=withdrawals)

@withdrawals_bp.route('/cancel/<transaction_id>')
@login_required
def cancel(transaction_id):
    """Cancel a pending withdrawal"""
    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id,
        user_id=current_user.id,
        status='pending'
    ).first()
    
    if not transaction:
        flash('Transaction not found or cannot be cancelled', 'danger')
        return redirect(url_for('withdrawals.history'))
    
    # Refund the balance
    user = User.query.get(current_user.id)
    if user:
        user.balance += transaction.amount
    
    transaction.status = 'cancelled'
    db.session.commit()
    
    flash('Withdrawal cancelled successfully. Funds have been refunded to your balance.', 'success')
    return redirect(url_for('withdrawals.history'))

@withdrawals_bp.route('/check-status')
@login_required
def check_status():
    """API endpoint to check if withdrawals are available"""
    can_withdraw_now, message, next_available = can_withdraw()
    
    return jsonify({
        'can_withdraw': can_withdraw_now,
        'message': message,
        'next_available': next_available,
        'business_hours': {
            'start': WITHDRAWAL_START_HOUR,
            'end': WITHDRAWAL_END_HOUR,
            'days': 'Monday - Friday'
        }
    })

@withdrawals_bp.route('/balance')
@login_required
def get_balance():
    """API endpoint to get user balance"""
    return jsonify({
        'balance': current_user.balance or 0,
        'formatted': f"KSH {current_user.balance:,.2f}"
    })