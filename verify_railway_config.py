#!/usr/bin/env python3
"""
Railway Configuration Verification Script
Checks if your Railway deployment is configured for data persistence
"""
import os
import sys

def check_database():
    """Check database configuration"""
    db_vars = ['DATABASE_URL', 'RAILWAY_DATABASE_URL', 'POSTGRES_URL', 'DATABASE_PRIVATE_URL']
    db_url = None
    
    for var in db_vars:
        if os.environ.get(var):
            db_url = os.environ.get(var)
            print(f"✅ Database configured via {var}")
            
            if 'sqlite' in db_url.lower():
                print(f"🔴 ERROR: Using SQLite - data will be LOST on restart!")
                print(f"   Fix: Add PostgreSQL database to Railway project")
                return False
            elif 'postgresql' in db_url or 'postgres' in db_url:
                print(f"✅ Using PostgreSQL - data will persist")
                return True
            break
    
    if not db_url:
        print(f"🔴 ERROR: No database configured!")
        print(f"   Fix: Add PostgreSQL to Railway:")
        print(f"   1. Railway dashboard → Your project")
        print(f"   2. Click '+ New' → Database → PostgreSQL")
        print(f"   3. Redeploy your app")
        return False
    
    return True

def check_file_storage():
    """Check file storage configuration"""
    upload_folder = os.environ.get('UPLOAD_FOLDER', 'photovault/uploads')
    
    if upload_folder.startswith('/data'):
        print(f"✅ File storage configured with Railway Volume: {upload_folder}")
        return True
    else:
        print(f"⚠️  WARNING: Files stored in ephemeral directory: {upload_folder}")
        print(f"   Uploaded photos will be LOST on Railway restart!")
        print(f"   Fix: Mount a Railway Volume:")
        print(f"   1. Railway → Service → Settings → Volumes")
        print(f"   2. New Volume → Mount path: /data")
        print(f"   3. Set env var: UPLOAD_FOLDER=/data/uploads")
        print(f"   4. Redeploy")
        return False

def check_secret_key():
    """Check secret key configuration"""
    secret_vars = ['SECRET_KEY', 'RAILWAY_SECRET_KEY']
    
    for var in secret_vars:
        if os.environ.get(var):
            print(f"✅ Secret key configured via {var}")
            return True
    
    print(f"⚠️  WARNING: No SECRET_KEY set")
    print(f"   User sessions will reset on restart")
    print(f"   Fix: railway variables set SECRET_KEY=$(openssl rand -base64 32)")
    return False

def main():
    print("=" * 60)
    print("Railway Configuration Verification")
    print("=" * 60)
    print()
    
    # Check if running on Railway
    is_railway = bool(os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PROJECT_ID'))
    
    if is_railway:
        print(f"📍 Running on Railway environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'unknown')}")
    else:
        print(f"📍 Not running on Railway (local/development environment)")
    
    print()
    print("Checking configuration...")
    print("-" * 60)
    print()
    
    # Run checks
    db_ok = check_database()
    print()
    
    storage_ok = check_file_storage()
    print()
    
    secret_ok = check_secret_key()
    print()
    
    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    if db_ok and storage_ok and secret_ok:
        print("✅ All checks passed! Your Railway deployment is properly configured.")
        sys.exit(0)
    elif db_ok and secret_ok:
        print("⚠️  Database is persistent, but uploaded files will be lost on restart.")
        print("   Consider adding a Railway Volume for file persistence.")
        sys.exit(1)
    else:
        print("🔴 CRITICAL: Configuration issues found!")
        print("   Follow the fixes above to ensure data persistence.")
        sys.exit(1)

if __name__ == '__main__':
    main()
