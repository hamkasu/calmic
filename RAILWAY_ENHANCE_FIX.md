# Fix iOS Auto Enhance 400 Error on Railway

## Problem
The iOS app Auto Enhance feature returns a **400 Bad Request** error on Railway production, but works fine locally on Replit.

## Root Cause
The mobile enhancement endpoint `/api/photos/<photo_id>/enhance` with JWT authentication exists in your **local Replit code** but hasn't been **deployed to Railway** yet. Railway is still running the old code without this mobile API endpoint.

## What's Fixed
Added enhanced logging to the mobile enhancement endpoint in `photovault/routes/mobile_api.py`:
- ✨ Request logging (photo ID, user)
- 📸 Photo details (filename, path)
- 📂 File path verification
- 📏 File size checking
- ⚙️ Enhancement settings
- 🔧 Processing status
- ✅ Success confirmation
- 💥 Error details with full traceback

## How to Deploy to Railway

### Step 1: Commit Your Changes to Git

```bash
# 1. Check what files have changed
git status

# 2. Stage the mobile API changes
git add photovault/routes/mobile_api.py

# 3. Commit with a clear message
git commit -m "Add enhanced logging to mobile photo enhancement endpoint"

# 4. Push to your GitHub repository
git push origin main
```

### Step 2: Railway Auto-Deployment

Railway will automatically detect the push and redeploy your app:

1. Go to https://railway.app/
2. Open your StoryKeep project
3. Watch the deployment progress
4. Wait for the build to complete (usually 2-5 minutes)

### Step 3: Verify the Fix

Once deployed:

1. Open the **StoryKeep iOS app**
2. Navigate to a photo
3. Tap **"Enhance Photo"**
4. Tap **"Auto Enhance"**
5. Check that it works without the 400 error

## What the Endpoint Does

**URL**: `POST /api/photos/<photo_id>/enhance`  
**Authentication**: JWT Bearer token  
**Request Body**:
```json
{
  "settings": {},  // Optional enhancement settings
  "auto_enhance": true
}
```

**Success Response** (200):
```json
{
  "success": true,
  "message": "Photo enhanced successfully",
  "photo": {
    "id": 123,
    "filename": "original.jpg",
    "enhanced_filename": "username.enhanced.20251012.123456.jpg",
    "enhanced_url": "/uploads/1/username.enhanced.20251012.123456.jpg",
    "settings_applied": {...}
  }
}
```

**Error Responses**:
- `404` - Photo not found or access denied
- `404` - Photo file not found on disk
- `400` - Image too large (over 10MB)
- `500` - Enhancement processing failed

## Debugging on Railway

After deployment, if issues persist, check Railway logs:

1. Go to Railway dashboard
2. Click on your project
3. Click "Deployments" → Select latest deployment
4. Click "View Logs"
5. Look for emoji-marked log entries:
   - ✨ ENHANCE REQUEST - Request received
   - 📸 Found photo - Photo retrieved from database
   - 📂 Full file path - File location
   - 📏 File size - Size validation
   - ⚙️ Enhancement settings - Settings received
   - 🎯 Enhanced filename - Output filename
   - 🔧 Applying enhancements - Processing started
   - ✅ Enhancement complete - Processing finished
   - 💾 Database updated - Success
   - 💥 ENHANCE ERROR - Error occurred

## Common Issues

### 1. Still getting 400 error after deployment
**Solution**: Clear the Railway cache
```bash
# In Railway dashboard:
# Settings → Service → Restart → Hard Restart
```

### 2. Photo not found (404)
**Check**: 
- Photo exists in database
- User has permission to access photo
- File exists on Railway disk/storage

### 3. File too large (400)
**Limit**: 10MB per photo
**Solution**: Resize photo before uploading or increase limit in code

### 4. Enhancement failed (500)
**Check Railway logs** for specific error message with traceback

## Files Changed
- ✅ `photovault/routes/mobile_api.py` - Added enhanced logging to enhancement endpoint

## Next Steps After Deployment
1. Test Auto Enhance on Railway
2. Test Colorize feature (also uses JWT auth)
3. Verify enhanced photos appear in gallery
4. Check that edited photos are accessible

---

**Note**: This fix is already working on your **local Replit server**. You just need to push it to Railway for production!
