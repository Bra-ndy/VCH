# rentals.py - Complete version with rentals_bp defined and referral bonus integration
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func

from models import db, Vehicle, Rental, Transaction, Notification
from forms import CarRentalForm
from utils.earnings import calculate_rental_earning, process_rental

# Create the blueprint
rentals_bp = Blueprint('rentals', __name__, url_prefix='/rentals')

@rentals_bp.route('/')
@login_required
def cars():
    vehicles = Vehicle.query.filter_by(is_active=True).order_by(Vehicle.sort_order).all()
    return render_template('rentals/cars.html', vehicles=vehicles)

@rentals_bp.route('/rent/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
def rent(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    if not vehicle.is_available:
        flash('This car is currently not available for rental', 'danger')
        return redirect(url_for('rentals.cars'))
    
    form = CarRentalForm()
    form.vehicle_id.data = vehicle_id
    
    if form.validate_on_submit():
        if current_user.balance < vehicle.rental_price:
            flash(f'Insufficient balance. You need KSH {vehicle.rental_price:,.2f}', 'danger')
            return render_template('rentals/rent.html', vehicle=vehicle, form=form)
        
        try:
            rental = process_rental(
                user_id=current_user.id,
                vehicle_id=vehicle_id,
                rental_period=form.rental_period.data
            )
            
            # Check if this is the user's first rental and process referral bonus
            previous_rentals = Rental.query.filter_by(
                user_id=current_user.id
            ).filter(Rental.status != 'cancelled').count()
            
            # If this is the first rental (only the one we just created), process referral bonus
            if previous_rentals == 0:
                success, message = process_referral_bonus(current_user.id)
                if success:
                    flash(message, 'success')
                else:
                    # Don't show error if no referral, just log it silently
                    if "User was not referred" not in message:
                        print(f"Referral bonus not processed: {message}")
            
            flash(f'Car rented successfully! You will earn KSH {vehicle.daily_earning:,.2f} per day.', 'success')
            return redirect(url_for('rentals.active_rentals'))
        
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'Error processing rental: {str(e)}', 'danger')
    
    return render_template('rentals/rent.html', vehicle=vehicle, form=form)

@rentals_bp.route('/active')
@login_required
def active_rentals():
    rentals = Rental.query.filter_by(user_id=current_user.id, status='active').all()
    return render_template('rentals/active_rentals.html', rentals=rentals)

@rentals_bp.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    rentals = Rental.query.filter_by(user_id=current_user.id)\
        .order_by(Rental.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('rentals/rental_history.html', rentals=rentals)

@rentals_bp.route('/daily-earnings')
@login_required
def daily_earnings():
    """API endpoint to get daily earnings for all active rentals"""
    active_rentals = Rental.query.filter_by(user_id=current_user.id, status='active').all()
    
    daily_earnings = []
    for rental in active_rentals:
        daily_earnings.append({
            'rental_id': rental.rental_id,
            'vehicle': rental.vehicle.name,
            'daily_earning': rental.daily_earning,
            'days_remaining': rental.days_remaining(),
            'days_elapsed': rental.days_elapsed,
            'total_earned': rental.total_earned
        })
    
    return jsonify(daily_earnings)


# ============================================================
# REFERRAL BONUS FUNCTION - Integrated directly in rentals.py
# ============================================================
def process_referral_bonus(user_id):
    """
    Process referral bonus when a user rents their first car.
    This should be called when a user completes their first rental.
    """
    from models import User, Transaction, ReferralBonus, Notification
    
    # Get the user
    user = User.query.get(user_id)
    if not user:
        return False, "User not found"
    
    # Check if user was referred
    if not user.referred_by:
        return False, "User was not referred by anyone"
    
    # Check if referral bonus already applied
    if user.referral_bonus_applied:
        return False, "Referral bonus already applied"
    
    # Get the referrer
    referrer = User.query.get(user.referred_by)
    if not referrer:
        return False, "Referrer not found"
    
    # Calculate bonus amounts
    referrer_bonus = 150.00  # KSH 150 for referrer
    user_bonus = 50.00       # KSH 50 for the new user
    
    try:
        # Add bonus to referrer's balance
        referrer.balance += referrer_bonus
        referrer.total_earned += referrer_bonus
        
        # Create referral bonus record for referrer
        referral_bonus = ReferralBonus(
            referrer_id=referrer.id,
            referred_id=user.id,
            amount=referrer_bonus,
            type='rental_bonus',
            is_paid=True,
            paid_at=datetime.utcnow()
        )
        db.session.add(referral_bonus)
        
        # Create transaction for referrer
        transaction = Transaction(
            user_id=referrer.id,
            type='referral_bonus',
            amount=referrer_bonus,
            fee=0,
            net_amount=referrer_bonus,
            description=f'Referral bonus for {user.username}\'s first rental',
            status='completed'
        )
        db.session.add(transaction)
        
        # Give bonus to the new user
        user.balance += user_bonus
        user.total_earned += user_bonus
        
        # Create transaction for new user
        user_transaction = Transaction(
            user_id=user.id,
            type='welcome_bonus',
            amount=user_bonus,
            fee=0,
            net_amount=user_bonus,
            description='Welcome bonus for your first rental!',
            status='completed'
        )
        db.session.add(user_transaction)
        
        # Mark bonus as applied
        user.referral_bonus_applied = True
        
        # Create notification for referrer
        referrer_notification = Notification(
            user_id=referrer.id,
            title='Referral Bonus Earned! 🎉',
            message=f'{user.username} rented their first car! You earned KSH {referrer_bonus:,.2f} referral bonus!',
            type='success'
        )
        db.session.add(referrer_notification)
        
        # Create notification for new user
        user_notification = Notification(
            user_id=user.id,
            title='Welcome Bonus! 🎉',
            message=f'Congratulations on your first rental! You earned a KSH {user_bonus:,.2f} welcome bonus!',
            type='success'
        )
        db.session.add(user_notification)
        
        db.session.commit()
        
        return True, f"🎉 Referral bonus: You earned KSH {user_bonus:,.2f} and your referrer {referrer.username} earned KSH {referrer_bonus:,.2f}!"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error processing referral bonus: {str(e)}"