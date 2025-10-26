# Railway Deployment Guide - CSRF Fix for iOS Upload

## Problem
iOS app shows CSRF error when uploading photos from camera roll to vaults:
```
ERROR: Upload failed: 400 <!doctype html>
The CSRF token is missing.
ERROR: Camera library upload error: [Error: Upload failed: 400]
```

## Root Cause
The entire `mobile_api` blueprint was not exempt from CSRF protection. Even though individual routes had `@csrf.exempt` decorators, Flask-WTF's blueprint-level CSRF checking was still enabled, causing it to block requests on Railway's production HTTPS environment with `WTF_CSRF_SSL_STRICT=True`.

## Solution
Added blueprint-level CSRF exemption in `photovault/__init__.py`:
```python
# Exempt entire mobile API blueprint from CSRF protection (uses JWT auth instead)
csrf.exempt(mobile_api_bp)
# Register mobile_api_bp BEFORE photo_bp
app.register_blueprint(mobile_api_bp)
```

This ensures **all** mobile API routes bypass CSRF checks, relying on JWT token authentication for security instead.

## Files Changed
1. `photovault/__init__.py` - Added `csrf.exempt(mobile_api_bp)` before blueprint registration
2. `photovault/routes/mobile_api.py` - Added `@csrf.exempt` to remaining GET endpoints (belt & suspenders)

## Why This Works
- **Mobile apps cannot use CSRF tokens** (no cookie/session support)
- **JWT authentication** provides equivalent security for mobile requests
- **Web routes remain protected** - only `/api/*` endpoints are exempt
- **Blueprint-level exemption** takes precedence over SSL-strict settings in production

## Deployment Steps

### Step 1: Commit Changes to Git
```bash
# Check what files changed
git status

# Review changes
git diff photovault/__init__.py photovault/routes/mobile_api.py

# Stage changes
git add photovault/__init__.py photovault/routes/mobile_api.py

# Commit with clear message
git commit -m "Fix CSRF error for iOS mobile API by exempting entire blueprint

- Added csrf.exempt(mobile_api_bp) before blueprint registration
- Fixes 'CSRF token is missing' error on Railway production
- Mobile API uses JWT auth instead of CSRF tokens
- Web routes remain CSRF protected"
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
   - Tap "Upload from Camera Roll"
   - Select a photo
   - Upload should succeed without CSRF error ✅

2. **Check Server Logs** (if issues persist)
   - In Railway dashboard → Deployments → View Logs
   - Look for any error messages during upload attempt

## Expected Results

### Before Fix
```
ERROR: Upload failed: 400 <!doctype html>
<h1>Bad Request</h1>
<p>The CSRF token is missing.</p>
ERROR: Camera library upload error: [Error: Upload failed: 400]
```

### After Fix
```
LOG: Upload response: {"success": true, "photo": {"id": 123, ...}}
LOG: ✅ Adding photo 123 to vault...
LOG: ✅ Successfully shared to vault
```

## Troubleshooting

### If deployment fails:
1. Check Railway logs for error messages
2. Verify requirements.txt includes all dependencies
3. Ensure environment variables are set in Railway dashboard

### If CSRF error persists after deployment:
1. **Verify deployment actually completed** - Check Railway shows "Success" status
2. **Hard refresh** - Force Railway to redeploy from Settings tab
3. **Check git commit** - Ensure changes were pushed to GitHub and Railway pulled them
4. **Verify Railway branch** - Ensure Railway is deploying from the correct branch
5. **Clear app cache** - Delete and reinstall iOS app if necessary

### If you see different errors:
1. **401 Unauthorized** - JWT token issue, user needs to re-login
2. **404 Not Found** - Check API endpoint URLs match between iOS and server
3. **500 Server Error** - Check Railway deployment logs for backend errors

## Technical Details

### Why Individual Route Decorators Weren't Enough
Even with `@csrf.exempt` on each route, Flask-WTF's CSRF protection runs **before** route handlers when:
- `WTF_CSRF_SSL_STRICT=True` (enabled in production with HTTPS)
- Request is to a registered blueprint
- Blueprint is not in the exempt list

The solution requires **both**:
1. Blueprint-level exemption: `csrf.exempt(mobile_api_bp)`
2. Proper ordering: exempt BEFORE register_blueprint()

### Security Considerations
This change is secure because:
- **JWT tokens** authenticate every mobile request
- **Only `/api/*` routes** are exempt (mobile API blueprint only)
- **Web routes** (`/auth/login`, `/gallery/*`, etc.) remain CSRF protected
- **Separate blueprints** isolate mobile and web security models

### Files and Line Numbers
- `photovault/__init__.py:267` - `csrf.exempt(mobile_api_bp)`
- `photovault/routes/mobile_api.py` - All routes use `@token_required` for JWT auth

## Related Documentation
- Flask-WTF CSRF: https://flask-wtf.readthedocs.io/en/stable/csrf.html
- JWT Authentication: `photovault/utils/jwt_auth.py`
- Mobile API Routes: `photovault/routes/mobile_api.py`

## Next Steps After Deployment
1. ✅ Test all iOS app features (upload, gallery, vaults, camera)
2. ✅ Verify web app still works (CSRF protection intact)
3. ✅ Monitor Railway logs for any unusual activity
4. ✅ Update iOS app version if needed

---

**Created:** October 26, 2025  
**Issue:** CSRF token missing error on iOS vault uploads  
**Root Cause:** Blueprint not exempt from CSRF despite route decorators  
**Fix:** Added `csrf.exempt(mobile_api_bp)` before blueprint registration  
**Deployment:** Automatic via Railway GitHub integration
