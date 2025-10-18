# Railway Deployment Guide - View Button Fix

## Overview
This deployment fixes the 404 error that occurs when clicking "View" after colorizing or sharpening photos in the iOS app.

## What Was Fixed

### Problem
After successfully colorizing a photo, clicking the "View" button resulted in:
1. ❌ 404 error from `/api/photos/<photo_id>` endpoint
2. ❌ Error message "Failed to colorize photo"
3. ❌ User couldn't see the colorized result

### Solution
1. ✅ Updated iOS app to fetch refreshed photo data after enhancement
2. ✅ Created missing `/api/photos/<photo_id>` GET endpoint in backend
3. ✅ Endpoint returns updated photo with `edited_url` for colorized version

## Files Changed

### Backend Changes
**File**: `photovault/routes/mobile_api.py`
- Added new endpoint: `GET /api/photos/<int:photo_id>`
- Returns single photo details with JWT authentication
- Includes `original_url` and `edited_url` fields
- Security: Only returns photos owned by authenticated user

### iOS App Changes
**File**: `StoryKeep-iOS/src/screens/EnhancePhotoScreen.js`
- Updated `handleColorize()` to fetch photo after colorization
- Updated `handleSharpen()` to fetch photo after sharpening
- Navigation now uses updated photo object instead of `goBack()`

## Deployment Steps

### Step 1: Commit Changes to Git
```bash
git add photovault/routes/mobile_api.py
git add StoryKeep-iOS/src/screens/EnhancePhotoScreen.js
git commit -m "Fix: Add missing photo detail endpoint for View button after colorization"
```

### Step 2: Push to GitHub
```bash
git push origin main
```

### Step 3: Verify Railway Auto-Deployment
1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Select your project: `web-production-535bd`
3. Check the **Deployments** tab
4. Wait for deployment to complete (usually 2-3 minutes)
5. Look for green checkmark ✅ indicating successful deployment

### Step 4: Verify New Endpoint
Test the new endpoint is live:
```bash
# Get your JWT token from iOS app or login endpoint
TOKEN="your_jwt_token_here"

# Test the photo detail endpoint
curl -X GET https://web-production-535bd.up.railway.app/api/photos/123 \
  -H "Authorization: Bearer $TOKEN"

# Should return photo details with original_url and edited_url
```

### Step 5: Test iOS App
1. Open StoryKeep app on iOS device
2. Navigate to any black & white photo
3. Tap "Enhance Photo"
4. Choose "Colorize (DNN)" or "Colorize (AI)"
5. Wait for "Success" dialog
6. **Click "View" button**
7. ✅ Should now show the colorized photo instead of 404 error

## Expected Behavior After Deployment

### Before Fix
```
User clicks "Colorize (DNN)"
  ↓
Backend colorizes photo successfully
  ↓
iOS app shows "Success" dialog
  ↓
User clicks "View"
  ↓
❌ 404 error: /api/photos/123 not found
  ↓
❌ Shows "Failed to colorize photo" error
```

### After Fix
```
User clicks "Colorize (DNN)"
  ↓
Backend colorizes photo successfully
  ↓
iOS app shows "Success" dialog
  ↓
iOS fetches updated photo via /api/photos/123
  ↓
User clicks "View"
  ↓
✅ Navigates to PhotoDetail with updated photo
  ↓
✅ Shows colorized image!
```

## API Endpoint Details

### GET /api/photos/<photo_id>

**Authentication**: JWT Bearer token required

**Request**:
```http
GET /api/photos/123 HTTP/1.1
Host: web-production-535bd.up.railway.app
Authorization: Bearer <jwt_token>
```

**Response** (200 OK):
```json
{
  "id": 123,
  "filename": "user_photo_original.jpg",
  "original_url": "/uploads/5/user_photo_original.jpg",
  "url": "/uploads/5/user_photo_original.jpg",
  "thumbnail_url": "/uploads/5/user_photo_original.jpg",
  "edited_url": "/uploads/5/user_photo_colorized.jpg",
  "has_edited": true,
  "created_at": "2025-10-12T17:00:00",
  "file_size": 2048576,
  "enhancement_metadata": {
    "colorization": {
      "method": "dnn",
      "timestamp": "2025-10-12T17:30:00"
    }
  },
  "processing_notes": null,
  "back_text": null,
  "date_text": null,
  "location_text": null,
  "occasion": null,
  "photo_date": null,
  "condition": null,
  "photo_source": null,
  "needs_restoration": false,
  "auto_enhanced": false
}
```

**Response** (404 Not Found):
```json
{
  "error": "Photo not found"
}
```

**Security Features**:
- JWT authentication required
- User can only access their own photos
- SQL injection prevention via parameterized queries
- CSRF protection via @token_required decorator

## Troubleshooting

### Issue: Still getting 404 error after deployment

**Check**:
1. Verify deployment succeeded on Railway dashboard
2. Check Railway logs for errors:
   ```bash
   railway logs
   ```
3. Confirm endpoint exists by testing with curl
4. Verify JWT token is valid and not expired

### Issue: "Photo not found" error

**Possible Causes**:
1. Photo doesn't exist in database
2. Photo belongs to different user
3. Photo ID is invalid

**Solution**:
- Check photo exists: `SELECT * FROM photos WHERE id = 123;`
- Verify user_id matches current user

### Issue: edited_url is null

**Possible Causes**:
1. Colorization didn't complete successfully
2. Photo hasn't been enhanced yet

**Solution**:
- Check if `edited_filename` exists in database
- Verify colorization endpoint completed without errors

## Rollback Plan

If deployment causes issues:

1. **Revert Git Commit**:
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Railway Will Auto-Deploy Previous Version**

3. **Alternative**: Manually rollback in Railway dashboard:
   - Go to Deployments tab
   - Find previous working deployment
   - Click "Redeploy"

## Testing Checklist

After deployment, verify:

- [ ] Login to iOS app works
- [ ] Photo gallery loads
- [ ] Colorize (DNN) works
- [ ] Colorize (AI) works
- [ ] Sharpen works
- [ ] "View" button shows colorized photo (not 404)
- [ ] Original photo still accessible
- [ ] Enhanced photo displays correctly
- [ ] No errors in Railway logs

## Success Metrics

After successful deployment:
- ✅ Zero 404 errors on `/api/photos/<photo_id>` endpoint
- ✅ "View" button navigation works 100% of the time
- ✅ Users can see colorized photos immediately
- ✅ No "Failed to colorize photo" errors

## Notes

- **Local Testing**: Changes are already applied to local Replit server
- **Production**: Requires Railway deployment via GitHub push
- **iOS App**: Works with both local and production servers (BASE_URL in api.js)
- **Backward Compatible**: Existing functionality unchanged, only adds new endpoint

## Support

If you encounter issues:
1. Check Railway deployment logs
2. Review iOS app console logs (Expo)
3. Test endpoint with curl/Postman
4. Verify JWT token is valid

---

**Last Updated**: October 12, 2025
**Version**: 1.0
**Status**: Ready for Deployment
