"""
StoryKeep Application Factory
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
"""
# photovault/__init__.py

from flask import Flask
from photovault.extensions import db, login_manager, migrate, csrf, limiter
from photovault.config import config
import os

# Register HEIC decoder for iOS image support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass  # pillow-heif not installed

def _seed_subscription_plans(app):
    """Ensure all default subscription plans exist in the database (upsert behavior)"""
    from photovault.models import SubscriptionPlan
    from decimal import Decimal
    
    # Define default subscription plans for Malaysian market
    default_plans = [
        {
            'name': 'free',
            'display_name': 'Free Plan',
            'description': 'Get started with basic photo storage',
            'price_myr': Decimal('0.00'),
            'sst_rate': Decimal('0.00'),
            'storage_gb': 0.5,
            'max_photos': None,
            'max_family_vaults': 1,
            'ai_enhancement_quota': 5,
            'face_detection': True,
            'photo_enhancement': True,
            'smart_tagging': False,
            'social_media_integration': False,
            'api_access': False,
            'priority_support': False,
            'billing_period': 'monthly',
            'is_active': True,
            'is_featured': False,
            'sort_order': 1
        },
        {
            'name': 'personal',
            'display_name': 'Personal Plan',
            'description': 'Perfect for personal photo management',
            'price_myr': Decimal('12.90'),
            'sst_rate': Decimal('6.00'),
            'storage_gb': 5,
            'max_photos': None,
            'max_family_vaults': 2,
            'ai_enhancement_quota': 25,
            'face_detection': True,
            'photo_enhancement': True,
            'smart_tagging': True,
            'social_media_integration': False,
            'api_access': False,
            'priority_support': False,
            'billing_period': 'monthly',
            'is_active': True,
            'is_featured': False,
            'sort_order': 2
        },
        {
            'name': 'family',
            'display_name': 'Family Plan',
            'description': 'Affordable storage for everyday photos',
            'price_myr': Decimal('24.90'),
            'sst_rate': Decimal('6.00'),
            'storage_gb': 25,
            'max_photos': None,
            'max_family_vaults': 5,
            'ai_enhancement_quota': 75,
            'face_detection': True,
            'photo_enhancement': True,
            'smart_tagging': True,
            'social_media_integration': False,
            'api_access': False,
            'priority_support': True,
            'billing_period': 'monthly',
            'is_active': True,
            'is_featured': True,
            'sort_order': 3
        },
        {
            'name': 'pro',
            'display_name': 'Pro Plan',
            'description': 'Unlimited storage and all premium features',
            'price_myr': Decimal('49.90'),
            'sst_rate': Decimal('6.00'),
            'storage_gb': 500,
            'max_photos': None,
            'max_family_vaults': 20,
            'ai_enhancement_quota': 500,
            'face_detection': True,
            'photo_enhancement': True,
            'smart_tagging': True,
            'social_media_integration': True,
            'api_access': True,
            'priority_support': True,
            'billing_period': 'monthly',
            'is_active': True,
            'is_featured': False,
            'sort_order': 4
        }
    ]
    
    try:
        plans_created = 0
        plans_updated = 0
        
        # Upsert each plan - create if missing, update if exists
        for plan_data in default_plans:
            plan_name = plan_data['name']
            existing_plan = SubscriptionPlan.query.filter_by(name=plan_name).first()
            
            if existing_plan:
                # Update existing plan with current defaults
                for key, value in plan_data.items():
                    if key != 'name':  # Don't update the unique name field
                        setattr(existing_plan, key, value)
                plans_updated += 1
            else:
                # Create new plan
                plan = SubscriptionPlan(**plan_data)
                db.session.add(plan)
                plans_created += 1
        
        db.session.commit()
        
        if plans_created > 0 or plans_updated > 0:
            app.logger.info(f"Subscription plans: created {plans_created}, updated {plans_updated}")
        else:
            app.logger.info("All subscription plans already up to date")
            
    except Exception as e:
        app.logger.error(f"Failed to seed subscription plans: {str(e)}")
        db.session.rollback()


