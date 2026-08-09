# admin.py - Complete admin panel with all functions including add user
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from datetime import datetime, timezone
from sqlalchemy import func, desc

from models import db, User, Vehicle, Rental, Transaction, ServiceHistory, ReferralBonus, Notification, ActivityLog
from forms import AdminUserForm, AdminVehicleForm, AdminSettingsForm
from utils.sms import send_sms
from utils.email import send_email
from werkzeug.security import generate_password_hash
import re

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
def check_admin():
    """Check if user is admin"""
    if not current_user.is_authenticated:
        flash('Please login to access the admin panel.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Check if user has admin privileges
    is_admin = (
        current_user.email == 'admin@vch.com' or 
        current_user.agent_level == 'level2' or
        current_user.id == 1 or
        current_user.username == 'admin'
    )
    
    if not is_admin:
        flash('You do not have permission to access the admin panel.', 'danger')
        return redirect(url_for('dashboard'))

# ==================== ADMIN DASHBOARD ====================

@admin_bp.route('/')
@admin_bp.route('/dashboard')
def dashboard():
    """Admin dashboard"""
    # Statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    verified_users = User.query.filter_by(is_verified=True).count()
    
    total_rentals = Rental.query.count()
    active_rentals = Rental.query.filter_by(status='active').count()
    completed_rentals = Rental.query.filter_by(status='completed').count()
    
    total_deposits = db.session.query(func.sum(Transaction.amount))\
        .filter_by(type='deposit', status='completed').scalar() or 0
    
    total_withdrawals = db.session.query(func.sum(Transaction.amount))\
        .filter_by(type='withdrawal', status='completed').scalar() or 0
    
    total_revenue = total_deposits - total_withdrawals
    
    total_vehicles = Vehicle.query.count()
    
    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Recent transactions
    recent_transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(10).all()
    
    # Pending withdrawals
    pending_withdrawals = Transaction.query.filter_by(type='withdrawal', status='pending').count()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         verified_users=verified_users,
                         total_rentals=total_rentals,
                         active_rentals=active_rentals,
                         completed_rentals=completed_rentals,
                         total_deposits=total_deposits,
                         total_withdrawals=total_withdrawals,
                         total_revenue=total_revenue,
                         total_vehicles=total_vehicles,
                         pending_withdrawals=pending_withdrawals,
                         recent_users=recent_users,
                         recent_transactions=recent_transactions)

# ==================== USER MANAGEMENT ====================

