# referrals.py - Complete version with referrals_bp defined
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func

from models import db, User, ReferralBonus, Transaction, Notification
from utils.referral import process_referral_bonus, calculate_referral_commission

# Create the blueprint
referrals_bp = Blueprint('referrals', __name__, url_prefix='/referrals')

@referrals_bp.route('/')
@login_required
def index():
    """Referral dashboard - main page"""
    # Get referred users
    referred_users = User.query.filter_by(referred_by=current_user.id).all()
    
    # Get referral bonuses
    bonuses = ReferralBonus.query.filter_by(referrer_id=current_user.id)\
        .order_by(ReferralBonus.created_at.desc()).all()
    
    # Calculate total referral earnings - include ALL bonuses (paid and unpaid)
    total_earnings = sum(b.amount for b in bonuses)
    
    # Get referral link
    referral_link = f"{request.host_url}auth/register?ref={current_user.referral_code}"
    
    # Get agent level
    agent_level = current_user.agent_level or 'None'
    
    return render_template('referrals/referrals.html',
                         referred_users=referred_users,
                         bonuses=bonuses,
                         total_earnings=total_earnings,
                         referral_link=referral_link,
                         agent_level=agent_level)

@referrals_bp.route('/dashboard')
@login_required
def dashboard():
    """Referral dashboard alias - for compatibility"""
    return redirect(url_for('referrals.index'))

@referrals_bp.route('/history')
@login_required
def history():
    """Referral history with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    bonuses = ReferralBonus.query.filter_by(referrer_id=current_user.id)\
        .order_by(ReferralBonus.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Calculate total earnings for the summary - include ALL bonuses
    total_earnings = sum(b.amount for b in bonuses.items) if bonuses.items else 0
    
    return render_template('referrals/referral_history.html', 
                         bonuses=bonuses,
                         total_earnings=total_earnings)

@referrals_bp.route('/agent-level')
@login_required
def agent_level():
    """Get current agent level and progress"""
    from config import Config
    
    current_level = current_user.agent_level
    level_config = Config.AGENT_LEVELS.get(current_level, None)
    
    # Calculate progress to next level
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
    
    progress = min(100, (current_user.referral_count / required * 100)) if required > 0 else 100
    
    return jsonify({
        'current_level': current_level,
        'referral_count': current_user.referral_count,
        'next_level': next_level,
        'members_required': required,
        'progress': progress,
        'salary': current_user.get_agent_salary() if current_level != 'none' else 0
    })

@referrals_bp.route('/earnings')
@login_required
def earnings():
    """Get referral earnings summary"""
    # Get all referral bonuses
    bonuses = ReferralBonus.query.filter_by(referrer_id=current_user.id).all()
    
    # Calculate statistics
    total_earnings = sum(b.amount for b in bonuses)  # Include all bonuses
    pending_earnings = sum(b.amount for b in bonuses if not b.is_paid)
    
    # Get referral count
    referral_count = User.query.filter_by(referred_by=current_user.id).count()
    
    # Get earnings by type
    deposit_commissions = [b for b in bonuses if b.type == 'deposit_commission']
    rental_commissions = [b for b in bonuses if b.type == 'rental_commission']
    
    return jsonify({
        'total_earnings': total_earnings,
        'pending_earnings': pending_earnings,
        'referral_count': referral_count,
        'deposit_commissions': len(deposit_commissions),
        'rental_commissions': len(rental_commissions),
        'recent_bonuses': [
            {
                'amount': b.amount,
                'type': b.type,
                'created_at': b.created_at.isoformat(),
                'is_paid': b.is_paid,
                'referred_username': User.query.get(b.referred_id).username if User.query.get(b.referred_id) else None
            } for b in bonuses[:5]
        ]
    })

@referrals_bp.route('/commission/<int:referral_id>')
@login_required
def commission_detail(referral_id):
    """Get details of a specific referral commission"""
    bonus = ReferralBonus.query.get_or_404(referral_id)
    
    # Check if the bonus belongs to the current user
    if bonus.referrer_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('referrals.index'))
    
    return jsonify({
        'id': bonus.id,
        'amount': bonus.amount,
        'type': bonus.type,
        'referrer_id': bonus.referrer_id,
        'referred_id': bonus.referred_id,
        'is_paid': bonus.is_paid,
        'paid_at': bonus.paid_at.isoformat() if bonus.paid_at else None,
        'created_at': bonus.created_at.isoformat()
    })