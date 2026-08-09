# utils/earnings.py - Complete version
from datetime import datetime, timedelta
from flask import current_app
from models import db, Rental, Transaction, User, Notification
import logging

logger = logging.getLogger(__name__)

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
        
        # Check if rental period is complete
        if rental.days_elapsed >= 30:
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

def process_rental(user_id, vehicle_id, rental_period=30):
    """Process a new rental"""
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
        
        # Check balance
        if user.balance < vehicle.rental_price:
            raise ValueError(f"Insufficient balance. Need KSH {vehicle.rental_price:,.2f}")
        
        # Create rental
        rental = Rental(
            user_id=user_id,
            vehicle_id=vehicle_id,
            amount=vehicle.rental_price,
            daily_earning=vehicle.daily_earning,
            total_profit=vehicle.total_profit if hasattr(vehicle, 'total_profit') else (vehicle.daily_earning * rental_period - vehicle.rental_price),
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=rental_period)
        )
        db.session.add(rental)
        
        # Deduct from user balance
        user.balance -= vehicle.rental_price
        
        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            type='rental_purchase',
            amount=vehicle.rental_price,
            fee=0,
            net_amount=-vehicle.rental_price,
            description=f'Rented {vehicle.name}',
            status='completed',
            reference=rental.rental_id
        )
        db.session.add(transaction)
        
        # Create notification
        notification = Notification(
            user_id=user_id,
            title='Car Rented Successfully',
            message=f'You have rented {vehicle.name}. You will earn KSH {vehicle.daily_earning:,.2f} per day.',
            type='success'
        )
        db.session.add(notification)
        
        db.session.commit()
        
        return rental
        
    except Exception as e:
        logger.error(f"Error processing rental: {e}")
        db.session.rollback()
        raise

def process_service_earning(user_id):
    """Process daily service earning"""
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
            earning=50.0,
            service_date=datetime.utcnow()
        )
        db.session.add(service)
        
        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            type='service_earning',
            amount=50.0,
            fee=0,
            net_amount=50.0,
            description='Daily servicing earning',
            status='completed'
        )
        db.session.add(transaction)
        
        # Update user balance
        user = User.query.get(user_id)
        if user:
            user.balance += 50.0
            user.total_earned += 50.0
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