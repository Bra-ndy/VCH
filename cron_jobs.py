# cron_jobs.py
from app import create_app, db
from models import Rental, User, Transaction, Notification
from datetime import datetime, timedelta
import logging

app = create_app()
logger = logging.getLogger(__name__)

def process_daily_earnings():
    """Process daily earnings for all active rentals"""
    with app.app_context():
        try:
            # Get all active rentals
            active_rentals = Rental.query.filter_by(status='active').all()
            
            for rental in active_rentals:
                # Check if already earned today
                today = datetime.now().date()
                last_earning = rental.last_earning_date
                
                if last_earning and last_earning.date() == today:
                    continue  # Already earned today
                
                # Calculate daily earning (from the vehicle)
                daily_amount = rental.daily_earning
                
                # Add to user's balance
                user = User.query.get(rental.user_id)
                if user:
                    user.balance += daily_amount
                    user.total_earned += daily_amount
                    
                    # Update rental tracking
                    rental.days_elapsed += 1
                    rental.total_earned += daily_amount
                    rental.last_earning_date = datetime.now()
                    
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
                    # Access rental_period from the vehicle
                    if rental.days_elapsed >= rental.vehicle.rental_period:
                        rental.status = 'completed'
                        rental.completed_at = datetime.now()
                        
                        # Create notification
                        notification = Notification(
                            user_id=user.id,
                            title='Rental Completed! 🎉',
                            message=f'Your {rental.vehicle.name} rental has completed. Total earned: KSH {rental.total_earned:,.2f}',
                            type='success'
                        )
                        db.session.add(notification)
            
            db.session.commit()
            logger.info(f"✅ Processed daily earnings for {len(active_rentals)} rentals")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error processing daily earnings: {str(e)}")

if __name__ == '__main__':
    process_daily_earnings()