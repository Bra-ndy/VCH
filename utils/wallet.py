# utils/wallet.py - Utility functions ONLY (NO flask imports, NO blueprint)
from datetime import datetime
from flask import current_app
from models import db, User, Transaction, Notification
import logging

logger = logging.getLogger(__name__)

def process_deposit(user_id, amount, payment_method='mpesa', phone=None):
    """Process a deposit"""
    try:
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        
        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            type='deposit',
            amount=amount,
            fee=0,
            net_amount=amount,
            description=f'Deposit via {payment_method}',
            status='completed',
            payment_method=payment_method,
            payment_reference=phone or ''
        )
        db.session.add(transaction)
        
        # Update user balance
        user.balance += amount
        user.total_deposited += amount
        db.session.add(user)
        
        db.session.commit()
        
        # Send notification
        notification = Notification(
            user_id=user_id,
            title='Deposit Completed',
            message=f'Your deposit of KSH {amount:,.2f} has been completed.',
            type='success'
        )
        db.session.add(notification)
        db.session.commit()
        
        return transaction
        
    except Exception as e:
        logger.error(f"Error processing deposit: {e}")
        db.session.rollback()
        raise

def process_withdrawal(user_id, amount, phone):
    """Process a withdrawal request"""
    try:
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        if amount <= 0:
            raise ValueError("Invalid amount")
        
        # Validate withdrawal limits
        min_withdrawal = current_app.config.get('MINIMUM_WITHDRAWAL', 100)
        max_withdrawal = current_app.config.get('MAXIMUM_WITHDRAWAL', 50000)
        
        if amount < min_withdrawal:
            raise ValueError(f"Minimum withdrawal is KSH {min_withdrawal:,.2f}")
        
        if amount > max_withdrawal:
            raise ValueError(f"Maximum withdrawal is KSH {max_withdrawal:,.2f}")
        
        if user.balance < amount:
            raise ValueError(f"Insufficient balance. Available: KSH {user.balance:,.2f}")
        
        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            type='withdrawal',
            amount=amount,
            fee=0,
            net_amount=-amount,
            description=f'Withdrawal to {phone}',
            status='completed',
            payment_method='mpesa',
            payment_reference=phone
        )
        db.session.add(transaction)
        
        # Deduct from user balance
        user.balance -= amount
        user.total_withdrawn += amount
        db.session.add(user)
        
        db.session.commit()
        
        # Send notification
        notification = Notification(
            user_id=user_id,
            title='Withdrawal Completed',
            message=f'Your withdrawal of KSH {amount:,.2f} has been processed.',
            type='success'
        )
        db.session.add(notification)
        db.session.commit()
        
        return transaction
        
    except Exception as e:
        logger.error(f"Error processing withdrawal: {e}")
        db.session.rollback()
        raise

def process_agent_salary(user_id):
    """Process agent salary"""
    try:
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        if user.agent_level == 'none':
            return None
        
        salary = user.get_agent_salary()
        if salary <= 0:
            return None
        
        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            type='agent_salary',
            amount=salary,
            fee=0,
            net_amount=salary,
            description=f'Agent salary - {user.agent_level}',
            status='completed'
        )
        db.session.add(transaction)
        
        # Update user balance
        user.balance += salary
        user.total_earned += salary
        user.agent_salary_earned += salary
        db.session.add(user)
        
        db.session.commit()
        
        return salary
        
    except Exception as e:
        logger.error(f"Error processing agent salary: {e}")
        db.session.rollback()
        return None