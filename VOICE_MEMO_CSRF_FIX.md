# Voice Memo CSRF Fix - Railway Deployment Guide

## Problem Identified
The iOS app was getting "Failed to save voice note" with error 400 because the voice memo upload endpoints were missing CSRF exemption. Mobile apps don't have CSRF tokens, so they were being rejected by Flask's CSRF protection.

## What Was Fixed
Added `@csrf.exempt` decorator to all three voice memo endpoints in `photovault/routes/mobile_api.py`:

1. **POST /api/photos/<photo_id>/voice-memos** - Upload voice memo
2. **DELETE /api/voice-memos/<memo_id>** - Delete voice memo  
3. **GET /api/voice-memos/<memo_id>/audio** - Download voice memo audio

These endpoints now bypass CSRF validation and rely solely on JWT authentication (which is secure for mobile APIs).

## Files Changed
- `photovault/routes/mobile_api.py` - Added `@csrf.exempt` to lines 1239, 1347, and 1384

## How to Deploy to Railway

### Step 1: Commit and Push Changes
```bash
git add photovault/routes/mobile_api.py
git commit -m "Fix voice memo upload - add CSRF exemption for mobile endpoints"
git push origin main
```

### Step 2: Verify Railway Auto-Deploy
Railway will automatically detect and deploy your changes. Wait 2-3 minutes for deployment to complete.

### Step 3: Test in iOS App
1. Open StoryKeep app on your phone
2. Go to any photo detail screen
3. Tap the Record button under Voice Notes
4. Record a voice memo
5. The upload should now succeed! ✅

## Expected Result
- Voice memo uploads will work without the 400 error
- The error message "Failed to save voice note" will no longer appear
- Voice memos will be saved and playable in the app

## Technical Details
**Root Cause:** Flask-WTF CSRF protection was rejecting multipart/form-data requests from the mobile app because they didn't include a CSRF token.

**Solution:** Added `@csrf.exempt` to mobile API endpoints that handle file uploads. These endpoints are already secured with JWT token authentication, so CSRF protection is redundant and was causing the issue.

**Security Note:** This is safe because:
- All endpoints still require valid JWT tokens in the Authorization header
- CSRF protection is meant for web browsers with cookies, not for mobile apps with token-based auth
- The `@token_required` decorator verifies the user identity on every request
