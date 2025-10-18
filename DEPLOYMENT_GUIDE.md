# Railway Deployment Guide - Mobile API Updates

## Overview
This deployment includes critical mobile API endpoints with JWT authentication that will fix the iOS app gallery issue where photos aren't loading.

## Files Modified for Mobile API

### 1. Core Mobile API Files (CRITICAL)
- **`photovault/routes/mobile_api.py`** - Mobile API endpoints
  - `/api/photos` - Get photos with JWT auth
  - `/api/upload` - Upload photos from mobile
  - `/api/dashboard` - Dashboard stats
  - `/api/auth/profile` - User profile
  - `/api/detect-and-extract` - Photo detection (Digitizer)
  - `/api/family/vaults` - Family vaults list
  - `/api/family/vault/<id>` - Vault details

- **`photovault/utils/jwt_auth.py`** - JWT authentication decorators
  - `@token_required` - JWT authentication for mobile
  - `@hybrid_auth` - Supports both session and JWT auth

- **`photovault/routes/gallery.py`** - Updated with hybrid auth
  - Modified `uploaded_file` route to support JWT tokens for image serving

### 2. Registration Endpoint Updates
- **`photovault/routes/auth.py`** - JSON support for mobile registration
  - Updated `/auth/register` to handle both web forms and mobile JSON requests
  - Returns proper JSON responses for mobile clients

### 3. App Initialization
- **`photovault/__init__.py`** - Blueprint registration
  - Registered `mobile_api_bp` blueprint

## What This Fixes

### Current Issue
- iOS app gallery shows "no images detected" 
- API returns HTML login page instead of JSON
- JWT authentication not working on Railway

### After Deployment
- iOS app will receive proper JSON photo data
- JWT authentication will work correctly
- Mobile uploads will function
- Image URLs will be accessible with JWT tokens

## Deployment Steps

### Option 1: GitHub Push (Recommended for Railway Auto-Deploy)
```bash
# 1. Stage all changes
git add photovault/routes/mobile_api.py
git add photovault/routes/auth.py
git add photovault/routes/gallery.py
git add photovault/utils/jwt_auth.py
git add photovault/__init__.py

# 2. Commit with descriptive message
git commit -m "Add mobile API with JWT authentication for iOS app

- Add /api/photos endpoint with JWT authentication
- Add /api/upload for mobile photo uploads
- Add /api/dashboard and /api/auth/profile endpoints
- Add JWT authentication decorators (@token_required, @hybrid_auth)
- Update /auth/register to support JSON requests from mobile
- Update uploaded_file route with hybrid auth for mobile image access
- Add /api/detect-and-extract for photo detection (Digitizer feature)
- Add Family Vaults mobile endpoints"

# 3. Push to GitHub
git push origin main
```

### Option 2: Railway CLI (If you have Railway CLI installed)
```bash
railway up
```

### Option 3: Manual File Upload to Railway
1. Go to Railway dashboard
2. Navigate to your project
3. Use Railway's file upload feature to update the modified files

## Verification After Deployment

### 1. Test Authentication Endpoint
```bash
# Test login (replace with your credentials)
curl -X POST https://web-production-535bd.up.railway.app/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"hamka@example.com","password":"password123"}'
```

### 2. Test Photos Endpoint (requires valid JWT token)
```bash
# Get photos (use token from login response)
curl -X GET https://web-production-535bd.up.railway.app/api/photos \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

### 3. Test from iOS App
1. Open StoryKeep app
2. Login with your credentials
3. Navigate to Gallery
4. You should see your 25 photos displayed

## Expected Railway Deployment Behavior

Railway will:
1. Detect the git push
2. Pull latest code
3. Install Python dependencies from `requirements.txt`
4. Run the build process
5. Deploy the new version
6. Route traffic to the new deployment

Deployment typically takes 2-5 minutes.

## Files Summary

**Critical Files for Mobile API:**
```
photovault/routes/mobile_api.py    (NEW - Mobile API endpoints)
photovault/utils/jwt_auth.py       (NEW - JWT authentication)
photovault/routes/auth.py          (MODIFIED - JSON support)
photovault/routes/gallery.py       (MODIFIED - Hybrid auth for images)
photovault/__init__.py             (MODIFIED - Blueprint registration)
```

**Supporting Files (already on Railway):**
```
requirements.txt                    (All dependencies)
photovault/models.py               (Database models)
photovault/extensions.py           (Flask extensions)
config.py                          (Configuration)
main.py                            (App factory)
```

## Important Notes

1. **JWT Secret Key**: Make sure Railway has the same `SECRET_KEY` environment variable as your local environment
2. **Database**: Railway uses a different PostgreSQL database than local Replit
3. **File Storage**: Railway may use different storage than Replit Object Storage
4. **Environment Variables**: Verify all required env vars are set in Railway dashboard

## Rollback Plan

If deployment fails:
1. Go to Railway dashboard
2. Navigate to Deployments tab
3. Click "Redeploy" on the previous working deployment

## Next Steps After Deployment

1. **Test iOS app** - Verify gallery loads photos
2. **Test photo upload** - Take a photo with camera and verify it uploads
3. **Test Digitizer** - Verify photo detection works
4. **Monitor logs** - Check Railway logs for any errors

## Questions?

If you encounter issues:
- Check Railway deployment logs
- Verify environment variables are set
- Test API endpoints directly with curl
- Check database connection in Railway logs
