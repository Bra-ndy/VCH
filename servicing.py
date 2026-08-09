from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func

from models import db, ServiceHistory, Transaction, Notification
from utils.earnings import process_service_earning

servicing_bp = Blueprint('servicing', __name__, url_prefix='/servicing')

@servicing_bp.route('/')
@login_required
def servicing():
    # Get today's service
    today = datetime.utcnow().date()
    today_service = ServiceHistory.query.filter(
        ServiceHistory.user_id == current_user.id,
        db.func.date(ServiceHistory.service_date) == today
    ).first()
    
    # Get service history
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    history = ServiceHistory.query.filter_by(user_id=current_user.id)\
        .order_by(ServiceHistory.service_date.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Get total service earnings
    total_earnings = db.session.query(func.sum(ServiceHistory.earning))\
        .filter_by(user_id=current_user.id).scalar() or 0
    
    return render_template('servicing/servicing.html',
                         today_service=today_service,
                         history=history,
                         total_earnings=total_earnings)

@servicing_bp.route('/perform', methods=['POST'])
@login_required
def perform_service():
    """Perform daily servicing"""
    try:
        # Check if already performed today
        today = datetime.utcnow().date()
        existing = ServiceHistory.query.filter(
            ServiceHistory.user_id == current_user.id,
            db.func.date(ServiceHistory.service_date) == today
        ).first()
        
        if existing:
            return jsonify({'error': 'Daily servicing already performed today'}), 400
        
        # Process service earning
        service = process_service_earning(current_user.id)
        
        return jsonify({
            'success': True,
            'earning': service.earning,
            'service_date': service.service_date.isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@servicing_bp.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    history = ServiceHistory.query.filter_by(user_id=current_user.id)\
        .order_by(ServiceHistory.service_date.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('servicing/service_history.html', history=history)