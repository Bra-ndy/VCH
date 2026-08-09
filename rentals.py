# rentals.py - Complete version with rentals_bp defined
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