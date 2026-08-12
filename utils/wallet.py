# utils/wallet.py - Utility functions ONLY (NO flask imports, NO blueprint)
from datetime import datetime
from flask import current_app
from models import db, User, Transaction, Notification
import logging

logger = logging.getLogger(__name__)

# =============================================
# CORE WALLET FUNCTIONS
# =============================================

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

# =============================================
# ADMIN DEPOSIT VERIFICATION FUNCTIONS
# =============================================

def create_pending_deposit(user_id, amount, transaction_code, phone):
    """Create a pending deposit for admin verification"""
    try:
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        
        if not transaction_code:
            raise ValueError("Transaction code is required")
        
        # Check for duplicate transaction code
        existing = Transaction.query.filter_by(
            payment_reference=transaction_code,
            type='deposit'
        ).first()
        
        if existing:
            raise ValueError("Transaction code already exists. Please check your deposits.")
        
        # Create pending transaction
        transaction = Transaction(
            user_id=user_id,
            type='deposit',
            amount=amount,
            fee=0,
            net_amount=amount,
            description=f'M-Pesa Deposit - Code: {transaction_code}',
            status='pending',
            payment_method='mpesa_manual',
            payment_reference=transaction_code
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Create notification for user
        notification = Notification(
            user_id=user_id,
            title='Deposit Submitted',
            message=f'Your deposit of KSH {amount:,.2f} has been submitted for verification. Transaction code: {transaction_code}',
            type='info'
        )
        db.session.add(notification)
        
        # Create notification for admin
        from models import User
        admins = User.query.filter(
            db.or_(
                User.email == 'admin@vch.com',
                User.agent_level == 'level2',
                User.username == 'admin'
            )
        ).all()
        
        for admin in admins:
            admin_notification = Notification(
                user_id=admin.id,
                title='New Deposit Pending',
                message=f'User {user.username} deposited KSH {amount:,.2f}. Code: {transaction_code}. Please verify.',
                type='warning',
                link=f'/admin/deposits/pending'
            )
            db.session.add(admin_notification)
        
        db.session.commit()
        
        return transaction
        
    except Exception as e:
        logger.error(f"Error creating pending deposit: {e}")
        db.session.rollback()
        raise

def verify_deposit(transaction_id, admin_id, action='approve'):
    """Verify or reject a pending deposit"""
    try:
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            raise ValueError("Transaction not found")
        
        if transaction.status != 'pending':
            raise ValueError(f"Transaction is already {transaction.status}")
        
        if transaction.payment_method != 'mpesa_manual':
            raise ValueError("This transaction does not require admin verification")
        
        admin = User.query.get(admin_id)
        if not admin:
            raise ValueError("Admin not found")
        
        if action == 'approve':
            # Approve the deposit
            transaction.status = 'completed'
            transaction.completed_at = datetime.utcnow()
            
            # Update user balance
            user = User.query.get(transaction.user_id)
            if user:
                user.balance += transaction.amount
                user.total_deposited += transaction.amount
                db.session.add(user)
            
            # Send notification to user
            notification = Notification(
                user_id=transaction.user_id,
                title='Deposit Approved',
                message=f'Your deposit of KSH {transaction.amount:,.2f} has been verified and added to your wallet.',
                type='success'
            )
            db.session.add(notification)
            
            # Log admin action
            logger.info(f"Admin {admin.username} approved deposit {transaction.transaction_id}")
            
        elif action == 'reject':
            # Reject the deposit
            transaction.status = 'failed'
            
            # Send notification to user
            notification = Notification(
                user_id=transaction.user_id,
                title='Deposit Rejected',
                message=f'Your deposit of KSH {transaction.amount:,.2f} was rejected. Please contact support or try again.',
                type='danger'
            )
            db.session.add(notification)
            
            # Log admin action
            logger.info(f"Admin {admin.username} rejected deposit {transaction.transaction_id}")
        
        else:
            raise ValueError("Invalid action. Use 'approve' or 'reject'")
        
        db.session.commit()
        return transaction
        
    except Exception as e:
        logger.error(f"Error verifying deposit: {e}")
        db.session.rollback()
        raise

def get_pending_deposits():
    """Get all pending deposits for admin verification"""
    try:
        deposits = Transaction.query.filter(
            Transaction.type == 'deposit',
            Transaction.status == 'pending',
            Transaction.payment_method == 'mpesa_manual'
        ).order_by(Transaction.created_at.desc()).all()
        
        return deposits
        
    except Exception as e:
        logger.error(f"Error getting pending deposits: {e}")
        return []

def get_user_deposits(user_id, limit=10):
    """Get user's deposit history"""
    try:
        deposits = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.type == 'deposit'
        ).order_by(Transaction.created_at.desc()).limit(limit).all()
        
        return deposits
        
    except Exception as e:
        logger.error(f"Error getting user deposits: {e}")
        return []

def get_admin_number():
    """Get admin M-Pesa number from config"""
    try:
        return current_app.config.get('ADMIN_MPESA_NUMBER', '0753796259')
    except:
        return '0753796259'

def get_admin_name():
    """Get admin name from config"""
    try:
        return current_app.config.get('ADMIN_NAME', 'WINNY LANGAT')
    except:
        return 'WINNY LANGAT'