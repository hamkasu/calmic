#!/usr/bin/env python3
"""
Railway Deployment Diagnostic Script
Run this on Railway to diagnose deployment issues
"""
import os
import sys

def check_environment():
    """Check if required environment variables are set"""
    print("=" * 60)
    print("RAILWAY DEPLOYMENT DIAGNOSTICS")
    print("=" * 60)
    print()
    
    # Check Flask configuration
    print("1. Flask Configuration:")
    flask_config = os.environ.get('FLASK_CONFIG', 'NOT SET')
    print(f"   FLASK_CONFIG: {flask_config}")
    if flask_config != 'production':
        print("   ⚠️  WARNING: Should be 'production' on Railway")
    else:
        print("   ✅ OK")
    print()
    
    # Check database configuration
    print("2. Database Configuration:")
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Mask password for security
        if '@' in database_url:
            parts = database_url.split('@')
            user_part = parts[0].split('//')[1].split(':')[0]
            masked_url = f"postgresql://{user_part}:***@{parts[1]}"
            print(f"   DATABASE_URL: {masked_url}")
        else:
            print(f"   DATABASE_URL: {database_url[:30]}...")
        print("   ✅ Database URL is configured")
    else:
        print("   DATABASE_URL: NOT SET")
        print("   ❌ CRITICAL: PostgreSQL database not configured!")
        print()
        print("   TO FIX:")
        print("   1. Go to Railway dashboard → Your project")
        print("   2. Click '+ New' → Database → PostgreSQL")
        print("   3. Railway will auto-set DATABASE_URL")
        print("   4. Redeploy your app")
    print()
    
    # Check secret key
    print("3. Security Configuration:")
    secret_key = os.environ.get('SECRET_KEY')
    if secret_key:
        print(f"   SECRET_KEY: {'*' * 20} (set)")
        print("   ✅ Secret key is configured")
    else:
        print("   SECRET_KEY: NOT SET")
        print("   ⚠️  WARNING: Using temporary secret key (sessions will not persist)")
        print()
        print("   TO FIX:")
        print("   railway variables set SECRET_KEY=$(openssl rand -base64 32)")
    print()
    
    # Check storage configuration
    print("4. File Storage Configuration:")
    upload_folder = os.environ.get('UPLOAD_FOLDER')
    railway_volume = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
    
    if railway_volume:
        print(f"   RAILWAY_VOLUME_MOUNT_PATH: {railway_volume}")
        print("   ✅ Railway Volume detected! (auto-configured)")
        if upload_folder:
            print(f"   UPLOAD_FOLDER (manual): {upload_folder}")
        else:
            print(f"   UPLOAD_FOLDER (auto): {railway_volume}/uploads")
        print("   ✅ Files will persist across restarts")
    elif upload_folder:
        print(f"   UPLOAD_FOLDER: {upload_folder}")
        if upload_folder.startswith('/data'):
            print("   ✅ Using persistent storage")
        else:
            print("   ⚠️  WARNING: Using ephemeral storage (files will be lost on restart)")
    else:
        print("   RAILWAY_VOLUME_MOUNT_PATH: NOT SET")
        print("   UPLOAD_FOLDER: NOT SET (using default)")
        print("   ⚠️  WARNING: Files stored in ephemeral directory")
        print()
        print("   TO FIX (for persistent storage):")
        print("   1. Go to Railway Dashboard → Your service → Settings")
        print("   2. Click '+ New Volume' in Volumes section")
        print("   3. Railway will auto-set RAILWAY_VOLUME_MOUNT_PATH")
        print("   4. Redeploy - app will automatically use the volume")
    print()
    
    # Check optional services
    print("5. Optional Services:")
    openai_key = os.environ.get('OPENAI_API_KEY')
    sendgrid_key = os.environ.get('SENDGRID_API_KEY')
    stripe_key = os.environ.get('STRIPE_SECRET_KEY')
    
    print(f"   OPENAI_API_KEY: {'✅ Configured' if openai_key else '⚪ Not set (AI features disabled)'}")
    print(f"   SENDGRID_API_KEY: {'✅ Configured' if sendgrid_key else '⚪ Not set (email disabled)'}")
    print(f"   STRIPE_SECRET_KEY: {'✅ Configured' if stripe_key else '⚪ Not set (payments disabled)'}")
    print()
    
    # Test database connection
    print("6. Database Connection Test:")
    if database_url:
        try:
            from photovault import create_app
            from photovault.config import ProductionConfig
            
            app = create_app(ProductionConfig)
            with app.app_context():
                from photovault.extensions import db
                db.session.execute(db.text('SELECT 1'))
                print("   ✅ Database connection successful")
                
                # Check if tables exist
                from photovault.models import SubscriptionPlan
                plan_count = SubscriptionPlan.query.count()
                print(f"   ✅ Subscription plans table exists ({plan_count} plans)")
                
        except Exception as e:
            print(f"   ❌ Database connection failed: {str(e)}")
            print()
            print("   POSSIBLE CAUSES:")
            print("   - PostgreSQL addon not added to Railway project")
            print("   - Database migrations not run")
            print("   - Connection timeout or SSL issues")
    else:
        print("   ⏭️  Skipped (DATABASE_URL not set)")
    print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    critical_issues = []
    warnings = []
    
    if not database_url:
        critical_issues.append("PostgreSQL database not configured")
    if not secret_key:
        warnings.append("SECRET_KEY not set")
    railway_volume = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
    if not railway_volume and (not upload_folder or not upload_folder.startswith('/data')):
        warnings.append("File storage not persistent - add Railway Volume")
    
    if critical_issues:
        print("❌ CRITICAL ISSUES:")
        for issue in critical_issues:
            print(f"   - {issue}")
        print()
        print("The app will NOT work properly until these are fixed!")
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   - {warning}")
        print()
        print("The app will work but may have issues.")
    
    if not critical_issues and not warnings:
        print("✅ All checks passed! Your Railway deployment is properly configured.")
    
    print()
    print("=" * 60)

if __name__ == '__main__':
    check_environment()