@admin_bp.route('/users/add', methods=['GET', 'POST'])
def add_user():
    """Add a new user manually"""
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        is_active = request.form.get('is_active') == 'on'
        is_verified = request.form.get('is_verified') == 'on'
        agent_level = request.form.get('agent_level', 'none')
        balance = float(request.form.get('balance', 0))
        
        # Validate input
        errors = []
        
        if not username:
            errors.append('Username is required')
        elif User.query.filter_by(username=username).first():
            errors.append('Username already exists')
        
        if not email:
            errors.append('Email is required')
        elif User.query.filter_by(email=email).first():
            errors.append('Email already exists')
        
        if not phone:
            errors.append('Phone number is required')
        else:
            # Format phone number
            phone = re.sub(r'\D', '', phone)
            if phone.startswith('0'):
                phone = '254' + phone[1:]
            elif len(phone) == 9:
                phone = '254' + phone
            elif len(phone) == 10 and not phone.startswith('254'):
                phone = '254' + phone[1:]
            elif phone.startswith('254'):
                phone = phone
            else:
                phone = '254' + phone
            
            if User.query.filter_by(phone=phone).first():
                errors.append('Phone number already exists')
        
        if not password or len(password) < 8:
            errors.append('Password must be at least 8 characters')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('admin/add_user.html')
        
        # Create new user
        try:
            user = User(
                username=username,
                email=email,
                phone=phone,
                full_name=full_name or username,
                is_active=is_active,
                is_verified=is_verified,
                agent_level=agent_level,
                balance=balance,
                total_deposited=balance if balance > 0 else 0
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Send welcome notification to the new user
            notification = Notification(
                user_id=user.id,
                title='Welcome to VCH!',
                message=f'Your account has been created by the administrator. You can now login and start using the platform. Email: {email}',
                type='success'
            )
            db.session.add(notification)
            db.session.commit()
            
            flash(f'User {username} created successfully!', 'success')
            return redirect(url_for('admin.view_user', user_id=user.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'danger')
            return render_template('admin/add_user.html')
    
    return render_template('admin/add_user.html')

@admin_bp.route('/users')
def users():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    level = request.args.get('level', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.username.contains(search),
                User.email.contains(search),
                User.phone.contains(search)
            )
        )
    
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    
    if level and level != 'all':
        query = query.filter_by(agent_level=level)
    
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>')
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get user transactions
    transactions = Transaction.query.filter_by(user_id=user_id)\
        .order_by(Transaction.created_at.desc()).limit(20).all()
    
    # Get user rentals
    rentals = Rental.query.filter_by(user_id=user_id)\
        .order_by(Rental.created_at.desc()).limit(20).all()
    
    return render_template('admin/view_user.html', 
                         user=user, 
                         transactions=transactions, 
                         rentals=rentals)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email').lower()
        user.phone = request.form.get('phone')
        user.full_name = request.form.get('full_name')
        user.is_active = request.form.get('is_active') == 'on'
        user.is_verified = request.form.get('is_verified') == 'on'
        user.agent_level = request.form.get('agent_level')
        
        if request.form.get('password'):
            user.set_password(request.form.get('password'))
        
        db.session.commit()
        flash('User updated successfully', 'success')
        return redirect(url_for('admin.view_user', user_id=user.id))
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/users/<int:user_id>/block', methods=['POST'])
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot block yourself!', 'danger')
        return redirect(url_for('admin.view_user', user_id=user_id))
    
    user.is_active = False
    db.session.commit()
    
    # Send notification
    notification = Notification(
        user_id=user_id,
        title='Account Blocked',
        message='Your account has been blocked by the administrator. Please contact support for assistance.',
        type='danger'
    )
    db.session.add(notification)
    db.session.commit()
    
    flash(f'User {user.username} has been blocked.', 'success')
    return redirect(url_for('admin.view_user', user_id=user_id))

@admin_bp.route('/users/<int:user_id>/unblock', methods=['POST'])
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    
    user.is_active = True
    db.session.commit()
    
    # Send notification
    notification = Notification(
        user_id=user_id,
        title='Account Unblocked',
        message='Your account has been unblocked. You can now login and continue using the platform.',
        type='success'
    )
    db.session.add(notification)
    db.session.commit()
    
    flash(f'User {user.username} has been unblocked.', 'success')
    return redirect(url_for('admin.view_user', user_id=user_id))

@admin_bp.route('/users/<int:user_id>/verify', methods=['POST'])
def verify_user(user_id):
    user = User.query.get_or_404(user_id)
    
    user.is_verified = True
    db.session.commit()
    
    # Send notification
    notification = Notification(
        user_id=user_id,
        title='Account Verified',
        message='Your account has been verified by the administrator. You now have full access to the platform.',
        type='success'
    )
    db.session.add(notification)
    db.session.commit()
    
    flash(f'User {user.username} has been verified.', 'success')
    return redirect(url_for('admin.view_user', user_id=user_id))

@admin_bp.route('/users/<int:user_id>/add-money', methods=['POST'])
def add_money(user_id):
    user = User.query.get_or_404(user_id)
    
    amount = request.form.get('amount', type=float)
    if not amount or amount <= 0:
        flash('Please enter a valid amount.', 'danger')
        return redirect(url_for('admin.view_user', user_id=user_id))
    
    description = request.form.get('description', 'Admin deposit')
    
    # Create transaction
    transaction = Transaction(
        user_id=user_id,
        type='deposit',
        amount=amount,
        fee=0,
        net_amount=amount,
        description=f'Admin: {description}',
        status='completed',
        payment_method='admin'
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
        title='Funds Added',
        message=f'The administrator has added KSH {amount:,.2f} to your account. Reason: {description}',
        type='success'
    )
    db.session.add(notification)
    db.session.commit()
    
    flash(f'KSH {amount:,.2f} added to {user.username}\'s account.', 'success')
    return redirect(url_for('admin.view_user', user_id=user_id))

@admin_bp.route('/users/<int:user_id>/deduct-money', methods=['POST'])
def deduct_money(user_id):
    user = User.query.get_or_404(user_id)
    
    amount = request.form.get('amount', type=float)
    if not amount or amount <= 0:
        flash('Please enter a valid amount.', 'danger')
        return redirect(url_for('admin.view_user', user_id=user_id))
    
    if user.balance < amount:
        flash(f'Insufficient balance. User only has KSH {user.balance:,.2f}', 'danger')
        return redirect(url_for('admin.view_user', user_id=user_id))
    
    description = request.form.get('description', 'Admin deduction')
    
    # Create transaction
    transaction = Transaction(
        user_id=user_id,
        type='withdrawal',
        amount=amount,
        fee=0,
        net_amount=-amount,
        description=f'Admin deduction: {description}',
        status='completed',
        payment_method='admin'
    )
    db.session.add(transaction)
    
    # Update user balance
    user.balance -= amount
    user.total_withdrawn += amount
    db.session.add(user)
    
    db.session.commit()
    
    # Send notification
    notification = Notification(
        user_id=user_id,
        title='Funds Deducted',
        message=f'The administrator has deducted KSH {amount:,.2f} from your account. Reason: {description}',
        type='danger'
    )
    db.session.add(notification)
    db.session.commit()
    
    flash(f'KSH {amount:,.2f} deducted from {user.username}\'s account.', 'success')
    return redirect(url_for('admin.view_user', user_id=user_id))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete yourself!', 'danger')
        return redirect(url_for('admin.view_user', user_id=user_id))
    
    username = user.username
    
    # Delete user's notifications
    Notification.query.filter_by(user_id=user_id).delete()
    
    # Delete user's transactions
    Transaction.query.filter_by(user_id=user_id).delete()
    
    # Delete user's rentals
    Rental.query.filter_by(user_id=user_id).delete()
    
    # Delete user's service history
    ServiceHistory.query.filter_by(user_id=user_id).delete()
    
    # Delete user's activity logs
    ActivityLog.query.filter_by(user_id=user_id).delete()
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} has been permanently deleted.', 'success')
    return redirect(url_for('admin.users'))

