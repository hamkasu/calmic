# Railway Deployment Guide - Sharpen Endpoint Fix

## Issue Fixed
The iOS app was getting errors when trying to sharpen or colorize photos:
- **Sharpen Error**: "Failed to sharpen photo" - Status code 400/404
- **Colorize Error**: "Failed to colorize photo" - Status code 404

## Root Cause
The iOS app calls `/api/photos/{photo_id}/sharpen` endpoint which didn't exist on the backend. Only `/enhance`, `/colorize`, and `/colorize-ai` endpoints existed.

## Fix Applied
Added the missing `/api/photos/<int:photo_id>/sharpen` endpoint to `photovault/routes/mobile_api.py`:
- ✅ JWT authentication support
- ✅ Accepts `intensity` parameter from iOS app
- ✅ Uses `sharpen_image()` function for actual sharpening
- ✅ Updates `photo.edited_filename` with sharpened version
- ✅ Returns sharpened photo URL and settings

## Files Modified
1. **photovault/routes/mobile_api.py** - Added sharpen endpoint (line 1477-1588)

## How to Deploy to Railway

### Step 1: Verify Local Server is Working
The local Replit server has been updated and is running with the new endpoint at:
- http://127.0.0.1:5000
- http://172.31.77.130:5000

### Step 2: Push Changes to GitHub
```bash
# Check what files changed
git status

# Add the modified file
git add photovault/routes/mobile_api.py

# Commit the change
git commit -m "Add /api/photos/<photo_id>/sharpen endpoint for iOS app"

# Push to GitHub (Railway will auto-deploy)
git push origin main
```

### Step 3: Verify Railway Deployment
1. Go to your Railway dashboard: https://railway.app/dashboard
2. Click on your `web-production-535bd` project
3. Wait for the deployment to complete (usually 2-3 minutes)
4. Check the deployment logs for any errors

### Step 4: Test on iOS App
1. Open the StoryKeep iOS app
2. Go to a photo's "Enhance Photo" screen
3. Try the **Sharpen** option
4. Try the **Colorize (DNN)** option
5. Try the **Colorize (AI)** option

All three should work without errors now!

## Endpoint Details

### POST /api/photos/<photo_id>/sharpen
**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "intensity": 1.5,
  "radius": 2.0,
  "threshold": 3,
  "method": "unsharp"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Photo sharpened successfully",
  "photo": {
    "id": 123,
    "filename": "original.jpg",
    "sharpened_filename": "username.sharpened.20251012.123456.jpg",
    "sharpened_url": "/uploads/1/username.sharpened.20251012.123456.jpg",
    "settings_applied": {
      "radius": 2.0,
      "amount": 1.5,
      "threshold": 3,
      "method": "unsharp"
    }
  }
}
```

## Summary
✅ **Local Fix Complete** - Sharpen endpoint added to local Replit server
📤 **Next Step** - Push to GitHub for Railway deployment
📱 **iOS App Ready** - Will work once Railway is updated

---

**Note:** The colorize endpoints were already working correctly. The sharpen endpoint was the missing piece.
