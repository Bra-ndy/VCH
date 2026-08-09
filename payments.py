# payments.py - Complete with M-Pesa integration
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
    """Handle M-Pesa payment callback"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'ResultCode': 1, 'ResultDesc': 'Invalid data'})
        
        logger.info(f"M-Pesa Callback received: {data}")
        
        # Extract callback data
        body = data.get('Body', {})
        stk_callback = body.get('stkCallback', {})
        
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        
        # Get callback metadata
        callback_metadata = stk_callback.get('CallbackMetadata', {})
        items = callback_metadata.get('Item', [])
        
        # Extract payment details
        amount = None
        mpesa_receipt = None
        phone = None
        
        for item in items:
            if item.get('Name') == 'Amount':
                amount = float(item.get('Value', 0))
            elif item.get('Name') == 'MpesaReceiptNumber':
                mpesa_receipt = item.get('Value')
            elif item.get('Name') == 'PhoneNumber':
                phone = item.get('Value')
        
        # Find transaction by checkout request ID
        transaction = Transaction.query.filter_by(
            payment_reference=checkout_request_id
        ).first()
        
        if not transaction:
            # Try to find by phone number if checkout request ID not found
            if phone:
                transaction = Transaction.query.filter_by(
                    payment_reference=phone,
                    status='pending'
                ).order_by(Transaction.created_at.desc()).first()
        
        if transaction:
            if result_code == '0' or result_code == 0:
                # Payment successful
                transaction.status = 'completed'
                transaction.completed_at = datetime.utcnow()
                transaction.payment_reference = mpesa_receipt or checkout_request_id
                
                # Update user balance
                user = User.query.get(transaction.user_id)
                if user:
                    user.balance += transaction.amount
                    user.total_deposited += transaction.amount
                    db.session.add(user)
                
                # Send notification
                notification = Notification(
                    user_id=transaction.user_id,
                    title='Deposit Successful',
                    message=f'Your deposit of KSH {transaction.amount:,.2f} via M-Pesa has been completed. Receipt: {mpesa_receipt}',
                    type='success'
                )
                db.session.add(notification)
                
                db.session.commit()
                logger.info(f"Payment completed for transaction: {transaction.transaction_id}")
                
                return jsonify({'ResultCode': 0, 'ResultDesc': 'Success'})
            else:
                # Payment failed
                transaction.status = 'failed'
                db.session.commit()
                
                # Send notification
                notification = Notification(
                    user_id=transaction.user_id,
                    title='Deposit Failed',
                    message=f'Your deposit of KSH {transaction.amount:,.2f} via M-Pesa failed. Reason: {result_desc}',
                    type='danger'
                )
                db.session.add(notification)
                db.session.commit()
                
                logger.warning(f"Payment failed for transaction: {transaction.transaction_id} - {result_desc}")
                return jsonify({'ResultCode': 0, 'ResultDesc': 'Success'})
        
        logger.warning(f"Transaction not found for checkout: {checkout_request_id}")
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Transaction not found'})
    
    except Exception as e:
        logger.error(f"MPesa callback error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Internal error'})

@payments_bp.route('/mpesa/validate', methods=['POST'])
def mpesa_validate():
    """Validate M-Pesa payment request"""
    return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'})

@payments_bp.route('/mpesa/confirm', methods=['POST'])
def mpesa_confirm():
    """Confirm M-Pesa payment"""
    return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'})

@payments_bp.route('/mpesa/query/<checkout_request_id>', methods=['GET'])
@login_required
def query_mpesa_status(checkout_request_id):
    """Query M-Pesa transaction status"""
    try:
        mpesa = MpesaAPI()
        result = mpesa.query_status(checkout_request_id)
        
        logger.info(f"Query result for {checkout_request_id}: {result}")
        
        if result['success']:
            # Update transaction status if needed
            transaction = Transaction.query.filter_by(
                payment_reference=checkout_request_id,
                user_id=current_user.id
            ).first()
            
            if transaction and transaction.status == 'pending':
                if result.get('status') == 'completed':
                    transaction.status = 'completed'
                    transaction.completed_at = datetime.utcnow()
                    
                    # Update user balance
                    user = User.query.get(transaction.user_id)
                    if user:
                        user.balance += transaction.amount
                        user.total_deposited += transaction.amount
                        db.session.add(user)
                    
                    db.session.commit()
                    
                    # Send notification
                    notification = Notification(
                        user_id=transaction.user_id,
                        title='Deposit Successful',
                        message=f'Your deposit of KSH {transaction.amount:,.2f} via M-Pesa has been completed.',
                        type='success'
                    )
                    db.session.add(notification)
                    db.session.commit()
                    
                    return jsonify({
                        'success': True,
                        'status': 'completed',
                        'mpesa_receipt': result.get('mpesa_receipt')
                    })
                elif result.get('status') == 'pending':
                    return jsonify({
                        'success': True,
                        'status': 'pending',
                        'message': 'Payment pending confirmation'
                    })
                else:
                    transaction.status = 'failed'
                    db.session.commit()
                    return jsonify({
                        'success': True,
                        'status': 'failed',
                        'message': result.get('result_desc', 'Payment failed')
                    })
            
            return jsonify(result)
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Query failed')})
            
    except Exception as e:
        logger.error(f"Query M-Pesa status error: {e}")
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

@payments_bp.route('/status/<transaction_id>')
@login_required
def payment_status(transaction_id):
    """Check payment status"""
    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id,
        user_id=current_user.id
    ).first()
    
    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404
    
    return jsonify({
        'status': transaction.status,
        'amount': transaction.amount,
        'created_at': transaction.created_at.isoformat(),
        'completed_at': transaction.completed_at.isoformat() if transaction.completed_at else None
    })

@payments_bp.route('/mpesa/test', methods=['GET'])
def test_mpesa():
    """Test M-Pesa integration"""
    try:
        from utils.mpesa import MpesaAPI
        
        mpesa = MpesaAPI()
        
        # Check if credentials are set
        if not mpesa.consumer_key or mpesa.consumer_key == 'your_consumer_key_here':
            return jsonify({
                'success': False,
                'message': 'Consumer Key not set. Please add MPESA_CONSUMER_KEY to .env file'
            }), 400
        
        if not mpesa.consumer_secret or mpesa.consumer_secret == 'your_consumer_secret_here':
            return jsonify({
                'success': False,
                'message': 'Consumer Secret not set. Please add MPESA_CONSUMER_SECRET to .env file'
            }), 400
        
        # Test access token
        token = mpesa.get_access_token()
        
        if token:
            return jsonify({
                'success': True,
                'message': 'M-Pesa connection successful!',
                'environment': mpesa.environment,
                'token_preview': token[:20] + '...'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'M-Pesa connection failed. Check your credentials.',
                'environment': mpesa.environment
            }), 400
            
    except Exception as e:
        logger.error(f"Test M-Pesa error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500