# app.py - Updated version with M-Pesa integration and production-ready port
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_mail import Mail
from flask_caching import Cache
from flask_socketio import SocketIO
import os
from datetime import datetime, timezone

from config import config
from models import db, User, Vehicle, Rental, Transaction, ServiceHistory, ReferralBonus, Notification

# Initialize extensions (do this BEFORE importing blueprints)
mail = Mail()
cache = Cache()
socketio = SocketIO()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Import blueprints AFTER extensions are initialized
    from auth import auth_bp
    from wallet import wallet_bp
    from rentals import rentals_bp
    from referrals import referrals_bp
    from payments import payments_bp
    from withdrawals import withdrawals_bp
    from servicing import servicing_bp
    from admin import admin_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(wallet_bp, url_prefix='/wallet')
    app.register_blueprint(rentals_bp, url_prefix='/rentals')
    app.register_blueprint(referrals_bp, url_prefix='/referrals')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    app.register_blueprint(withdrawals_bp, url_prefix='/withdrawals')
    app.register_blueprint(servicing_bp, url_prefix='/servicing')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Context processor
    @app.context_processor
    def utility_processor():
        return {
            'app_name': app.config['APP_NAME'],
            'current_year': datetime.now(timezone.utc).year,
            'agent_levels': app.config.get('AGENT_LEVELS', {})
        }
    
    # Home route
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        vehicles = Vehicle.query.filter_by(is_active=True).order_by(Vehicle.sort_order).limit(6).all()
        return render_template('index.html', vehicles=vehicles)
    
    # User Dashboard
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Check if user is admin - redirect to admin dashboard
        is_admin = (
            current_user.email == 'admin@vch.com' or 
            current_user.agent_level == 'level2' or
            current_user.id == 1 or
            current_user.username == 'admin'
        )
        
        if is_admin:
            return redirect(url_for('admin.dashboard'))
        
        active_rentals = Rental.query.filter_by(user_id=current_user.id, status='active').all()
        recent_transactions = Transaction.query.filter_by(user_id=current_user.id)\
            .order_by(Transaction.created_at.desc()).limit(10).all()
        
        today = datetime.now(timezone.utc).date()
        today_earnings = Transaction.query.filter(
            Transaction.user_id == current_user.id,
            db.func.date(Transaction.created_at) == today,
            Transaction.type.in_(['rental_earning', 'service_earning', 'referral_bonus', 'agent_salary'])
        ).all()
        today_earnings_total = sum(t.amount for t in today_earnings)
        
        referral_count = User.query.filter_by(referred_by=current_user.id).count()
        
        return render_template('dashboard/dashboard.html',
                             active_rentals=active_rentals,
                             recent_transactions=recent_transactions,
                             today_earnings_total=today_earnings_total,
                             referral_count=referral_count)
    
    # About
    @app.route('/about')
    def about():
        return render_template('about.html')
    
    # FAQ
    @app.route('/faq')
    def faq():
        return render_template('faq.html')
    
    # Contact
    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        if request.method == 'POST':
            flash('Thank you for your message. We will get back to you soon!', 'success')
            return redirect(url_for('contact'))
        return render_template('contact.html')
    
    # Profile route
    @app.route('/profile')
    @login_required
    def profile():
        return render_template('dashboard/profile.html')
    
    # Favicon route to prevent 404 errors
    @app.route('/favicon.ico')
    def favicon():
        """Return empty response for favicon to avoid 404 errors"""
        try:
            return send_from_directory(os.path.join(app.root_path, 'static'),
                                       'favicon.ico', mimetype='image/vnd.microsoft.icon')
        except:
            return '', 204  # No content
    
    # Error handlers with fallback templates
    @app.errorhandler(404)
    def not_found(error):
        try:
            return render_template('errors/404.html'), 404
        except:
            # Fallback if template doesn't exist
            return """
            <!DOCTYPE html>
            <html>
            <head><title>404 - Page Not Found</title>
            <style>
                body { background: #0b0b0b; color: white; font-family: Arial; text-align: center; padding: 3rem; }
                h1 { color: #d4af37; font-size: 4rem; }
                .gold { color: #d4af37; }
                a { color: #d4af37; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
            </head>
            <body>
                <h1>404</h1>
                <h2>Page Not Found</h2>
                <p style="color: #9a9a9a;">The page you are looking for could not be found.</p>
                <a href="/">← Back to Home</a>
            </body>
            </html>
            """, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        try:
            return render_template('errors/500.html'), 500
        except:
            return """
            <!DOCTYPE html>
            <html>
            <head><title>500 - Server Error</title>
            <style>
                body { background: #0b0b0b; color: white; font-family: Arial; text-align: center; padding: 3rem; }
                h1 { color: #d4af37; font-size: 4rem; }
                a { color: #d4af37; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
            </head>
            <body>
                <h1>500</h1>
                <h2>Internal Server Error</h2>
                <p style="color: #9a9a9a;">Something went wrong. Please try again later.</p>
                <a href="/">← Back to Home</a>
            </body>
            </html>
            """, 500
    
    # Health check endpoint for monitoring
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        try:
            # Check database
            db.session.execute('SELECT 1')
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'database': 'connected',
                'm_pesa': 'configured' if app.config.get('MPESA_CONSUMER_KEY') else 'not configured'
            })
        except Exception as e:
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Seed initial data if needed
        try:
            from database.seed import seed_database
            seed_database()
            print("✅ Database seeding completed!")
        except ImportError as e:
            print(f"⚠️ Seed module not found: {e}")
        except Exception as e:
            print(f"⚠️ Error seeding database: {e}")
        
        # Check if admin user exists, create if not
        admin = User.query.filter_by(email='admin@vch.com').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@vch.com',
                phone='254700000001',
                full_name='System Administrator',
                is_verified=True,
                is_active=True,
                agent_level='level2',
                balance=100000,
                total_deposited=100000
            )
            admin.set_password('Admin123!')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created: admin@vch.com / Admin123!")
        
        # Create sample vehicles if none exist
        if Vehicle.query.count() == 0:
            vehicles_data = [
                {'name': 'Ferrari', 'brand': 'Ferrari', 'rental_price': 10000, 'daily_earning': 500, 'rental_period': 30, 'sort_order': 1, 'is_active': True, 'is_available': True},
                {'name': 'Porsche', 'brand': 'Porsche', 'rental_price': 8000, 'daily_earning': 400, 'rental_period': 30, 'sort_order': 2, 'is_active': True, 'is_available': True},
                {'name': 'Jaguar', 'brand': 'Jaguar', 'rental_price': 7000, 'daily_earning': 350, 'rental_period': 30, 'sort_order': 3, 'is_active': True, 'is_available': True},
                {'name': 'Mercedes-Benz', 'brand': 'Mercedes-Benz', 'rental_price': 5500, 'daily_earning': 290, 'rental_period': 30, 'sort_order': 4, 'is_active': True, 'is_available': True},
                {'name': 'BMW', 'brand': 'BMW', 'rental_price': 4000, 'daily_earning': 230, 'rental_period': 30, 'sort_order': 5, 'is_active': True, 'is_available': True},
                {'name': 'Isuzu', 'brand': 'Isuzu', 'rental_price': 3500, 'daily_earning': 200, 'rental_period': 30, 'sort_order': 6, 'is_active': True, 'is_available': True},
                {'name': 'Mazda', 'brand': 'Mazda', 'rental_price': 3000, 'daily_earning': 170, 'rental_period': 30, 'sort_order': 7, 'is_active': True, 'is_available': True},
                {'name': 'Toyota', 'brand': 'Toyota', 'rental_price': 2500, 'daily_earning': 150, 'rental_period': 30, 'sort_order': 8, 'is_active': True, 'is_available': True}
            ]
            
            for v in vehicles_data:
                vehicle = Vehicle(**v)
                db.session.add(vehicle)
            db.session.commit()
            print("✅ Vehicles seeded successfully!")
    
    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============================================================
# PRODUCTION READY - MODIFIED FOR RENDER DEPLOYMENT
# ============================================================
if __name__ == '__main__':
    # Get port from environment variable (Render uses PORT)
    port = int(os.environ.get('PORT', 10000))
    
    # Check if we're in production or development
    is_production = os.environ.get('FLASK_ENV', 'development') == 'production'
    
    if is_production:
        # Production mode - use simple app.run with minimal resources
        print(f"🚀 Starting VCH in PRODUCTION mode on port {port}")
        app = create_app('production')
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # Development mode - use socketio with debug
        print(f"🔧 Starting VCH in DEVELOPMENT mode on port {port}")
        app = create_app('development')
        socketio.run(app, debug=True, host='0.0.0.0', port=port)