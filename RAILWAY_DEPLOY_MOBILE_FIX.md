# Fix iOS Mobile App 500 Errors on Railway

## Problem
The iOS app connects to Railway successfully but gets **500 errors** when accessing:
- `/api/dashboard` - Dashboard statistics  
- `/api/auth/profile` - User profile

## Root Cause
Your Railway production server likely has **outdated code** or **missing database columns** that were added recently to support the mobile app.

## Solution: Deploy Latest Code to Railway

### Step 1: Verify Git Status
```bash
git status
```

### Step 2: Add All Changes
```bash
git add .
```

### Step 3: Commit Changes
```bash
git commit -m "Fix mobile API endpoints for iOS app - dashboard and profile"
```

### Step 4: Push to Railway
```bash
git push origin main
```
(Or `git push origin master` if your branch is named master)

### Step 5: Wait for Deployment
- Railway will automatically detect the push
- Watch the deployment logs in Railway dashboard
- Wait for "Deployed successfully" message

### Step 6: Test iOS App
- Close and reopen the iOS app
- Try logging in again
- Dashboard should load without errors

## Database Schema Check

If errors persist after deployment, you may need to run migrations on Railway to add missing columns:

### Required Columns in User Table:
- `profile_picture` - Stores user avatar path

### To Check/Add via Railway CLI:
```bash
# Connect to Railway database
railway run python

# In Python shell:
from photovault import create_app, db
app = create_app()
with app.app_context():
    from sqlalchemy import text
    # Check if profile_picture column exists
    result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='user'"))
    columns = [row[0] for row in result]
    print("User table columns:", columns)
    
    # If profile_picture is missing, add it:
    if 'profile_picture' not in columns:
        db.session.execute(text("ALTER TABLE \"user\" ADD COLUMN profile_picture VARCHAR(500)"))
        db.session.commit()
        print("✅ Added profile_picture column")
```

## Expected Result
After deploying the latest code, your iOS app should:
- ✅ Load dashboard with photo statistics
- ✅ Display user profile information  
- ✅ Show all features without 500 errors

## Troubleshooting

If issues continue:
1. Check Railway logs for specific error messages
2. Verify environment variables are set correctly
3. Ensure database migrations have run
4. Test the API endpoints directly:
   ```bash
   curl https://extraordinary-contentment-production.up.railway.app/api/dashboard \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```