# ==================== VEHICLE MANAGEMENT ====================

@admin_bp.route('/vehicles')
def vehicles():
    vehicles = Vehicle.query.order_by(Vehicle.sort_order).all()
    return render_template('admin/vehicles.html', vehicles=vehicles)

@admin_bp.route('/vehicles/add', methods=['GET', 'POST'])
def add_vehicle():
    if request.method == 'POST':
        vehicle = Vehicle(
            name=request.form.get('name'),
            brand=request.form.get('brand'),
            rental_price=float(request.form.get('rental_price', 0)),
            daily_earning=float(request.form.get('daily_earning', 0)),
            rental_period=int(request.form.get('rental_period', 30)),
            description=request.form.get('description'),
            is_active=request.form.get('is_active') == 'on',
            is_available=request.form.get('is_available') == 'on',
            sort_order=int(request.form.get('sort_order', 0))
        )
        
        db.session.add(vehicle)
        db.session.commit()
        
        flash(f'Vehicle {vehicle.name} added successfully!', 'success')
        return redirect(url_for('admin.vehicles'))
    
    return render_template('admin/add_vehicle.html')

@admin_bp.route('/vehicles/<int:vehicle_id>/edit', methods=['GET', 'POST'])
def edit_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    if request.method == 'POST':
        vehicle.name = request.form.get('name')
        vehicle.brand = request.form.get('brand')
        vehicle.rental_price = float(request.form.get('rental_price', 0))
        vehicle.daily_earning = float(request.form.get('daily_earning', 0))
        vehicle.rental_period = int(request.form.get('rental_period', 30))
        vehicle.description = request.form.get('description')
        vehicle.is_active = request.form.get('is_active') == 'on'
        vehicle.is_available = request.form.get('is_available') == 'on'
        vehicle.sort_order = int(request.form.get('sort_order', 0))
        
        db.session.commit()
        flash(f'Vehicle {vehicle.name} updated successfully!', 'success')
        return redirect(url_for('admin.vehicles'))
    
    return render_template('admin/edit_vehicle.html', vehicle=vehicle)

@admin_bp.route('/vehicles/<int:vehicle_id>/delete', methods=['POST'])
def delete_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    name = vehicle.name
    db.session.delete(vehicle)
    db.session.commit()
    
    flash(f'Vehicle {name} deleted successfully.', 'success')
    return redirect(url_for('admin.vehicles'))

