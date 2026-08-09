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
def referrals():
    # Get referred users
    referred_users = User.query.filter_by(referred_by=current_user.id).all()
    
    # Get referral bonuses
    bonuses = ReferralBonus.query.filter_by(referrer_id=current_user.id)\
        .order_by(ReferralBonus.created_at.desc()).all()
    
    # Calculate total referral earnings
    total_earnings = db.session.query(func.sum(ReferralBonus.amount))\
        .filter_by(referrer_id=current_user.id, is_paid=True).scalar() or 0
    
    # Get referral link
    referral_link = f"{request.host_url}auth/register?ref={current_user.referral_code}"
    
    return render_template('referrals/referrals.html',
                         referred_users=referred_users,
                         bonuses=bonuses,
                         total_earnings=total_earnings,
                         referral_link=referral_link)

@referrals_bp.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    bonuses = ReferralBonus.query.filter_by(referrer_id=current_user.id)\
        .order_by(ReferralBonus.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('referrals/referral_history.html', bonuses=bonuses)

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