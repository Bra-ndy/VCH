# cron_jobs.py
from app import create_app, db
from models import Rental, User, Transaction, Notification
from datetime import datetime, timezone, timedelta
import logging

app = create_app()
logger = logging.getLogger(__name__)

def fix_rentals():
    """Fix inconsistent rental data (days_elapsed and total_earned)"""
    with app.app_context():
        try:
            logger.info("🔧 Fixing rental inconsistencies...")
            
            # Get all active rentals
            rentals = Rental.query.filter_by(status='active').all()
            
            if not rentals:
                logger.info("ℹ️ No active rentals found")
                return
            
            fixed_count = 0
            completed_count = 0
            now = datetime.now(timezone.utc)
            
            for rental in rentals:
                # Make start_date timezone-aware if needed
                start_date = rental.start_date
                if start_date.tzinfo is None:
                    start_date = start_date.replace(tzinfo=timezone.utc)
                
                days_since_start = (now - start_date).days
                
                if rental.days_elapsed == 0 and days_since_start > 0:
                    rental.days_elapsed = days_since_start
                    rental.total_earned = days_since_start * rental.daily_earning
                    fixed_count += 1
                    logger.info(f"✅ Fixed {rental.vehicle.name}: days_elapsed={rental.days_elapsed}, total_earned={rental.total_earned:.2f}")
                
                if rental.days_elapsed >= rental.vehicle.rental_period:
                    rental.status = 'completed'
                    rental.completed_at = datetime.now(timezone.utc)
                    completed_count += 1
                    logger.info(f"✅ Completed {rental.vehicle.name}: Period complete after {rental.days_elapsed} days")
            
            db.session.commit()
            logger.info(f"📊 Fix summary: Fixed {fixed_count} rentals, Completed {completed_count} rentals")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error fixing rentals: {str(e)}")

def process_daily_earnings():
    """Process daily earnings for all active rentals"""
    with app.app_context():
        try:
            logger.info("🔄 Starting daily earnings processing...")
            
            # First fix any inconsistencies
            fix_rentals()
            
            # Get all active rentals
            active_rentals = Rental.query.filter_by(status='active').all()
            logger.info(f"📊 Found {len(active_rentals)} active rentals")
            
            processed_count = 0
            now = datetime.now(timezone.utc)
            today = now.date()
            
            for rental in active_rentals:
                # Check if already earned today
                last_earning = rental.last_earning_date
                if last_earning and last_earning.date() == today:
                    continue  # Already earned today
                
                # Calculate daily earning
                daily_amount = rental.daily_earning
                
                # Add to user's balance
                user = User.query.get(rental.user_id)
                if user:
                    user.balance += daily_amount
                    user.total_earned += daily_amount
                    
                    # Update rental tracking
                    rental.days_elapsed += 1
                    rental.total_earned += daily_amount
                    rental.last_earning_date = datetime.now(timezone.utc)
                    
                    # Create transaction record
                    transaction = Transaction(
                        user_id=user.id,
                        type='rental_earning',
                        amount=daily_amount,
                        fee=0,
                        net_amount=daily_amount,
                        description=f'Daily rental earning for {rental.vehicle.name}',
                        status='completed'
                    )
                    db.session.add(transaction)
                    
                    # Check if rental period is complete
                    if rental.days_elapsed >= rental.vehicle.rental_period:
                        rental.status = 'completed'
                        rental.completed_at = datetime.now(timezone.utc)
                        
                        # Create notification
                        notification = Notification(
                            user_id=user.id,
                            title='Rental Completed! 🎉',
                            message=f'Your {rental.vehicle.name} rental has completed. Total earned: KSH {rental.total_earned:,.2f}',
                            type='success'
                        )
                        db.session.add(notification)
                        logger.info(f"✅ Completed {rental.vehicle.name} for user {user.username}")
                    
                    processed_count += 1
                    logger.info(f"✅ Processed {rental.vehicle.name}: +KSH {daily_amount:.2f} for user {user.username}")
            
            db.session.commit()
            logger.info(f"✅ Processed daily earnings for {processed_count} rentals")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error processing daily earnings: {str(e)}")

def fix_and_process():
    """Fix existing rentals and process daily earnings"""
    with app.app_context():
        fix_rentals()
        process_daily_earnings()

if __name__ == '__main__':
    fix_and_process()