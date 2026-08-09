from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from models import db, Transaction, Notification
from forms import WithdrawForm
from utils.wallet import process_withdrawal

withdrawals_bp = Blueprint('withdrawals', __name__, url_prefix='/withdrawals')

@withdrawals_bp.route('/')
@login_required
def index():
    return render_template('wallet/withdraw.html')

@withdrawals_bp.route('/request', methods=['POST'])
@login_required
def request_withdrawal():
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
        
        transaction = process_withdrawal(
            user_id=current_user.id,
            amount=amount,
            phone=phone
        )
        
        return jsonify({
            'success': True,
            'transaction_id': transaction.transaction_id,
            'amount': transaction.amount,
            'status': transaction.status
        })
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@withdrawals_bp.route('/history')
@login_required
def history():
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
    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id,
        user_id=current_user.id,
        status='pending'
    ).first()
    
    if not transaction:
        flash('Transaction not found or cannot be cancelled', 'danger')
        return redirect(url_for('withdrawals.history'))
    
    transaction.status = 'cancelled'
    db.session.commit()
    
    flash('Withdrawal cancelled successfully', 'success')
    return redirect(url_for('withdrawals.history'))