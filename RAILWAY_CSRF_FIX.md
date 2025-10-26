# Railway Deployment Guide - CSRF Fix for iOS Upload

## Problem
iOS app shows CSRF error when uploading photos to family vaults:
```
ERROR: Upload failed: 400 <!doctype html>
The CSRF token is missing.
ERROR: Camera library upload error: [Error: Upload failed: 400]
```

## Solution
All mobile API endpoints now have `@csrf.exempt` decorator to allow JWT-authenticated requests from the iOS app without CSRF tokens.

## Files Changed
- `photovault/routes/mobile_api.py` - Added `@csrf.exempt` to 5 GET endpoints

## Deployment Steps

### Step 1: Commit Changes to Git
```bash
# Check what files changed
git status

# Review changes
git diff photovault/routes/mobile_api.py

# Stage changes
git add photovault/routes/mobile_api.py

# Commit with clear message
git commit -m "Fix CSRF error for iOS mobile API endpoints

- Added @csrf.exempt to all mobile GET endpoints
- Fixes 'CSRF token is missing' error when uploading to vaults
- Affected endpoints: /dashboard, /auth/profile, /photos, /photos/<id>, /family/vault/<id>
- All mobile endpoints now properly exempt from CSRF protection"
```

### Step 2: Push to GitHub
```bash
# Push to your main branch (adjust branch name if needed)
git push origin main
```

### Step 3: Railway Auto-Deploy
Railway is configured to automatically deploy when you push to GitHub. After pushing:

1. **Open Railway Dashboard**
   - Go to https://railway.app
   - Select your StoryKeep project

2. **Monitor Deployment**
   - Click on the "web" service
   - Go to "Deployments" tab
   - Watch for new deployment to start (usually within 30 seconds)
   - Wait for status to change from "Building" → "Deploying" → "Success"

3. **Check Deployment Logs**
   - Click on the active deployment
   - View logs to ensure no errors
   - Look for "Starting PhotoVault development server" message

### Step 4: Verify Fix on Railway
After deployment completes:

1. **Test iOS App**
   - Open StoryKeep app on your iOS device
   - Go to a Family Vault
   - Try uploading a photo from camera roll
   - Should now work without CSRF error ✅

2. **Check Server Logs** (if issues persist)
   - In Railway dashboard → Deployments → View Logs
   - Look for any error messages during upload attempt

## Expected Results

### Before Fix
```
ERROR: Upload failed: 400 <!doctype html>
<p>The CSRF token is missing.</p>
ERROR: Camera library upload error: [Error: Upload failed: 400]
```

### After Fix
```
LOG: ✅ Bulk share success: {"success":true,"added":1,"failed":0}
LOG: ✅ Successfully shared to vault
```

## Troubleshooting

### If deployment fails:
1. Check Railway logs for error messages
2. Verify requirements.txt includes all dependencies
3. Ensure environment variables are set in Railway dashboard

### If CSRF error persists after deployment:
1. Hard refresh the Railway deployment (Redeploy from Settings)
2. Check that git commit was successfully pushed to GitHub
3. Verify Railway is connected to correct GitHub repository and branch
4. Clear iOS app cache: delete app and reinstall, or clear data

### If you need to test locally first:
```bash
# Restart local server
# (PhotoVault Server workflow will auto-restart)

# Test with iOS app pointing to local Replit URL
# Update BASE_URL in StoryKeep-iOS/src/services/api.js temporarily
```

## Important Notes

- **All mobile API endpoints** now have `@csrf.exempt` - this is intentional and secure because:
  - JWT token authentication provides security
  - Mobile apps cannot use traditional CSRF protection (no cookies/sessions)
  - Web routes still have full CSRF protection
  
- **Railway deployment is automatic** - just push to GitHub and wait

- **No database migration needed** for this fix - it's code-only

## Technical Details

### Endpoints Fixed
Added `@csrf.exempt` to these GET endpoints:
1. `/api/dashboard` - Get dashboard statistics
2. `/api/auth/profile` - Get user profile
3. `/api/photos` - Get photo gallery
4. `/api/photos/<int:photo_id>` - Get single photo detail
5. `/api/family/vault/<int:vault_id>` - Get vault detail

### Why This Fix Works
- **POST endpoints** already had `@csrf.exempt` (including `/add-photos-bulk`)
- **GET endpoints** were missing it, causing issues with JWT auth flow
- Flask CSRF protection expects session cookies, which mobile apps don't use
- JWT tokens provide equivalent security for mobile requests

## Related Files
- `photovault/routes/mobile_api.py` - Mobile API endpoints (JWT auth + CSRF exempt)
- `photovault/routes/gallery.py` - Web routes (session auth + CSRF protected)
- `photovault/utils/jwt_auth.py` - JWT token validation

## Next Steps After Deployment
1. Test all iOS app features to ensure nothing broke
2. Verify web app still works (CSRF protection intact for web routes)
3. Monitor Railway logs for any unusual activity
4. Update app version in iOS if needed

---

**Created:** October 26, 2025  
**Issue:** CSRF token missing error on iOS vault uploads  
**Fix:** Added @csrf.exempt to all mobile API GET endpoints  
**Deployment:** Automatic via Railway GitHub integration
