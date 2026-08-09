# wallet.py - Blueprint ONLY (NO utility functions)
from flask import Blueprint, render_template, redirect, url_for, flash, request
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

@wallet_bp.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    """Deposit funds - supports both manual and M-Pesa"""
    form = DepositForm()
    
    if request.method == 'POST':
        amount = request.form.get('amount', type=float)
        payment_method = request.form.get('payment_method', 'mpesa')
        phone = request.form.get('phone', '')
        
        logger.info(f"Deposit attempt: amount={amount}, method={payment_method}, phone={phone}")
        
        if not amount or amount <= 0:
            flash('Please enter a valid amount.', 'danger')
            return render_template('wallet/deposit.html', form=form)
        
        # If M-Pesa, initiate STK Push
        if payment_method == 'mpesa':
            if not phone:
                flash('Please enter your M-Pesa phone number.', 'danger')
                return render_template('wallet/deposit.html', form=form)
            
            try:
                from utils.mpesa import MpesaAPI
                
                # Format phone number
                phone_clean = re.sub(r'\D', '', phone)
                if phone_clean.startswith('0'):
                    phone_clean = '254' + phone_clean[1:]
                elif len(phone_clean) == 9:
                    phone_clean = '254' + phone_clean
                elif len(phone_clean) == 10 and not phone_clean.startswith('254'):
                    phone_clean = '254' + phone_clean[1:]
                
                if not phone_clean.startswith('254'):
                    phone_clean = '254' + phone_clean
                
                logger.info(f"Formatted phone: {phone_clean}")
                
                # Create transaction
                transaction = Transaction(
                    user_id=current_user.id,
                    type='deposit',
                    amount=amount,
                    fee=0,
                    net_amount=amount,
                    description='M-Pesa Deposit',
                    status='pending',
                    payment_method='mpesa',
                    payment_reference=phone_clean
                )
                db.session.add(transaction)
                db.session.commit()
                
                logger.info(f"Transaction created: {transaction.transaction_id}")
                
                # Initiate STK Push
                mpesa = MpesaAPI()
                result = mpesa.stk_push(
                    phone_number=phone_clean,
                    amount=amount,
                    account_reference=transaction.transaction_id,
                    transaction_desc='VCH Deposit'
                )
                
                logger.info(f"STK Push result: {result}")
                
                if result['success']:
                    transaction.payment_reference = result.get('checkout_request_id')
                    db.session.commit()
                    
                    flash('M-Pesa payment initiated. Please check your phone and enter your PIN.', 'success')
                    # FIXED: Correct route name for M-Pesa status page
                    return redirect(url_for('payments.mpesa_status', transaction_id=transaction.transaction_id))
                else:
                    transaction.status = 'failed'
                    db.session.commit()
                    flash(f'M-Pesa payment failed: {result.get("error", "Unknown error")}', 'danger')
                    return render_template('wallet/deposit.html', form=form)
                    
            except Exception as e:
                logger.error(f"Error in M-Pesa deposit: {e}")
                import traceback
                traceback.print_exc()
                flash(f'Error initiating M-Pesa payment: {str(e)}', 'danger')
                return render_template('wallet/deposit.html', form=form)
        
        # Regular deposit (non-M-Pesa)
        try:
            transaction = process_deposit(
                user_id=current_user.id,
                amount=amount,
                payment_method=payment_method,
                phone=phone
            )
            
            flash(f'Deposit of KSH {amount:,.2f} completed successfully!', 'success')
            return redirect(url_for('wallet.transactions'))
        
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'Error processing deposit: {str(e)}', 'danger')
    
    return render_template('wallet/deposit.html', form=form)

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
    today = datetime.now().date()
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