def _create_superuser_if_needed(app):
    """Create superuser account from environment variables if no superuser exists"""
    from photovault.models import User
    
    try:
        # Check if any superuser already exists
        if User.query.filter_by(is_superuser=True).first():
            return
    except Exception as e:
        # Tables don't exist yet (likely during migration), skip superuser creation
        app.logger.info(f"Skipping superuser creation - tables not ready: {str(e)}")
        return
        
    # Get superuser credentials from environment variables
    username = os.environ.get('PHOTOVAULT_SUPERUSER_USERNAME')
    email = os.environ.get('PHOTOVAULT_SUPERUSER_EMAIL')
    password = os.environ.get('PHOTOVAULT_SUPERUSER_PASSWORD')
    
    if username and email and password:
        try:
            # Check if user with same username or email already exists
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                # Make existing user a superuser
                existing_user.is_superuser = True
                existing_user.is_admin = True
                db.session.commit()
                app.logger.info(f"Made existing user {existing_user.username} a superuser")
            else:
                # Create new superuser
                superuser = User(
                    username=username,
                    email=email,
                    is_admin=True,
                    is_superuser=True
                )
                superuser.set_password(password)
                db.session.add(superuser)
                db.session.commit()
                app.logger.info(f"Created superuser account: {username}")
        except Exception as e:
            app.logger.error(f"Failed to create superuser: {str(e)}")
            db.session.rollback()

