# wallet.py - Complete wallet blueprint with all routes
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
import re
import logging

from models import db, User, Transaction, Notification
from forms import DepositForm, WithdrawForm
from utils.wallet import process_deposit, process_withdrawal

logger = logging.getLogger(__name__)

wallet_bp = Blueprint('wallet', __name__, url_prefix='/wallet')

@wallet_bp.route('/')
@login_required
def wallet():
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.created_at.desc()).limit(10).all()
    
    return render_template('wallet/wallet.html', 
                         recent_transactions=recent_transactions)

# =============================================
# DEPOSIT - DISABLED STK PUSH, USING MANUAL ONLY
# =============================================
@wallet_bp.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    """Deposit funds - Manual deposit via admin only (STK Push disabled)"""
    form = DepositForm()
    recent_deposits = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'deposit'
    ).order_by(Transaction.created_at.desc()).limit(10).all()
    
    # Get admin info from config
    admin_name = current_app.config.get('ADMIN_NAME', 'WINNY LANGAT')
    admin_number = current_app.config.get('ADMIN_MPESA_NUMBER', '0753796259')
    
    # STK Push is disabled - Coming Soon
    # Redirect to manual deposit page if POST request
    if request.method == 'POST':
        flash('STK Push is coming soon! Please use the manual deposit option via admin.', 'info')
        return redirect(url_for('wallet.deposit_mpesa'))
    
    return render_template('wallet/deposit.html', 
                         form=form, 
                         recent_deposits=recent_deposits, 
                         admin_name=admin_name, 
                         admin_number=admin_number)

# =============================================
# DEPOSIT VIA ADMIN (Manual M-Pesa Verification)
# =============================================
@wallet_bp.route('/deposit/mpesa', methods=['GET', 'POST'])
@login_required
def deposit_mpesa():
    """Deposit via M-Pesa - Admin verification required"""
    
    # Get admin info from config
    admin_name = current_app.config.get('ADMIN_NAME', 'WINNY LANGAT')
    admin_number = current_app.config.get('ADMIN_MPESA_NUMBER', '0753796259')
    
    # Get recent deposits
    recent_deposits = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'deposit',
        Transaction.payment_method == 'mpesa_manual'
    ).order_by(Transaction.created_at.desc()).limit(10).all()
    
    if request.method == 'POST':
        amount = request.form.get('amount', type=float)
        transaction_code = request.form.get('transaction_code', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # Validate
        errors = []
        if not amount or amount <= 0:
            errors.append('Please enter a valid amount')
        if not transaction_code:
            errors.append('Please enter your M-Pesa transaction code')
        if not phone:
            errors.append('Please enter your phone number')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('wallet/deposit_mpesa.html', 
                                 admin_name=admin_name,
                                 admin_number=admin_number,
                                 recent_deposits=recent_deposits)
        
        # Format phone number
        phone = re.sub(r'\D', '', phone)
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif len(phone) == 9:
            phone = '254' + phone
        elif len(phone) == 10 and not phone.startswith('254'):
            phone = '254' + phone[1:]
        
        try:
            # Create pending deposit
            from utils.wallet import create_pending_deposit
            transaction = create_pending_deposit(
                user_id=current_user.id,
                amount=amount,
                transaction_code=transaction_code,
                phone=phone
            )
            
            flash(f'Deposit submitted successfully! Your transaction code {transaction_code} is being verified.', 'success')
            return redirect(url_for('wallet.deposit_mpesa'))
            
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            logger.error(f"Deposit M-Pesa error: {e}")
            flash('Error submitting deposit. Please try again.', 'danger')
    
    return render_template('wallet/deposit_mpesa.html', 
                         admin_name=admin_name,
                         admin_number=admin_number,
                         recent_deposits=recent_deposits)

# =============================================
# STK PUSH - COMING SOON (Disabled)
# =============================================
@wallet_bp.route('/deposit/stk-push')
@login_required
def stk_push_coming_soon():
    """Show coming soon message for STK Push"""
    flash('STK Push feature is coming soon! Please use the manual deposit option via admin.', 'info')
    return redirect(url_for('wallet.deposit'))

# =============================================
# OTHER WALLET ROUTES
# =============================================

@wallet_bp.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    """Withdraw funds"""
    form = WithdrawForm()
    
    if request.method == 'POST':
        amount = request.form.get('amount', type=float)
        phone = request.form.get('phone', '')
        
        if not amount or amount <= 0:
            flash('Please enter a valid amount.', 'danger')
            return render_template('wallet/withdraw.html', form=form)
        
        if amount < 100:
            flash('Minimum withdrawal is KSH 100', 'danger')
            return render_template('wallet/withdraw.html', form=form)
        
        if amount > 50000:
            flash('Maximum withdrawal is KSH 50,000', 'danger')
            return render_template('wallet/withdraw.html', form=form)
        
        if not phone:
            flash('Please enter your phone number.', 'danger')
            return render_template('wallet/withdraw.html', form=form)
        
        try:
            transaction = process_withdrawal(
                user_id=current_user.id,
                amount=amount,
                phone=phone
            )
            
            flash(f'Withdrawal of KSH {amount:,.2f} submitted successfully!', 'success')
            return redirect(url_for('wallet.transactions'))
        
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'Error processing withdrawal: {str(e)}', 'danger')
    
    return render_template('wallet/withdraw.html', form=form)

@wallet_bp.route('/transactions')
@login_required
def transactions():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('wallet/transactions.html', transactions=transactions)

@wallet_bp.route('/earnings')
@login_required
def earnings():
    today = datetime.utcnow().date()
    today_earnings = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        db.func.date(Transaction.created_at) == today,
        Transaction.type.in_(['rental_earning', 'service_earning', 'referral_bonus', 'agent_salary'])
    ).all()
    today_earnings_total = sum(t.amount for t in today_earnings)
    
    week_start = today - timedelta(days=today.weekday())
    week_earnings = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        db.func.date(Transaction.created_at) >= week_start,
        Transaction.type.in_(['rental_earning', 'service_earning', 'referral_bonus', 'agent_salary'])
    ).all()
    week_earnings_total = sum(t.amount for t in week_earnings)
    
    month_start = today.replace(day=1)
    month_earnings = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        db.func.date(Transaction.created_at) >= month_start,
        Transaction.type.in_(['rental_earning', 'service_earning', 'referral_bonus', 'agent_salary'])
    ).all()
    month_earnings_total = sum(t.amount for t in month_earnings)
    
    earnings_by_type = db.session.query(
        Transaction.type,
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type.in_(['rental_earning', 'service_earning', 'referral_bonus', 'agent_salary'])
    ).group_by(Transaction.type).all()
    
    earnings_by_type_dict = {e[0]: float(e[1]) for e in earnings_by_type}
    
    return render_template('wallet/earnings.html',
                         today_earnings_total=today_earnings_total,
                         week_earnings_total=week_earnings_total,
                         month_earnings_total=month_earnings_total,
                         earnings_by_type=earnings_by_type_dict)

@wallet_bp.route('/statements')
@login_required
def statements():
    return render_template('wallet/statements.html')