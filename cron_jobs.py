# cron_jobs.py
from app import create_app, db
from models import Rental, Transaction, User, Notification
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def process_daily_earnings():
    """Process daily earnings for all active rentals"""
    app = create_app()
    with app.app_context():
        try:
            logger.info("🔄 Starting daily earnings processing...")
            
            # Get all active rentals
            rentals = Rental.query.filter_by(status='active').all()
            
            if not rentals:
                logger.info("ℹ️ No active rentals found")
                return
            
            processed = 0
            today = datetime.utcnow().date()
            
            for rental in rentals:
                # Check if already earned today
                last_earning = rental.last_earning_date
                if last_earning and last_earning.date() == today:
                    continue
                
                # Check if rental is expired
                if rental.is_expired():
                    rental.status = 'completed'
                    rental.completed_at = datetime.utcnow()
                    db.session.add(rental)
                    continue
                
                # Calculate earning
                earning = rental.daily_earning
                
                # Update rental
                rental.days_elapsed += 1
                rental.total_earned += earning
                rental.last_earning_date = datetime.utcnow()
                
                # Check if rental period is complete
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
                
                processed += 1
                logger.info(f"✅ Processed {rental.rental_id}: {rental.vehicle.name} - +KSH {earning:.2f}")
            
            # Commit all changes
            db.session.commit()
            logger.info(f"✅ Daily earnings processing complete! Processed {processed} rentals")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error processing daily earnings: {str(e)}")
            raise

def fix_existing_rentals():
    """Fix existing rentals that haven't been earning properly"""
    app = create_app()
    with app.app_context():
        try:
            logger.info("🔄 Fixing existing rentals...")
            
            # Find rentals with 0 days elapsed but should have earnings
            rentals = Rental.query.filter(
                Rental.status == 'active',
                Rental.days_elapsed == 0,
                Rental.last_earning_date.is_(None)
            ).all()
            
            fixed = 0
            for rental in rentals:
                # Calculate days since rental started
                days_since = (datetime.utcnow() - rental.start_date).days
                
                if days_since > 0:
                    # Update rental
                    rental.days_elapsed = days_since
                    rental.total_earned = rental.daily_earning * days_since
                    rental.last_earning_date = rental.start_date + timedelta(days=days_since - 1)
                    
                    # Create transaction for each day
                    for i in range(days_since):
                        transaction = Transaction(
                            user_id=rental.user_id,
                            type='rental_earning',
                            amount=rental.daily_earning,
                            fee=0,
                            net_amount=rental.daily_earning,
                            description=f'Back-dated earning from {rental.vehicle.name} rental - Day {i+1}',
                            status='completed',
                            reference=rental.rental_id
                        )
                        db.session.add(transaction)
                    
                    # Update user balance
                    user = User.query.get(rental.user_id)
                    if user:
                        user.balance += rental.total_earned
                        user.total_earned += rental.total_earned
                        db.session.add(user)
                    
                    fixed += 1
                    logger.info(f"✅ Fixed {rental.rental_id}: {rental.vehicle.name} - Added {days_since} days, KSH {rental.total_earned:.2f}")
            
            db.session.commit()
            logger.info(f"✅ Fixed {fixed} rentals")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error fixing rentals: {str(e)}")