def create_app(config_class=None):
    """Application factory"""
    static_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
    template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    app = Flask(__name__, static_folder=static_folder, template_folder=template_folder)
    
    # Configuration
    if config_class is None:
        config_name = os.environ.get('FLASK_CONFIG') or 'development'
        config_class = config.get(config_name, config['default'])
    
    if isinstance(config_class, str):
        config_class = config.get(config_class, config['default'])
    
    app.config.from_object(config_class)
    
    # Initialize configuration
    config_class.init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from photovault.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from photovault.routes.main import main_bp
    from photovault.routes.auth import auth_bp
    from photovault.routes.upload import upload_bp
    from photovault.routes.photo_detection import photo_detection_bp
    from photovault.routes.admin import admin_bp
    from photovault.routes.admin_export import admin_export_bp
    from photovault.routes.superuser import superuser_bp
    from photovault.routes.photo import photo_bp
    from photovault.routes.camera_routes import camera_bp
    from photovault.routes.mobile_api import mobile_api_bp
    from photovault.routes.gallery import gallery_bp
    from photovault.routes.family import family_bp
    from photovault.routes.smart_tagging import smart_tagging_bp
    from photovault.routes.social_media import social_media_bp
    from photovault.routes.colorization import colorization_bp
    from photovault.routes.damage_repair import damage_repair_bp
    from photovault.routes.mfa import mfa_bp
    from photovault.routes.oauth import oauth_bp
    from photovault.billing import billing_bp
    
    # Initialize OAuth
    from photovault.utils.oauth import init_oauth
    init_oauth(app)
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(mfa_bp)
    app.register_blueprint(oauth_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(photo_detection_bp)
    app.register_blueprint(camera_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(admin_export_bp, url_prefix='/admin')
    app.register_blueprint(superuser_bp, url_prefix='/superuser')
    # Exempt entire mobile API blueprint from CSRF protection (uses JWT auth instead)
    csrf.exempt(mobile_api_bp)
    # Register mobile_api_bp - mobile uses /api/upload, web uses /api/web/upload
    app.register_blueprint(mobile_api_bp)
    app.register_blueprint(photo_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(family_bp)
    app.register_blueprint(smart_tagging_bp)
    app.register_blueprint(social_media_bp)
    app.register_blueprint(colorization_bp)
    app.register_blueprint(damage_repair_bp)
    app.register_blueprint(billing_bp)
    
    # Note: Upload file serving is handled securely via gallery.uploaded_file route with authentication
    
    # Add cache control headers for Replit environment
    @app.after_request
    def add_cache_control_headers(response):
        """Add cache control headers to prevent caching issues in Replit proxy"""
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    # Subscription enforcement middleware
    @app.before_request
    def enforce_subscription():
        """Ensure authenticated users have selected a subscription plan"""
        from flask import request, redirect, url_for
        from flask_login import current_user
        
        # Skip check for non-authenticated users
        if not current_user.is_authenticated:
            return None
        
        # Skip check for admin/superuser accounts
        if current_user.is_admin or current_user.is_superuser:
            return None
        
        # List of routes that don't require a subscription
        public_routes = [
            'auth.login',
            'auth.logout',
            'auth.register',
            'auth.forgot_password',
            'auth.reset_password',
            'billing.plans',
            'billing.subscribe',
            'billing.success',
            'billing.dashboard',
            'main.about',
            'main.terms',
            'main.privacy',
            'main.contact',
            'main.features',
            'main.api_health',
            'main.db_health',
            'main.health_check',
            'static'
        ]
        
        # Get current endpoint
        endpoint = request.endpoint
        
        # Skip check for public routes
        if endpoint in public_routes or (endpoint and endpoint.startswith('auth.')):
            return None
        
        # Check if user has an active subscription
        from photovault.models import UserSubscription
        active_subscription = UserSubscription.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).first()
        
        # If no active subscription, redirect to plans page
        if not active_subscription:
            from flask import flash
            flash('Please choose a subscription plan to access PhotoVault features.', 'info')
            return redirect(url_for('billing.plans'))
        
        return None
    
    # Initialize database - with improved error handling for Railway/production
    with app.app_context():
        try:
            # Only run create_all in development - production should use migrations
            # Use FLASK_CONFIG as authoritative source of environment
            is_development = os.environ.get('FLASK_CONFIG', 'development') == 'development'
            
            if is_development:
                db.create_all()
                app.logger.info("Database tables initialized successfully (development mode)")
            else:
                # In production, verify database connectivity
                db.session.execute(db.text('SELECT 1'))
                app.logger.info("Database connection verified (production mode)")
                
                # AUTO-MIGRATION: Run migrations automatically in production
                # This is a quick fix for Railway deployments
                try:
                    import alembic.config
                    import os as migration_os
                    
                    migrations_path = migration_os.path.join(migration_os.path.dirname(migration_os.path.dirname(__file__)), 'migrations')
                    alembic_cfg = alembic.config.Config()
                    alembic_cfg.set_main_option('script_location', migrations_path)
                    alembic_cfg.set_main_option('sqlalchemy.url', app.config['SQLALCHEMY_DATABASE_URI'])
                    
                    app.logger.info("Running database migrations automatically...")
                    from alembic import command
                    command.upgrade(alembic_cfg, 'head')
                    app.logger.info("✅ Database migrations completed successfully")
                except Exception as migration_error:
                    app.logger.warning(f"Auto-migration via Alembic failed: {str(migration_error)}")
                    app.logger.info("Attempting direct column addition as fallback...")
                    
                    # Fallback: Add missing columns directly if they don't exist
                    try:
                        from sqlalchemy import inspect, text
                        inspector = inspect(db.engine)
                        
                        # Check if subscription_plan table exists
                        if 'subscription_plan' in inspector.get_table_names():
                            columns = [col['name'] for col in inspector.get_columns('subscription_plan')]
                            
                            # Add social_media_integration column if missing
                            if 'social_media_integration' not in columns:
                                app.logger.info("Adding missing column: social_media_integration")
                                db.session.execute(text(
                                    'ALTER TABLE subscription_plan ADD COLUMN social_media_integration BOOLEAN DEFAULT false'
                                ))
                                db.session.commit()
                                app.logger.info("✅ Added social_media_integration column")
                            
                            app.logger.info("✅ Database schema updated successfully")
                    except Exception as fallback_error:
                        app.logger.error(f"Fallback migration also failed: {str(fallback_error)}")
                        app.logger.error("Manual migration may be required")
            
            # Seed default subscription plans (only if db connection works)
            _seed_subscription_plans(app)
            
            # Bootstrap superuser account if environment variables are set
            _create_superuser_if_needed(app)
        except Exception as e:
            # Log error but don't crash the app - allow it to start even if DB init fails
            # This allows health checks to work and helps diagnose Railway deployment issues
            app.logger.error(f"Database initialization error: {str(e)}")
            app.logger.error("App will continue to start, but database operations may fail")
            # In production, this will be caught by health checks
    
    return app