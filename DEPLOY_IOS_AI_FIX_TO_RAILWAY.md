# Deploy iOS AI Enhancement Fix to Railway

## What Was Fixed

Fixed the iOS app error: **"No module named 'photovault.utils.app_storage'"** and **"Error 500"** when trying to use AI colorization/enhancement features.

### Changes Made:
1. ✅ Fixed 3 incorrect import statements in `mobile_api.py`
2. ✅ Added missing `download_to_temp()` method to `AppStorageService`
3. ✅ Created SQL script to fix AI quota database issues

## Deployment Steps

### Step 1: Run the Database Fix (Already Done?)

If you already ran the SQL script from `RAILWAY_IOS_AI_QUOTA_FIX.sql`, skip to Step 2.

Otherwise:
1. Go to Railway → PostgreSQL database → Data tab → Query
2. Copy and paste the entire SQL from `RAILWAY_IOS_AI_QUOTA_FIX.sql`
3. Click "Run Query"

### Step 2: Deploy Code Changes to Railway

Railway should automatically deploy when you push to your git repository. Here's how:

#### Option A: If Railway is Connected to Git (Recommended)

Railway will automatically detect the changes and deploy them. Just wait for the deployment to complete.

#### Option B: Manual Deploy via Railway CLI

If auto-deploy isn't working:

```bash
# Install Railway CLI if you haven't
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Deploy
railway up
```

### Step 3: Restart Railway Service

After deployment completes:

1. Go to your Railway project
2. Click on your **Flask/PhotoVault service** (not the database)
3. Click **"Settings"**
4. Scroll down and click **"Restart"**
5. Wait 30-60 seconds for the service to fully restart

### Step 4: Test on iOS

1. **Force quit** the StoryKeep app on your iPhone (swipe up from app switcher)
2. **Reopen** the app
3. Try using an AI enhancement feature:
   - Colorization
   - AI Restore
   - Sharpen

Expected result: ✅ The AI feature should work without errors!

## What to Monitor

After deployment, check Railway logs for:

```bash
# Good signs:
INFO:photovault:Database tables initialized successfully
INFO:photovault:Subscription plans: created 0, updated 4
INFO:werkzeug:Running on all addresses

# Bad signs (report if you see these):
ModuleNotFoundError: No module named 'photovault.utils.app_storage'
AttributeError: 'AppStorageService' object has no attribute 'download_to_temp'
```

## Troubleshooting

### Still Getting "No module" Error
- Make sure Railway deployed the latest code
- Check the deployment logs for any build errors
- Verify the restart actually happened

### Still Getting 429 Error (Quota)
- Make sure you ran the SQL script from Step 1
- Check that your subscription plan has `ai_enhancement_quota > 0`
- Restart the Railway service again

### Getting Different Errors
- Check Railway logs for the full error message
- Let me know the exact error and I'll help debug

## Files Changed

- `photovault/routes/mobile_api.py` - Fixed 3 import statements
- `photovault/services/app_storage_service.py` - Added download_to_temp method
- `RAILWAY_IOS_AI_QUOTA_FIX.sql` - Database quota fix

## Success Indicators

✅ No "module not found" errors in Railway logs
✅ iOS app can use AI colorization without 500 errors
✅ AI quota tracking works correctly
✅ Users can enhance photos successfully
