from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func

from models import db, ServiceHistory, Transaction, Notification, Rental
from utils.earnings import process_service_earning

servicing_bp = Blueprint('servicing', __name__, url_prefix='/servicing')

# Service earning amount
SERVICE_AMOUNT = 5.0  # KSH 5 per day


@servicing_bp.route('/')
@login_required
def servicing():
    """Servicing dashboard"""
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    today_end = today_start + timedelta(days=1)
    
    # Check if user has active rentals
    active_rentals = Rental.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).count()
    
    has_active_rental = active_rentals > 0
    
    # Get today's service if performed
    today_service = ServiceHistory.query.filter(
        ServiceHistory.user_id == current_user.id,
        ServiceHistory.service_date >= today_start,
        ServiceHistory.service_date < today_end,
        ServiceHistory.type == 'daily_servicing'
    ).first()
    
    is_serviced_today = today_service is not None
    
    # Get total service earnings
    total_earnings = db.session.query(
        func.sum(ServiceHistory.earning)
    ).filter(
        ServiceHistory.user_id == current_user.id,
        ServiceHistory.type == 'daily_servicing'
    ).scalar() or 0
    
    # Get service history for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    service_history = ServiceHistory.query.filter(
        ServiceHistory.user_id == current_user.id,
        ServiceHistory.type == 'daily_servicing',
        ServiceHistory.service_date >= thirty_days_ago
    ).order_by(ServiceHistory.service_date.desc()).all()
    
    # Calculate service streak
    streak = calculate_service_streak(current_user.id)
    
    # Get page for paginated history
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    history = ServiceHistory.query.filter_by(
        user_id=current_user.id,
        type='daily_servicing'
    ).order_by(ServiceHistory.service_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        'servicing/servicing.html',
        today_service=today_service,
        history=history,
        total_earnings=total_earnings,
        service_history=service_history,
        daily_earning=SERVICE_AMOUNT,
        is_serviced_today=is_serviced_today,
        has_active_rental=has_active_rental,
        active_rentals_count=active_rentals,
        streak=streak
    )


@servicing_bp.route('/perform', methods=['POST'])
@login_required
def perform_service():
    """Perform daily servicing"""
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    today_end = today_start + timedelta(days=1)
    
    # Check if user has active rentals
    active_rentals = Rental.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).count()
    
    if active_rentals == 0:
        flash('You need an active rental to perform daily servicing! Rent a car first.', 'warning')
        return redirect(url_for('servicing.servicing'))
    
    # Check if already serviced today
    existing = ServiceHistory.query.filter(
        ServiceHistory.user_id == current_user.id,
        ServiceHistory.service_date >= today_start,
        ServiceHistory.service_date < today_end,
        ServiceHistory.type == 'daily_servicing'
    ).first()
    
    if existing:
        flash('You have already performed daily servicing today! Come back tomorrow.', 'info')
        return redirect(url_for('servicing.servicing'))
    
    try:
        # Create service record
        service = ServiceHistory(
            user_id=current_user.id,
            type='daily_servicing',
            earning=SERVICE_AMOUNT,
            service_date=datetime.utcnow()
        )
        db.session.add(service)
        
        # Add earnings to user's balance
        current_user.balance += SERVICE_AMOUNT
        current_user.total_earned += SERVICE_AMOUNT
        
        # Create transaction record
        transaction = Transaction(
            user_id=current_user.id,
            type='service_earning',
            amount=SERVICE_AMOUNT,
            fee=0,
            net_amount=SERVICE_AMOUNT,
            description=f'Daily servicing earning - KSH {SERVICE_AMOUNT:.2f}',
            status='completed'
        )
        db.session.add(transaction)
        
        # Create notification
        notification = Notification(
            user_id=current_user.id,
            title='Daily Servicing Complete! ✅',
            message=f'You earned KSH {SERVICE_AMOUNT:.2f} for today\'s servicing.',
            type='success'
        )
        db.session.add(notification)
        
        db.session.commit()
        
        flash(f'Daily servicing complete! You earned KSH {SERVICE_AMOUNT:.2f}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error performing service: {str(e)}', 'danger')
    
    return redirect(url_for('servicing.servicing'))


@servicing_bp.route('/history')
@login_required
def history():
    """View service history"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    history = ServiceHistory.query.filter(
        ServiceHistory.user_id == current_user.id,
        ServiceHistory.type == 'daily_servicing'
    ).order_by(ServiceHistory.service_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('servicing/service_history.html', history=history)


@servicing_bp.route('/check-status')
@login_required
def check_status():
    """API endpoint to check if user can service today"""
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    today_end = today_start + timedelta(days=1)
    
    # Check if user has active rentals
    active_rentals = Rental.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).count()
    
    has_active_rental = active_rentals > 0
    
    # Check if already serviced today
    today_service = ServiceHistory.query.filter(
        ServiceHistory.user_id == current_user.id,
        ServiceHistory.service_date >= today_start,
        ServiceHistory.service_date < today_end,
        ServiceHistory.type == 'daily_servicing'
    ).first()
    
    # Get today's total earnings
    today_earnings = db.session.query(
        func.sum(ServiceHistory.earning)
    ).filter(
        ServiceHistory.user_id == current_user.id,
        ServiceHistory.service_date >= today_start,
        ServiceHistory.service_date < today_end,
        ServiceHistory.type == 'daily_servicing'
    ).scalar() or 0
    
    return jsonify({
        'can_service': has_active_rental and not today_service,
        'has_active_rental': has_active_rental,
        'serviced_today': today_service is not None,
        'daily_earning': SERVICE_AMOUNT,
        'today_earnings': float(today_earnings),
        'active_rentals_count': active_rentals
    })


@servicing_bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint to get service statistics"""
    # Get total service earnings
    total_earnings = db.session.query(
        func.sum(ServiceHistory.earning)
    ).filter(
        ServiceHistory.user_id == current_user.id,
        ServiceHistory.type == 'daily_servicing'
    ).scalar() or 0
    
    # Get service count
    service_count = ServiceHistory.query.filter(
        ServiceHistory.user_id == current_user.id,
        ServiceHistory.type == 'daily_servicing'
    ).count()
    
    # Get monthly earnings (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    monthly_earnings = db.session.query(
        func.sum(ServiceHistory.earning)
    ).filter(
        ServiceHistory.user_id == current_user.id,
        ServiceHistory.type == 'daily_servicing',
        ServiceHistory.service_date >= thirty_days_ago
    ).scalar() or 0
    
    # Get streak
    streak = calculate_service_streak(current_user.id)
    
    return jsonify({
        'total_earnings': float(total_earnings),
        'service_count': service_count,
        'monthly_earnings': float(monthly_earnings),
        'streak': streak,
        'daily_earning': SERVICE_AMOUNT
    })


def calculate_service_streak(user_id):
    """Calculate consecutive days of servicing"""
    streak = 0
    current_date = datetime.utcnow().date()
    
    while True:
        day_start = datetime(current_date.year, current_date.month, current_date.day)
        day_end = day_start + timedelta(days=1)
        
        service = ServiceHistory.query.filter(
            ServiceHistory.user_id == user_id,
            ServiceHistory.service_date >= day_start,
            ServiceHistory.service_date < day_end,
            ServiceHistory.type == 'daily_servicing'
        ).first()
        
        if service:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break
    
    return streak