# Railway Bulk Delete Fix - Deployment Guide

## Issue
The iOS app shows "Failed to delete photos" error when trying to delete multiple photos on Railway production.

**Error Details:**
- Error message: "Failed to delete photos"
- Console: "Bulk delete error: AxiosError: Request failed with status code 400"
- HTTP Status: 400 Bad Request (not 404)

## Root Cause - ROUTE CONFLICT ✅ FIXED
The issue was a **route conflict** between two endpoints at the same path:

1. **Web endpoint** (`photo.py`): `/api/photos/bulk-delete` 
   - Uses `@login_required` (session cookies)
   - For web browser users

2. **Mobile endpoint** (`mobile_api.py`): `/api/photos/bulk-delete`
   - Uses `@token_required` (JWT tokens)  
   - For mobile app users

**What happened:**
- The web endpoint was registered first
- It caught ALL requests to `/api/photos/bulk-delete`
- When mobile app sent JWT token, web endpoint expected session cookie
- Result: **400 Bad Request**

**The Fix:**
- Changed mobile endpoint to unique path: `/api/photos/bulk-delete-mobile`
- Updated iOS app to use new endpoint
- No more route conflict ✅

## Solution - Deploy to Railway

### Step 1: Verify Local Changes
The bulk delete endpoint has been FIXED in:
- **Backend File**: `photovault/routes/mobile_api.py`
  - **Old Route**: `POST /api/photos/bulk-delete` (conflicted with web)
  - **New Route**: `POST /api/photos/bulk-delete-mobile` ✅
  - **Lines**: 2212-2325

- **iOS App File**: `StoryKeep-iOS/src/services/api.js`
  - **Updated endpoint**: `/api/photos/bulk-delete-mobile` ✅

### Step 2: Commit and Push to GitHub

```bash
# Stage the changes
git add photovault/routes/mobile_api.py StoryKeep-iOS/src/services/api.js

# Commit with descriptive message
git commit -m "Fix bulk delete route conflict - use /api/photos/bulk-delete-mobile for iOS app"

# Push to GitHub (Railway will auto-deploy)
git push origin main
```

### Step 3: Wait for Railway Deployment
- Railway will automatically detect the GitHub push
- Wait 2-3 minutes for deployment to complete
- Check Railway dashboard for deployment status

### Step 4: Verify on iOS App
1. Open the iOS app (connected to Railway)
2. Go to Gallery
3. Long-press a photo to enter selection mode
4. Select multiple photos (2-3 photos)
5. Tap the 🗑️ (trash) icon
6. Confirm deletion
7. **Expected**: Success message "Deleted X photos"
8. **Previously**: Error "Failed to delete photos"

## Endpoint Details

### New Mobile Endpoint (Fixed)
```http
POST /api/photos/bulk-delete-mobile
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json

{
  "photo_ids": [123, 456, 789]
}
```

### Old Web Endpoint (Conflicted)
```http
POST /api/photos/bulk-delete
Cookie: session={SESSION_COOKIE}
Content-Type: application/json

{
  "photo_ids": [123, 456, 789]
}
```
*Note: This endpoint is for web users only*

### Response Format (Success)
```json
{
  "success": true,
  "message": "Deleted 3 photos",
  "deleted_count": 3,
  "failed_count": 0,
  "errors": null
}
```

### Response Format (Error)
```json
{
  "success": false,
  "error": "Bulk delete failed: {reason}"
}
```

## Features of the Endpoint
✅ Deletes multiple photos in one request  
✅ Removes all associated files (original, thumbnail, edited versions)  
✅ Cleans up voice memos, vault associations, tags, and comments  
✅ Tracks success/failure counts  
✅ Provides detailed error reporting  
✅ Verifies user ownership before deletion  
✅ Uses JWT authentication  
✅ CSRF exempt for mobile API  

## Testing Checklist
- [ ] Single photo deletion still works
- [ ] Multiple photo selection (2-5 photos)
- [ ] Bulk deletion success message shows correct count
- [ ] Deleted photos disappear from gallery
- [ ] No orphaned files left in storage
- [ ] Voice memos are cleaned up
- [ ] Vault associations are removed

## Rollback Plan
If issues occur after deployment:
1. Revert the commit: `git revert HEAD`
2. Push to GitHub: `git push origin main`
3. Railway will auto-deploy the rollback
4. Report the issue for investigation

## Summary

### What Was Wrong
- Route conflict: Both web and mobile used `/api/photos/bulk-delete`
- Web endpoint (session auth) was registered first
- Mobile app JWT requests hit web endpoint → 400 error

### What Was Fixed
- Mobile endpoint renamed to `/api/photos/bulk-delete-mobile`
- iOS app updated to use new endpoint
- Both endpoints now work independently ✅

## Status
✅ **FIXED LOCALLY** - Route conflict resolved, unique endpoints for web and mobile  
⚠️ **ACTION REQUIRED** - Push changes to GitHub for Railway deployment

```bash
git add photovault/routes/mobile_api.py StoryKeep-iOS/src/services/api.js
git commit -m "Fix bulk delete route conflict - use /api/photos/bulk-delete-mobile for iOS app"
git push origin main
```
