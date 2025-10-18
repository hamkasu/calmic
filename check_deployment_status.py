#!/usr/bin/env python3
"""
Complete Deployment Status Checker
Verifies configuration and checks database for missing photos
"""
import os
import sys
from photovault import create_app, db
from photovault.models import Photo, User

def check_deployment_status():
    """Check complete deployment status"""
    
    print("=" * 70)
    print("PhotoVault - Complete Deployment Status")
    print("=" * 70)
    print()
    
    # Environment detection
    is_railway = bool(os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PROJECT_ID'))
    env_name = os.environ.get('RAILWAY_ENVIRONMENT', 'development')
    
    if is_railway:
        print(f"📍 Environment: Railway ({env_name})")
    else:
        print(f"📍 Environment: Local/Development")
    
    print()
    print("-" * 70)
    print("1. Configuration Check")
    print("-" * 70)
    print()
    
    # Check database
    db_vars = ['DATABASE_URL', 'RAILWAY_DATABASE_URL', 'POSTGRES_URL', 'DATABASE_PRIVATE_URL']
    db_url = None
    db_ok = False
    
    for var in db_vars:
        if os.environ.get(var):
            db_url = os.environ.get(var)
            print(f"✅ Database: {var} is set")
            
            if 'sqlite' in db_url.lower():
                print(f"   🔴 WARNING: Using SQLite - data will be lost on restart!")
                db_ok = False
            elif 'postgresql' in db_url or 'postgres' in db_url:
                print(f"   ✅ Using PostgreSQL - data persists")
                db_ok = True
            break
    
    if not db_url:
        print(f"🔴 ERROR: No database configured!")
        db_ok = False
    
    print()
    
    # Check file storage
    upload_folder = os.environ.get('UPLOAD_FOLDER', 'photovault/uploads')
    storage_ok = False
    
    if upload_folder.startswith('/data'):
        print(f"✅ File Storage: {upload_folder} (Railway Volume - persistent)")
        storage_ok = True
    else:
        print(f"⚠️  File Storage: {upload_folder} (ephemeral - files lost on restart)")
        storage_ok = False
    
    print()
    
    # Check secret key
    secret_ok = bool(os.environ.get('SECRET_KEY') or os.environ.get('RAILWAY_SECRET_KEY'))
    if secret_ok:
        print(f"✅ Secret Key: Configured")
    else:
        print(f"⚠️  Secret Key: Not set (sessions will reset)")
    
    print()
    print("-" * 70)
    print("2. Database Status")
    print("-" * 70)
    print()
    
    app = create_app()
    
    with app.app_context():
        try:
            # Count users
            user_count = User.query.count()
            print(f"👥 Total Users: {user_count}")
            
            # Count photos
            total_photos = Photo.query.count()
            print(f"📸 Total Photos in DB: {total_photos}")
            
            # Check for missing files
            if total_photos > 0:
                missing_count = 0
                existing_count = 0
                
                for photo in Photo.query.all():
                    if os.path.exists(photo.file_path):
                        existing_count += 1
                    else:
                        missing_count += 1
                
                print(f"   ✅ Files exist: {existing_count}")
                print(f"   🔴 Files missing: {missing_count}")
                
                if missing_count > 0:
                    print()
                    print(f"   ⚠️  {missing_count} photos are in database but files are missing!")
                    print(f"   Run: railway run python cleanup_missing_photos.py")
            
            print()
            
        except Exception as e:
            print(f"❌ Error querying database: {e}")
            print()
    
    print("-" * 70)
    print("3. Action Items")
    print("-" * 70)
    print()
    
    actions_needed = []
    
    if not db_ok:
        actions_needed.append("🔴 CRITICAL: Add PostgreSQL database to Railway")
    
    if not storage_ok and is_railway:
        actions_needed.append("⚠️  IMPORTANT: Set up Railway Volume for file persistence")
    
    if not secret_ok:
        actions_needed.append("⚠️  RECOMMENDED: Set SECRET_KEY environment variable")
    
    with app.app_context():
        missing_count = sum(1 for photo in Photo.query.all() if not os.path.exists(photo.file_path))
        if missing_count > 0:
            actions_needed.append(f"🗑️  CLEANUP: Remove {missing_count} orphaned photo records")
    
    if actions_needed:
        for action in actions_needed:
            print(f"  {action}")
    else:
        print("  ✅ No actions needed - everything is properly configured!")
    
    print()
    print("=" * 70)
    print("Quick Fix Commands")
    print("=" * 70)
    print()
    
    if actions_needed:
        if not db_ok:
            print("# Add PostgreSQL (via Railway dashboard):")
            print("#   Dashboard → + New → Database → PostgreSQL")
            print()
        
        if not storage_ok and is_railway:
            print("# Add Railway Volume (via Railway dashboard):")
            print("#   Service → Settings → Volumes → New Volume")
            print("#   Mount path: /data")
            print("railway variables set UPLOAD_FOLDER=/data/uploads")
            print()
        
        if not secret_ok:
            print("# Set secret key:")
            print("railway variables set SECRET_KEY=$(openssl rand -base64 32)")
            print()
        
        if missing_count > 0:
            print("# Clean up missing photos:")
            print("railway run python cleanup_missing_photos.py        # Preview")
            print("railway run python cleanup_missing_photos.py --execute  # Execute")
            print()
    
    print("# Verify configuration:")
    print("railway run python verify_railway_config.py")
    print()
    
    # Return exit code based on critical issues
    if not db_ok:
        return 1
    elif not storage_ok and is_railway:
        return 1
    else:
        return 0

if __name__ == '__main__':
    exit_code = check_deployment_status()
    sys.exit(exit_code)
