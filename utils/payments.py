# payments.py - Complete with all routes
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime
import json
import logging

from models import db, Transaction, Notification, User
from utils.mpesa import MpesaAPI

logger = logging.getLogger(__name__)

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

@payments_bp.route('/mpesa/initiate', methods=['POST'])
@login_required
def initiate_mpesa_payment():
    """Initiate M-Pesa STK Push payment"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Invalid data'}), 400
        
        phone = data.get('phone')
        amount = float(data.get('amount', 0))
        
        if not phone or amount <= 0:
            return jsonify({'success': False, 'error': 'Invalid phone or amount'}), 400
        
        # Format phone number
        import re
        phone = re.sub(r'\D', '', str(phone))
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif len(phone) == 9:
            phone = '254' + phone
        elif len(phone) == 10 and not phone.startswith('254'):
            phone = '254' + phone[1:]
        
        if not phone.startswith('254'):
            phone = '254' + phone
        
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
            payment_reference=phone
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Initiate STK Push
        mpesa = MpesaAPI()
        result = mpesa.stk_push(
            phone_number=phone,
            amount=amount,
            account_reference=transaction.transaction_id,
            transaction_desc=f'VCH Deposit'
        )
        
        if result['success']:
            transaction.payment_reference = result.get('checkout_request_id')
            db.session.commit()
            
            return jsonify({
                'success': True,
                'checkout_request_id': result.get('checkout_request_id'),
                'transaction_id': transaction.transaction_id,
                'message': 'STK Push sent successfully'
            })
        else:
            transaction.status = 'failed'
            db.session.commit()
            return jsonify({'success': False, 'error': result.get('error', 'Payment failed')}), 400
        
    except Exception as e:
        logger.error(f"Initiate M-Pesa error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@payments_bp.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """Handle M-Pesa callback"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'ResultCode': 1, 'ResultDesc': 'Invalid data'})
        
        logger.info(f"M-Pesa Callback received: {data}")
        
        body = data.get('Body', {})
        stk_callback = body.get('stkCallback', {})
        
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        
        # Find transaction
        transaction = Transaction.query.filter_by(
            payment_reference=checkout_request_id
        ).first()
        
        if transaction:
            if result_code == '0':
                transaction.status = 'completed'
                transaction.completed_at = datetime.utcnow()
                
                user = User.query.get(transaction.user_id)
                if user:
                    user.balance += transaction.amount
                    user.total_deposited += transaction.amount
                    db.session.add(user)
                
                notification = Notification(
                    user_id=transaction.user_id,
                    title='Deposit Successful',
                    message=f'Your deposit of KSH {transaction.amount:,.2f} via M-Pesa has been completed.',
                    type='success'
                )
                db.session.add(notification)
                db.session.commit()
                
                return jsonify({'ResultCode': 0, 'ResultDesc': 'Success'})
            else:
                transaction.status = 'failed'
                db.session.commit()
                return jsonify({'ResultCode': 0, 'ResultDesc': 'Success'})
        
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Transaction not found'})
        
    except Exception as e:
        logger.error(f"M-Pesa callback error: {e}")
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Internal error'})

@payments_bp.route('/mpesa/query/<checkout_request_id>', methods=['GET'])
@login_required
def query_mpesa_status(checkout_request_id):
    """Query M-Pesa transaction status"""
    try:
        mpesa = MpesaAPI()
        result = mpesa.query_status(checkout_request_id)
        
        if result['success']:
            transaction = Transaction.query.filter_by(
                payment_reference=checkout_request_id,
                user_id=current_user.id
            ).first()
            
            if transaction and transaction.status == 'pending':
                if result.get('status') == 'completed':
                    transaction.status = 'completed'
                    transaction.completed_at = datetime.utcnow()
                    
                    user = User.query.get(transaction.user_id)
                    if user:
                        user.balance += transaction.amount
                        user.total_deposited += transaction.amount
                        db.session.add(user)
                    
                    db.session.commit()
                    
                    return jsonify({
                        'success': True,
                        'status': 'completed',
                        'mpesa_receipt': result.get('mpesa_receipt')
                    })
                elif result.get('status') == 'pending':
                    return jsonify({'success': True, 'status': 'pending', 'message': 'Payment pending'})
                else:
                    transaction.status = 'failed'
                    db.session.commit()
                    return jsonify({'success': True, 'status': 'failed', 'message': result.get('result_desc')})
            
            return jsonify(result)
        else:
            return jsonify({'success': False, 'error': result.get('error')})
            
    except Exception as e:
        logger.error(f"Query M-Pesa error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@payments_bp.route('/mpesa/status/<transaction_id>')
@login_required
def mpesa_status(transaction_id):
    """Show M-Pesa payment status page"""
    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id,
        user_id=current_user.id
    ).first_or_404()
    
    checkout_request_id = transaction.payment_reference
    
    return render_template('wallet/mpesa_status.html',
                         checkout_request_id=checkout_request_id,
                         transaction_id=transaction_id,
                         amount=transaction.amount)

@payments_bp.route('/mpesa/test', methods=['GET'])
def test_mpesa():
    """Test M-Pesa integration"""
    try:
        mpesa = MpesaAPI()
        token = mpesa.get_access_token()
        
        if token:
            return jsonify({
                'success': True,
                'message': 'M-Pesa connection successful!',
                'environment': mpesa.environment
            })
        else:
            return jsonify({
                'success': False,
                'message': 'M-Pesa connection failed.'
            }), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500