# ==================== RENTAL MANAGEMENT ====================

@admin_bp.route('/rentals')
def rentals():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    rentals = Rental.query.order_by(Rental.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/rentals.html', rentals=rentals)

# ==================== WITHDRAWAL MANAGEMENT ====================

@admin_bp.route('/withdrawals')
def withdrawals():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    withdrawals = Transaction.query.filter_by(type='withdrawal')\
        .order_by(Transaction.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/withdrawals.html', withdrawals=withdrawals)

@admin_bp.route('/withdrawals/<int:transaction_id>/process', methods=['POST'])
def process_withdrawal(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    if transaction.status != 'pending':
        flash('Transaction already processed', 'warning')
        return redirect(url_for('admin.withdrawals'))
    
    action = request.form.get('action')
    
    if action == 'approve':
        transaction.status = 'completed'
        transaction.completed_at = datetime.now(timezone.utc)
        
        notification = Notification(
            user_id=transaction.user_id,
            title='Withdrawal Approved',
            message=f'Your withdrawal of KSH {transaction.amount:,.2f} has been approved and processed.',
            type='success'
        )
        db.session.add(notification)
        
        flash('Withdrawal approved successfully', 'success')
    
    elif action == 'reject':
        transaction.status = 'failed'
        
        # Refund the user
        user = User.query.get(transaction.user_id)
        if user:
            user.balance += transaction.amount
            db.session.add(user)
        
        notification = Notification(
            user_id=transaction.user_id,
            title='Withdrawal Rejected',
            message=f'Your withdrawal of KSH {transaction.amount:,.2f} has been rejected. Funds have been refunded to your balance.',
            type='danger'
        )
        db.session.add(notification)
        
        flash('Withdrawal rejected and funds refunded', 'warning')
    
    db.session.commit()
    return redirect(url_for('admin.withdrawals'))

# ==================== DEPOSIT MANAGEMENT ====================

@admin_bp.route('/deposits')
def deposits():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    deposits = Transaction.query.filter_by(type='deposit')\
        .order_by(Transaction.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/deposits.html', deposits=deposits)

# ==================== REFERRAL MANAGEMENT ====================

@admin_bp.route('/referrals')
def referrals():
    referrals = ReferralBonus.query.order_by(ReferralBonus.created_at.desc()).limit(100).all()
    
    total_referrals = ReferralBonus.query.count()
    total_bonus_paid = db.session.query(func.sum(ReferralBonus.amount))\
        .filter_by(is_paid=True).scalar() or 0
    
    # Get top referrer
    top_referrer_data = db.session.query(
        User.username,
        func.count(ReferralBonus.id).label('count')
    ).join(ReferralBonus, User.id == ReferralBonus.referrer_id)\
     .group_by(User.id)\
     .order_by(desc('count'))\
     .first()
    
    top_referrer = top_referrer_data[0] if top_referrer_data else 'N/A'
    
    return render_template('admin/referrals.html',
                         referrals=referrals,
                         total_referrals=total_referrals,
                         total_bonus_paid=total_bonus_paid,
                         top_referrer=top_referrer)

# ==================== REPORTS ====================

@admin_bp.route('/reports')
def reports():
    return render_template('admin/reports.html')

# ==================== SETTINGS ====================

@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    return render_template('admin/settings.html')

# ==================== ANNOUNCEMENTS ====================

@admin_bp.route('/announcements', methods=['GET', 'POST'])
def announcements():
    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        user_type = request.form.get('user_type', 'all')
        
        if not title or not message:
            flash('Title and message are required', 'danger')
            return render_template('admin/announcements.html')
        
        # Get target users
        query = User.query.filter_by(is_active=True)
        if user_type == 'agents':
            query = query.filter(User.agent_level != 'none')
        
        users = query.all()
        
        # Create notifications for all target users
        created_count = 0
        for user in users:
            notification = Notification(
                user_id=user.id,
                title=title,
                message=message,
                type='info'
            )
            db.session.add(notification)
            created_count += 1
        
        db.session.commit()
        
        flash(f'Announcement sent to {created_count} users!', 'success')
        return redirect(url_for('admin.announcements'))
    
    announcements = Notification.query.filter_by(type='info')\
        .order_by(Notification.created_at.desc()).limit(20).all()
    
    return render_template('admin/announcements.html', announcements=announcements)