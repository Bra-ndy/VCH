# utils/earnings.py - Complete version with rental period support
from datetime import datetime, timedelta
from flask import current_app
from models import db, Rental, Transaction, User, Notification, Vehicle
import logging

logger = logging.getLogger(__name__)

# Service earning amount
SERVICE_AMOUNT = 5.0  # KSH 5 per day

def calculate_rental_earning(rental):
    """Calculate daily earning for a rental"""
    try:
        # Check if rental is active
        if rental.status != 'active':
            return None
        
        # Check if already earned today
        today = datetime.utcnow().date()
        last_earning = rental.last_earning_date
        
        if last_earning and last_earning.date() == today:
            return None
        
        # Calculate earning
        earning = rental.daily_earning
        
        # Update rental
        rental.days_elapsed += 1
        rental.total_earned += earning
        rental.last_earning_date = datetime.utcnow()
        
        # Check if rental period is complete (using rental_period)
        if rental.days_elapsed >= rental.rental_period:
            rental.status = 'completed'
            rental.completed_at = datetime.utcnow()
        
        db.session.add(rental)
        
        # Create transaction
        transaction = Transaction(
            user_id=rental.user_id,
            type='rental_earning',
            amount=earning,
            fee=0,
            net_amount=earning,
            description=f'Daily earning from {rental.vehicle.name} rental',
            status='completed',
            reference=rental.rental_id
        )
        db.session.add(transaction)
        
        # Update user balance
        user = User.query.get(rental.user_id)
        if user:
            user.balance += earning
            user.total_earned += earning
            db.session.add(user)
        
        db.session.commit()
        
        return earning
        
    except Exception as e:
        logger.error(f"Error calculating rental earning: {e}")
        db.session.rollback()
        return None

def process_rental(user_id, vehicle_id, rental_period=None):
    """Process a new rental with proper period support"""
    try:
        from models import Vehicle, Rental, User
        
        # Get vehicle
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            raise ValueError("Vehicle not found")
        
        if not vehicle.is_available:
            raise ValueError("Vehicle is not available")
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Use vehicle's rental period if not provided
        if not rental_period:
            rental_period = vehicle.rental_period
        
        # Check balance
        if user.balance < vehicle.rental_price:
            raise ValueError(f"Insufficient balance. Need KSH {vehicle.rental_price:,.2f}")
        
        # Calculate total profit
        total_profit = (vehicle.daily_earning * rental_period) - vehicle.rental_price
        
        # Create rental with proper period
        rental = Rental(
            user_id=user_id,
            vehicle_id=vehicle_id,
            amount=vehicle.rental_price,
            daily_earning=vehicle.daily_earning,
            total_profit=total_profit,
            rental_period=rental_period,  # ← SAVE THE RENTAL PERIOD
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=rental_period)
        )
        db.session.add(rental)
        
        # Deduct from user balance
        user.balance -= vehicle.rental_price
        
        # Create transaction for rental purchase
        transaction = Transaction(
            user_id=user_id,
            type='rental_purchase',
            amount=vehicle.rental_price,
            fee=0,
            net_amount=-vehicle.rental_price,
            description=f'Rented {vehicle.name} for {rental_period} days',
            status='completed',
            reference=rental.rental_id
        )
        db.session.add(transaction)
        
        # Mark vehicle as unavailable
        vehicle.is_available = False
        db.session.add(vehicle)
        
        # Create notification
        notification = Notification(
            user_id=user_id,
            title='Car Rented Successfully 🚗',
            message=f'You have rented {vehicle.name} for {rental_period} days. You will earn KSH {vehicle.daily_earning:,.2f} per day.',
            type='success'
        )
        db.session.add(notification)
        
        db.session.commit()
        
        logger.info(f"✅ Rental created: {rental.rental_id} for {rental_period} days")
        
        return rental
        
    except Exception as e:
        logger.error(f"Error processing rental: {e}")
        db.session.rollback()
        raise

def process_service_earning(user_id):
    """Process daily service earning (KSH 5 per day)"""
    try:
        from models import ServiceHistory, Transaction, User, Notification
        
        # Check if already serviced today
        today = datetime.utcnow().date()
        existing = ServiceHistory.query.filter(
            ServiceHistory.user_id == user_id,
            db.func.date(ServiceHistory.service_date) == today
        ).first()
        
        if existing:
            raise ValueError("Daily servicing already performed today")
        
        # Create service record
        service = ServiceHistory(
            user_id=user_id,
            type='daily_servicing',
            earning=SERVICE_AMOUNT,
            service_date=datetime.utcnow()
        )
        db.session.add(service)
        
        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            type='service_earning',
            amount=SERVICE_AMOUNT,
            fee=0,
            net_amount=SERVICE_AMOUNT,
            description=f'Daily servicing earning - KSH {SERVICE_AMOUNT:.2f}',
            status='completed'
        )
        db.session.add(transaction)
        
        # Update user balance
        user = User.query.get(user_id)
        if user:
            user.balance += SERVICE_AMOUNT
            user.total_earned += SERVICE_AMOUNT
            db.session.add(user)
        
        db.session.commit()
        
        return service
        
    except Exception as e:
        logger.error(f"Error processing service earning: {e}")
        db.session.rollback()
        raise

def process_referral_commission(referrer_id, referred_id, amount):
    """Process referral commission"""
    try:
        from models import ReferralBonus, Transaction, User, Notification
        
        # Calculate commission (2% of daily earnings)
        commission = amount * 0.02
        
        if commission <= 0:
            return None
        
        # Create referral bonus
        bonus = ReferralBonus(
            referrer_id=referrer_id,
            referred_id=referred_id,
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
            description=f'Commission from referral earnings',
            status='completed'
        )
        db.session.add(transaction)
        
        # Update user balance
        user = User.query.get(referrer_id)
        if user:
            user.balance += commission
            user.total_earned += commission
            db.session.add(user)
        
        db.session.commit()
        
        return commission
        
    except Exception as e:
        logger.error(f"Error processing referral commission: {e}")
        db.session.rollback()
        return None

def get_daily_earnings(user_id):
    """Get total daily earnings for a user"""
    try:
        # Get active rentals
        rentals = Rental.query.filter_by(user_id=user_id, status='active').all()
        
        total_daily = 0
        for rental in rentals:
            if rental.status == 'active' and not rental.is_expired():
                total_daily += rental.daily_earning
        
        return total_daily
        
    except Exception as e:
        logger.error(f"Error getting daily earnings: {e}")
        return 0

def get_total_earnings(user_id):
    """Get total earnings from all sources for a user"""
    try:
        total = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type.in_(['rental_earning', 'service_earning', 'referral_bonus', 'welcome_bonus'])
        ).scalar() or 0
        
        return total
        
    except Exception as e:
        logger.error(f"Error getting total earnings: {e}")
        return 0