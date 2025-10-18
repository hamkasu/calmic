# iOS Sharpen Feature - Railway Deployment Fix

## Problem
The iOS app shows "Failed to sharpen photo" with AxiosError 400 when trying to use the Sharpen feature on Railway production.

## Root Cause
The `/api/photos/<photo_id>/sharpen` endpoint exists on local Replit but hasn't been deployed to Railway yet.

## Endpoint Details
**Endpoint**: `POST /api/photos/<photo_id>/sharpen`  
**File**: `photovault/routes/mobile_api.py` (lines 2196-2307)  
**Authentication**: JWT Bearer token required

### Request Format
```json
{
  "intensity": 1.5,
  "radius": 2.0,
  "threshold": 3,
  "method": "unsharp"
}
```

### Response Format (Success)
```json
{
  "success": true,
  "message": "Photo sharpened successfully",
  "photo": {
    "id": 123,
    "filename": "original.jpg",
    "sharpened_filename": "hamka.sharpened.20251016.123456.jpg",
    "sharpened_url": "/uploads/1/hamka.sharpened.20251016.123456.jpg",
    "settings_applied": {
      "radius": 2.0,
      "amount": 1.5,
      "threshold": 3
    }
  }
}
```

## How to Deploy to Railway

### Step 1: Verify Local Code
The sharpen endpoint is already implemented in `photovault/routes/mobile_api.py`. Check the file:
```bash
grep -A 50 "def sharpen_photo_mobile" photovault/routes/mobile_api.py
```

### Step 2: Push to GitHub
```bash
# Check what will be committed
git status

# Add the mobile_api.py file if not already staged
git add photovault/routes/mobile_api.py

# Commit with a clear message
git commit -m "Add sharpen photo endpoint for iOS mobile app"

# Push to GitHub (Railway auto-deploys from main branch)
git push origin main
```

### Step 3: Verify Railway Deployment
1. Go to your Railway dashboard
2. Check the deployment logs for successful build
3. Wait for the deployment to complete (usually 2-3 minutes)

### Step 4: Test on iOS App
1. Open StoryKeep app on your iPhone
2. Select any photo from Gallery
3. Tap "Enhance Photo"
4. Try the "Sharpen" button
5. Should see success message: "Photo sharpened successfully!"

## Expected Behavior After Fix
✅ Sharpen button works without errors  
✅ Photo is sharpened with default intensity 1.5  
✅ Sharpened version is saved with new filename  
✅ Sharpened photo appears in Gallery

## Error Codes Explained
- **400 Bad Request**: Endpoint missing or file too large (>50MB)
- **404 Not Found**: Photo not found or access denied
- **500 Internal Error**: Processing failed (check Railway logs)

## Notes
- The endpoint supports both Railway volumes and object storage
- Maximum file size is 50MB (configurable in config.py)
- Sharpening uses unsharp mask algorithm by default
- Each sharpened photo gets a unique filename with timestamp and random number
