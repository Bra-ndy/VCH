# app.py - Production ready with PostgreSQL, logging, and health checks
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_mail import Mail
from flask_caching import Cache
from flask_socketio import SocketIO
import os
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

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
    
    # =============================================
    # LOGGING - Production Ready
    # =============================================
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(app.config.get('LOG_FILE', 'logs/vch.log'))
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # File handler for errors and info
        log_file = app.config.get('LOG_FILE', 'logs/vch.log')
        max_bytes = app.config.get('LOG_MAX_BYTES', 10485760)
        backup_count = app.config.get('LOG_BACKUP_COUNT', 10)
        
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_bytes, 
            backupCount=backup_count
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Also log to console for Render
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        console_handler.setLevel(logging.INFO)
        app.logger.addHandler(console_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('🚀 VCH application startup')
        app.logger.info(f'📊 Environment: {config_name}')
        app.logger.info(f'🗄️  Database: {app.config.get("SQLALCHEMY_DATABASE_URI", "unknown")[:50]}...')
    
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
    
    # =============================================
    # CONTEXT PROCESSOR - Add admin info and logo for all templates
    # =============================================
    @app.context_processor
    def utility_processor():
        return {
            'app_name': app.config.get('APP_NAME', 'VCH'),
            'current_year': datetime.now(timezone.utc).year,
            'agent_levels': app.config.get('AGENT_LEVELS', {}),
            'admin_name': app.config.get('ADMIN_NAME', 'WINNY LANGAT'),
            'admin_number': app.config.get('ADMIN_MPESA_NUMBER', '0753796259'),
            'logo_url': url_for('static', filename='images/logo.png') if os.path.exists(os.path.join(app.root_path, 'static', 'images', 'logo.png')) else None
        }
    
    # =============================================
    # HOME ROUTE
    # =============================================
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        vehicles = Vehicle.query.filter_by(is_active=True).order_by(Vehicle.sort_order).limit(6).all()
        return render_template('index.html', vehicles=vehicles)
    
    # =============================================
    # USER DASHBOARD
    # =============================================
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
    
    # =============================================
    # STATIC PAGES
    # =============================================
    @app.route('/about')
    def about():
        return render_template('about.html')
    
    @app.route('/faq')
    def faq():
        return render_template('faq.html')
    
    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        if request.method == 'POST':
            flash('Thank you for your message. We will get back to you soon!', 'success')
            return redirect(url_for('contact'))
        return render_template('contact.html')
    
    @app.route('/profile')
    @login_required
    def profile():
        return render_template('dashboard/profile.html')
    
    # =============================================
    # FAVICON
    # =============================================
    @app.route('/favicon.ico')
    def favicon():
        """Return empty response for favicon to avoid 404 errors"""
        try:
            return send_from_directory(os.path.join(app.root_path, 'static'),
                                       'favicon.ico', mimetype='image/vnd.microsoft.icon')
        except:
            return '', 204  # No content
    
    # =============================================
    # ERROR HANDLERS
    # =============================================
    @app.errorhandler(404)
    def not_found(error):
        app.logger.error(f'404 error: {request.url} - {request.remote_addr}')
        try:
            return render_template('errors/404.html'), 404
        except:
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
        app.logger.error(f'500 error: {str(error)} - {request.url}')
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
    
    # =============================================
    # HEALTH CHECK ENDPOINT
    # =============================================
    @app.route('/health')
    def health_check():
        """Health check endpoint for Render monitoring"""
        try:
            # Check database connection
            db.session.execute('SELECT 1')
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'database': 'connected',
                'environment': os.environ.get('FLASK_ENV', 'development'),
                'm_pesa': 'configured' if app.config.get('MPESA_CONSUMER_KEY') else 'not configured'
            })
        except Exception as e:
            app.logger.error(f'Health check failed: {str(e)}')
            return jsonify({
                'status': 'unhealthy', 
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 500
    
    # =============================================
    # DEBUG ENVIRONMENT CHECK (Remove in production)
    # =============================================
    @app.route('/env')
    def show_env():
        """Debug endpoint to check environment variables"""
        if app.config.get('DEBUG', False):
            import os
            env_vars = {
                'FLASK_ENV': os.environ.get('FLASK_ENV'),
                'PORT': os.environ.get('PORT'),
                'DATABASE_URL': os.environ.get('DATABASE_URL', 'not set')[:50] + '...' if os.environ.get('DATABASE_URL') else 'not set',
                'ADMIN_NAME': os.environ.get('ADMIN_NAME'),
                'ADMIN_MPESA_NUMBER': os.environ.get('ADMIN_MPESA_NUMBER'),
            }
            return jsonify(env_vars)
        return jsonify({'error': 'Not available in production'}), 403
    
    # =============================================
    # DATABASE INITIALIZATION AND SEEDING
    # =============================================
    with app.app_context():
        try:
            db.create_all()
            app.logger.info('✅ Database tables created/verified')
        except Exception as e:
            app.logger.error(f'❌ Error creating database tables: {str(e)}')
        
        # Seed initial data if needed
        try:
            from database.seed import seed_database
            seed_database()
            app.logger.info('✅ Database seeding completed!')
        except ImportError as e:
            app.logger.warning(f'⚠️ Seed module not found: {e}')
        except Exception as e:
            app.logger.warning(f'⚠️ Error seeding database: {e}')
        
        # Check if admin user exists, create if not
        try:
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
                app.logger.info('✅ Admin user created: admin@vch.com / Admin123!')
            else:
                app.logger.info('✅ Admin user already exists')
        except Exception as e:
            app.logger.error(f'❌ Error creating admin user: {str(e)}')
        
        # =============================================
        # VEHICLE SEEDING WITH IMAGES
        # =============================================
        try:
            vehicle_count = Vehicle.query.count()
            
            if vehicle_count == 0:
                # Seed all vehicles with images
                vehicles_data = [
                    {'name': 'Ferrari', 'brand': 'Ferrari', 'image': 'ferrari.jpg', 'rental_price': 10000, 'daily_earning': 500, 'rental_period': 30, 'sort_order': 1, 'is_active': True, 'is_available': True},
                    {'name': 'Porsche', 'brand': 'Porsche', 'image': 'porsche.jpg', 'rental_price': 8000, 'daily_earning': 400, 'rental_period': 30, 'sort_order': 2, 'is_active': True, 'is_available': True},
                    {'name': 'Jaguar', 'brand': 'Jaguar', 'image': 'jaguar.jpg', 'rental_price': 7000, 'daily_earning': 350, 'rental_period': 30, 'sort_order': 3, 'is_active': True, 'is_available': True},
                    {'name': 'Mercedes-Benz', 'brand': 'Mercedes-Benz', 'image': 'mercedes.jpg', 'rental_price': 5500, 'daily_earning': 290, 'rental_period': 30, 'sort_order': 4, 'is_active': True, 'is_available': True},
                    {'name': 'BMW', 'brand': 'BMW', 'image': 'bmw.jpg', 'rental_price': 4000, 'daily_earning': 230, 'rental_period': 30, 'sort_order': 5, 'is_active': True, 'is_available': True},
                    {'name': 'Isuzu', 'brand': 'Isuzu', 'image': 'isuzu.jpg', 'rental_price': 3500, 'daily_earning': 200, 'rental_period': 30, 'sort_order': 6, 'is_active': True, 'is_available': True},
                    {'name': 'Mazda', 'brand': 'Mazda', 'image': 'mazda.jpg', 'rental_price': 3000, 'daily_earning': 170, 'rental_period': 30, 'sort_order': 7, 'is_active': True, 'is_available': True},
                    {'name': 'Toyota', 'brand': 'Toyota', 'image': 'toyota.jpg', 'rental_price': 2500, 'daily_earning': 150, 'rental_period': 30, 'sort_order': 8, 'is_active': True, 'is_available': True}
                ]
                
                for v in vehicles_data:
                    vehicle = Vehicle(**v)
                    db.session.add(vehicle)
                db.session.commit()
                app.logger.info('✅ 8 Vehicles seeded successfully with images!')
            
            else:
                # Update existing vehicles with images if they don't have them
                vehicles_with_images = {
                    'Ferrari': 'ferrari.jpg',
                    'Porsche': 'porsche.jpg',
                    'Jaguar': 'jaguar.jpg',
                    'Mercedes-Benz': 'mercedes.jpg',
                    'BMW': 'bmw.jpg',
                    'Isuzu': 'isuzu.jpg',
                    'Mazda': 'mazda.jpg',
                    'Toyota': 'toyota.jpg'
                }
                
                updated = 0
                missing = []
                
                for name, image in vehicles_with_images.items():
                    vehicle = Vehicle.query.filter_by(name=name).first()
                    if vehicle:
                        if not vehicle.image:
                            vehicle.image = image
                            updated += 1
                            app.logger.info(f'✅ Updated {name} with image: {image}')
                    else:
                        missing.append(name)
                
                # Add any missing vehicles
                vehicle_data_map = {
                    'Ferrari': {'brand': 'Ferrari', 'image': 'ferrari.jpg', 'rental_price': 10000, 'daily_earning': 500, 'rental_period': 30, 'sort_order': 1},
                    'Porsche': {'brand': 'Porsche', 'image': 'porsche.jpg', 'rental_price': 8000, 'daily_earning': 400, 'rental_period': 30, 'sort_order': 2},
                    'Jaguar': {'brand': 'Jaguar', 'image': 'jaguar.jpg', 'rental_price': 7000, 'daily_earning': 350, 'rental_period': 30, 'sort_order': 3},
                    'Mercedes-Benz': {'brand': 'Mercedes-Benz', 'image': 'mercedes.jpg', 'rental_price': 5500, 'daily_earning': 290, 'rental_period': 30, 'sort_order': 4},
                    'BMW': {'brand': 'BMW', 'image': 'bmw.jpg', 'rental_price': 4000, 'daily_earning': 230, 'rental_period': 30, 'sort_order': 5},
                    'Isuzu': {'brand': 'Isuzu', 'image': 'isuzu.jpg', 'rental_price': 3500, 'daily_earning': 200, 'rental_period': 30, 'sort_order': 6},
                    'Mazda': {'brand': 'Mazda', 'image': 'mazda.jpg', 'rental_price': 3000, 'daily_earning': 170, 'rental_period': 30, 'sort_order': 7},
                    'Toyota': {'brand': 'Toyota', 'image': 'toyota.jpg', 'rental_price': 2500, 'daily_earning': 150, 'rental_period': 30, 'sort_order': 8}
                }
                
                for name in missing:
                    data = vehicle_data_map.get(name)
                    if data:
                        vehicle = Vehicle(
                            name=name,
                            brand=data['brand'],
                            image=data['image'],
                            rental_price=data['rental_price'],
                            daily_earning=data['daily_earning'],
                            rental_period=data['rental_period'],
                            sort_order=data['sort_order'],
                            is_active=True,
                            is_available=True
                        )
                        db.session.add(vehicle)
                        app.logger.info(f'✅ Added missing vehicle: {name}')
                
                if updated > 0 or len(missing) > 0:
                    db.session.commit()
                    app.logger.info(f'✅ Updated {updated} vehicles with images, added {len(missing)} missing vehicles')
                else:
                    app.logger.info(f'✅ All {vehicle_count} vehicles already have images')
                    
        except Exception as e:
            app.logger.error(f'❌ Error seeding vehicles: {str(e)}')
    
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
        # Production mode - use gunicorn or simple app.run
        print(f"🚀 Starting VCH in PRODUCTION mode on port {port}")
        app = create_app('production')
        # Use app.run for simplicity, but gunicorn is recommended
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # Development mode - use socketio with debug
        print(f"🔧 Starting VCH in DEVELOPMENT mode on port {port}")
        app = create_app('development')
        socketio.run(app, debug=True, host='0.0.0.0', port=port)