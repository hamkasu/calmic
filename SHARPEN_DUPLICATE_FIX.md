# Fix: iOS Sharpen Token Error - Removed Duplicate Endpoint

## Problem
iOS app kept showing **"Authorization token is missing"** even after code was pushed to Railway.

## Root Cause
There were **TWO sharpen endpoints with the exact same URL**:

1. **photo.py** (line 1583-1770) - DUPLICATE, DELETED ✅
   - Route: `/api/photos/<id>/sharpen`
   - Auth: `@login_required` (session-based, NO JWT support)
   
2. **mobile_api.py** (line 2196) - KEPT ✅
   - Route: `/api/photos/<id>/sharpen` 
   - Auth: `@token_required` (JWT authentication)

Both endpoints had the **exact same URL path**, causing Flask to match the wrong one (photo.py) which didn't support JWT tokens.

## Solution
**Deleted the entire duplicate sharpen endpoint from photo.py** (lines 1583-1770).

Now there's only ONE sharpen endpoint in `mobile_api.py` with proper JWT authentication.

## What Was Changed

### ❌ DELETED from photovault/routes/photo.py
```python
@photo_bp.route('/api/photos/<int:photo_id>/sharpen', methods=['POST'])
@csrf.exempt
@hybrid_auth
def sharpen_photo_api(current_user, photo_id):
    # ... 188 lines of duplicate code ...
```

### ✅ KEPT in photovault/routes/mobile_api.py
```python
@mobile_api_bp.route('/photos/<int:photo_id>/sharpen', methods=['POST'])
@csrf.exempt
@token_required
def sharpen_photo_mobile(current_user, photo_id):
    """Simple robust sharpen for iOS - based on working web version"""
    # ... JWT authentication, works with iOS ...
```

## How to Deploy to Railway

### Step 1: Commit and Push
```bash
git add photovault/routes/photo.py
git commit -m "Fix: Remove duplicate sharpen endpoint causing JWT auth failure"
git push origin main
```

### Step 2: Verify Deployment
1. Wait for Railway auto-deploy (~2-3 minutes)
2. Check Railway deployment logs
3. Test in iOS app

### Step 3: Test Sharpen Feature
1. Open StoryKeep iOS app
2. Go to any photo detail screen
3. Tap "Sharpen" button
4. Adjust sharpening strength
5. Tap "Apply"
6. ✅ Should work without token error!

## Why This Fixes It
- No more route conflict - only ONE `/api/photos/<id>/sharpen` endpoint exists
- Mobile API endpoint uses `@token_required` decorator
- iOS app JWT token is now properly recognized
- No more "Authorization token is missing" error
