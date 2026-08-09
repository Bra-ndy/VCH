# utils/referral.py - Complete file with all required functions
from datetime import datetime
from flask import current_app
from models import db, User, ReferralBonus, Transaction, Notification
import logging

logger = logging.getLogger(__name__)

def process_referral_bonus(referrer_id, referred_id):
    """Process referral signup bonus"""
    try:
        # Get users
        referrer = User.query.get(referrer_id)
        referred = User.query.get(referred_id)
        
        if not referrer or not referred:
            raise ValueError("User not found")
        
        # Check if bonus already given
        existing = ReferralBonus.query.filter_by(
            referrer_id=referrer_id,
            referred_id=referred_id,
            type='signup_bonus'
        ).first()
        
        if existing:
            return None
        
        # Calculate bonus (10% of joining member's first deposit)
        # For now, we give a fixed bonus of 100
        bonus_amount = 100.0
        
        # Create referral bonus
        bonus = ReferralBonus(
            referrer_id=referrer_id,
            referred_id=referred_id,
            amount=bonus_amount,
            type='signup_bonus',
            is_paid=True,
            paid_at=datetime.utcnow()
        )
        db.session.add(bonus)
        
        # Create transaction
        transaction = Transaction(
            user_id=referrer_id,
            type='referral_bonus',
            amount=bonus_amount,
            fee=0,
            net_amount=bonus_amount,
            description=f'Signup bonus from {referred.username}',
            status='completed'
        )
        db.session.add(transaction)
        
        # Update referrer balance
        referrer.balance += bonus_amount
        referrer.total_earned += bonus_amount
        db.session.add(referrer)
        
        db.session.commit()
        
        # Send notification to referrer
        notification = Notification(
            user_id=referrer_id,
            title='Referral Bonus',
            message=f'You earned KSH {bonus_amount:,.2f} for referring {referred.username}!',
            type='success'
        )
        db.session.add(notification)
        db.session.commit()
        
        return bonus
        
    except Exception as e:
        logger.error(f"Error processing referral bonus: {e}")
        db.session.rollback()
        return None

def calculate_referral_commission(referrer_id, referred_earning):
    """Calculate referral commission on daily earnings"""
    try:
        # 2% commission on referred user's daily earnings
        commission = referred_earning * 0.02
        
        if commission <= 0:
            return None
        
        # Create referral bonus
        bonus = ReferralBonus(
            referrer_id=referrer_id,
            referred_id=None,  # We don't track individual referral for commission
            amount=commission,
            type='commission',
            is_paid=True,
            paid_at=datetime.utcnow()
        )
        db.session.add(bonus)
        
        # Create transaction
        transaction = Transaction(
            user_id=referrer_id,
            type='referral_bonus',
            amount=commission,
            fee=0,
            net_amount=commission,
            description='Commission from referral earnings',
            status='completed'
        )
        db.session.add(transaction)
        
        # Update referrer balance
        referrer = User.query.get(referrer_id)
        if referrer:
            referrer.balance += commission
            referrer.total_earned += commission
            db.session.add(referrer)
        
        db.session.commit()
        
        return commission
        
    except Exception as e:
        logger.error(f"Error calculating referral commission: {e}")
        db.session.rollback()
        return None

def get_referral_stats(user_id):
    """Get referral statistics for a user"""
    try:
        # Total referrals
        total_referrals = User.query.filter_by(referred_by=user_id).count()
        
        # Active referrals (users who have earned at least once)
        active_referrals = User.query.filter(
            User.referred_by == user_id,
            User.total_earned > 0
        ).count()
        
        # Total referral earnings
        total_earnings = db.session.query(db.func.sum(Transaction.amount))\
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == 'referral_bonus',
                Transaction.status == 'completed'
            ).scalar() or 0
        
        # Current agent level
        from config import Config
        user = User.query.get(user_id)
        current_level = user.agent_level if user else 'none'
        
        # Next level progress
        next_level = None
        required = 0
        if current_level == 'none':
            next_level = 'junior'
            required = Config.AGENT_LEVELS['junior']['members']
        elif current_level == 'junior':
            next_level = 'level1'
            required = Config.AGENT_LEVELS['level1']['members']
        elif current_level == 'level1':
            next_level = 'level2'
            required = Config.AGENT_LEVELS['level2']['members']
        
        progress = min(100, (total_referrals / required * 100)) if required > 0 else 100
        
        return {
            'total_referrals': total_referrals,
            'active_referrals': active_referrals,
            'total_earnings': total_earnings,
            'current_level': current_level,
            'next_level': next_level,
            'members_required': required,
            'progress': progress,
            'salary': user.get_agent_salary() if user else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting referral stats: {e}")
        return None