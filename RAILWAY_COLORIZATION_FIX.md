# Railway Deployment Guide - iOS Colorization Fix

## Issue Fixed
The iOS app colorization feature was not working because only the basic DNN colorization method was connected. The Railway app has **2 colorization algorithms** but the mobile app only had access to one.

## Changes Made

### 1. Mobile API - New AI Colorization Endpoint
**File: `photovault/routes/mobile_api.py`**

Added new endpoint `/api/photos/<photo_id>/colorize-ai` that:
- Uses JWT authentication with `@token_required` decorator
- Calls Google Gemini AI for intelligent color suggestions
- Uses DNN colorization with AI-guided color analysis
- Returns colorized image with AI guidance metadata
- Handles App Storage upload for persistence

### 2. iOS App - API Service Update
**File: `StoryKeep-iOS/src/services/api.js`**

Added new API methods:
- `colorizePhoto(photoId, method)` - DNN-based colorization (auto/dnn/basic)
- `colorizePhotoAI(photoId)` - AI-powered colorization with Gemini

### 3. iOS App - UI Enhancement
**File: `StoryKeep-iOS/src/screens/EnhancePhotoScreen.js`**

Updated UI to show **two colorization options**:
- **Colorize (DNN)** - Fast, DNN-based algorithm (green icon)
- **Colorize (AI)** - AI-powered with Gemini analysis (purple sparkles icon)

## Deployment Steps

### Step 1: Commit Changes to Git
```bash
git add photovault/routes/mobile_api.py
git add StoryKeep-iOS/src/services/api.js
git add StoryKeep-iOS/src/screens/EnhancePhotoScreen.js
git commit -m "Add AI colorization support to iOS mobile app

- Added /api/photos/{id}/colorize-ai endpoint with JWT auth
- Updated iOS app to support both DNN and AI colorization
- Added two colorization options in EnhancePhotoScreen UI
- Fixed issue where only basic DNN method was available"
```

### Step 2: Push to GitHub
```bash
git push origin main
```

### Step 3: Railway Auto-Deploy
Railway will automatically:
1. Detect the push to main branch
2. Build the new version with AI colorization endpoint
3. Deploy the updated server

**Monitor deployment in Railway dashboard:**
- Check build logs for errors
- Verify deployment completes successfully
- Test the new endpoints

### Step 4: Verify on Production
After Railway deployment completes:

1. **Test DNN Colorization:**
   - Open StoryKeep iOS app
   - Select a black & white photo
   - Tap "Enhance Photo"
   - Tap "Colorize (DNN)"
   - Verify photo is colorized

2. **Test AI Colorization:**
   - Select same photo
   - Tap "Enhance Photo"
   - Tap "Colorize (AI)"
   - Verify photo is colorized with AI analysis

## Environment Requirements

### Railway Environment Variables (Already Set)
- `GEMINI_API_KEY` - Required for AI colorization (should already be configured)

If AI colorization returns "AI service not available", verify:
```bash
# In Railway dashboard, check environment variable:
GEMINI_API_KEY=your-gemini-api-key-here
```

## Testing on Local Server

Both workflows are currently running on Replit:
- **PhotoVault Server**: Running on port 5000 with new endpoint
- **Expo Server**: Running with updated iOS app

To test locally before Railway deployment:
1. Update `BASE_URL` in `StoryKeep-iOS/src/services/api.js` to Replit URL
2. Test both colorization options
3. Revert `BASE_URL` back to Railway production URL
4. Deploy to Railway

## API Endpoint Summary

### DNN Colorization (Basic)
```
POST /api/photos/{photo_id}/colorize
Authorization: Bearer <jwt_token>
Body: { "method": "auto" | "dnn" | "basic" }

Response:
{
  "success": true,
  "message": "Photo colorized successfully",
  "photo": {
    "id": 123,
    "colorized_url": "/uploads/1/filename.jpg",
    "method_used": "dnn"
  }
}
```

### AI Colorization (Gemini)
```
POST /api/photos/{photo_id}/colorize-ai
Authorization: Bearer <jwt_token>

Response:
{
  "success": true,
  "message": "Photo colorized successfully using AI",
  "photo": {
    "id": 123,
    "colorized_url": "/uploads/1/filename.jpg",
    "method_used": "ai_guided_dnn",
    "ai_guidance": "The photo appears to show..."
  }
}
```

## Troubleshooting

### Issue: 404 Error on /colorize-ai
**Cause:** Changes not deployed to Railway
**Fix:** Complete deployment steps above

### Issue: 503 AI Service Not Available
**Cause:** GEMINI_API_KEY not configured
**Fix:** Add GEMINI_API_KEY to Railway environment variables

### Issue: Images Not Loading After Colorization
**Cause:** JWT auth missing on image requests
**Fix:** Already handled in iOS app - images include Bearer token

## Summary

✅ **Both colorization algorithms now available in iOS app:**
1. DNN-based colorization (fast, traditional)
2. AI-powered colorization (Gemini, intelligent)

✅ **User can choose colorization method:**
- Tap "Colorize (DNN)" for quick results
- Tap "Colorize (AI)" for AI-analyzed colors

✅ **All endpoints use JWT authentication for security**

## Questions?
Check Railway deployment logs if colorization fails after deployment.
