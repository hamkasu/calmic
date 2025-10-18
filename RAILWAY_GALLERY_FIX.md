# Fix iOS Gallery on Railway - Deployment Guide

## Problem Identified ✅
- **Local Replit Server**: Has fixed SQLAlchemy 2.0 pagination code (working ✅)
- **Railway Production**: Still has OLD code with deprecated `.paginate()` method (broken ❌)
- **iOS App**: Points to Railway at `https://web-production-535bd.up.railway.app`

The dashboard shows 46 photos because it uses `.count()` and `.all()`.
The gallery shows 0 photos because Railway has the old `.paginate()` code that fails silently.

## Files That Need to be Deployed

The following files contain the fixes:

1. **`photovault/routes/mobile_api.py`** - Fixed pagination (lines 199-280)
   - Changed from `.paginate()` to manual pagination with `.limit()` and `.offset()`
   - This is the CRITICAL file that fixes the gallery

2. **`photovault/utils/jwt_auth.py`** - JWT authentication decorators
3. **`photovault/routes/gallery.py`** - Hybrid auth for image serving
4. **`photovault/routes/auth.py`** - JSON support for mobile registration
5. **`photovault/__init__.py`** - Blueprint registration

## Deployment Steps

### Step 1: Commit Changes
```bash
# Add the critical mobile API file
git add photovault/routes/mobile_api.py
git add photovault/utils/jwt_auth.py
git add photovault/routes/gallery.py
git add photovault/routes/auth.py
git add photovault/__init__.py

# Commit with descriptive message
git commit -m "Fix iOS gallery with SQLAlchemy 2.0 pagination

- Replace deprecated .paginate() with manual pagination (.limit() + .offset())
- Fix /api/photos endpoint to return photos correctly
- Add input validation to prevent negative offsets
- Update JWT authentication for mobile image access"
```

### Step 2: Push to GitHub
```bash
git push origin main
```

### Step 3: Verify Railway Deployment
1. Go to your Railway dashboard
2. Check the deployment logs to ensure it deploys successfully
3. Look for "Build successful" and "Deployment live"

### Step 4: Test iOS App
1. Force close the StoryKeep app on your iPhone
2. Reopen the app
3. Login with your credentials (username: hamka)
4. Navigate to Gallery
5. You should now see all 46 photos

## What Changed in the Code

### Before (Broken on Railway with SQLAlchemy 2.0):
```python
# This fails silently in SQLAlchemy 2.0
pagination = query.paginate(page=page, per_page=per_page)
photos = pagination.items
total = pagination.total
```

### After (Fixed - Works with SQLAlchemy 2.0):
```python
# Manual pagination that works in SQLAlchemy 2.0
total = query.count()
offset = (page - 1) * per_page
photos = query.limit(per_page).offset(offset).all()
has_more = (offset + len(photos)) < total
```

## Verification Commands

After deployment, test the API directly:
```bash
# Test with your actual JWT token (get from iOS app or login)
curl "https://web-production-535bd.up.railway.app/api/photos?filter=all" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

Expected response:
```json
{
  "success": true,
  "photos": [...array of 46 photos...],
  "page": 1,
  "per_page": 20,
  "total": 46,
  "has_more": true
}
```

## Troubleshooting

If gallery still shows 0 photos after deployment:

1. **Check Railway logs** for any errors during deployment
2. **Verify the commit** was pushed successfully to GitHub
3. **Check Railway environment** is using SQLAlchemy 2.0+ (should be in requirements.txt)
4. **Clear iOS app cache**: Delete and reinstall the app
5. **Check authentication**: Make sure you're logged in with the correct account

## Summary

The code is already fixed locally on Replit. You just need to:
1. ✅ Commit the fixed files
2. ✅ Push to GitHub  
3. ✅ Railway will auto-deploy
4. ✅ iOS gallery will work!

Your photos ARE in the database (46 photos confirmed). Railway just needs the updated code to return them properly.
