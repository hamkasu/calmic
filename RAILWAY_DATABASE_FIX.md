# Railway Database Migration Fix

## Problem
Railway's production database didn't have any tables created because the migration script wasn't running before the app started.

**Error:**
```
(psycopg2.errors.UndefinedTable) relation "subscription_plan" does not exist
(psycopg2.errors.UndefinedTable) relation "user" does not exist
```

## Root Cause
The `railway.json` deployment configuration was only running `gunicorn` directly, without executing the `release.py` script that creates database tables and runs migrations.

## Fix Applied
Updated `railway.json` to run migrations **before** starting the app:

**Old:**
```json
"startCommand": "gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 ..."
```

**New:**
```json
"startCommand": "python release.py && gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 ..."
```

## What release.py Does
1. ✅ Connects to Railway's PostgreSQL database
2. ✅ Runs Flask-Migrate to create/update all tables
3. ✅ Adds missing columns (is_active, is_admin, is_superuser, etc.)
4. ✅ Creates subscription_plan, user, photo, album, and all other tables
5. ✅ Downloads colorization AI models if needed
6. ✅ Verifies environment configuration

## How to Deploy This Fix to Railway

### Step 1: Push Changes to GitHub
```bash
git add railway.json Procfile RAILWAY_DATABASE_FIX.md
git commit -m "Fix Railway database migration - run release.py before starting app"
git push origin main
```

### Step 2: Railway Auto-Deploys
Railway will detect the changes and automatically:
1. ⏳ Build your application
2. ⏳ Run `python release.py` (creates all database tables)
3. ⏳ Start `gunicorn` (starts your app)

### Step 3: Verify Deployment
Once deployed, your Railway app logs should show:
```
PhotoVault Release: Starting deployment tasks...
PhotoVault Release: Database migrations completed successfully
PhotoVault Release: All deployment tasks completed successfully
PhotoVault WSGI: App created successfully, ready to handle requests
```

## What This Fixes
✅ All database tables will be created automatically  
✅ subscription_plan table created with Free, Basic, Pro, Premium, Enterprise plans  
✅ user table created with all required columns  
✅ photo, album, family_vault, and all other tables created  
✅ Database schema matches your local development environment  
✅ iOS app will be able to register, login, and fetch data  

## Testing After Deployment
1. **Test iOS Registration**: Create a new account via the iOS app
2. **Test iOS Login**: Login with the new account
3. **Test Dashboard API**: Should show 0 photos, 0 albums (fresh account)
4. **Test Gallery**: Should show empty state (no photos yet)
5. **Upload a Photo**: Test the digitizer/camera upload

## Important Notes
- ⚠️ The first deployment after this fix may take 1-2 minutes longer (one-time table creation)
- ⚠️ Future deployments will be faster (tables already exist, only schema changes run)
- ✅ Your local Replit development database is unaffected
- ✅ This fix ensures production database stays in sync with code changes

---
**Status**: Ready to deploy
**Action Required**: Push to GitHub (Railway will handle the rest)
