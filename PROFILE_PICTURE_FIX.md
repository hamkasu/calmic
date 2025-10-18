# Profile Picture Upload Fix for Railway

## Problem
Profile picture upload was failing on Railway with a 500 error when uploading from the iOS app.

## Root Cause
The issue was likely caused by one or more of these Railway-specific problems:
1. **UPLOAD_FOLDER not configured** - Environment variable missing or incorrect
2. **File system permissions** - Upload directory not writable
3. **Directory creation failures** - Unable to create user folders
4. **Weak error handling** - Original code didn't properly catch and log errors

## What Was Fixed

### 1. Enhanced Error Logging
Added comprehensive emoji-based logging to track every step:
- 📸 Upload started
- ✅ File received  
- 📊 File size validation
- 📝 Filename generation
- 📂 UPLOAD_FOLDER configuration check
- 📁 User folder creation
- 💾 File saving
- 🖼️ Image resize
- 🗑️ Old file deletion
- 💾 Database update
- 🎉 Success

### 2. Robust Error Handling
Added try-catch blocks for all critical operations:
- **Filename extraction** - Safely handles invalid filenames
- **Upload folder validation** - Checks if UPLOAD_FOLDER is configured
- **Directory creation** - Catches permission errors
- **File save operation** - Handles write failures
- **Image resize** - Continues even if resize fails
- **Database updates** - Rolls back on failure

### 3. Better Error Messages
- Server logs show full stack traces
- Client receives specific error messages
- Each failure point is clearly identified

## Files Modified:
- `photovault/routes/mobile_api.py` - Added robust error handling and comprehensive logging

## How to Deploy to Railway

### Step 1: Commit Your Changes
```bash
git add photovault/routes/mobile_api.py
git commit -m "Fix: Add comprehensive logging to profile picture upload endpoint"
```

### Step 2: Push to GitHub
```bash
git push origin main
```

### Step 3: Railway Auto-Deploys
Railway will automatically:
1. Detect the new commit
2. Build the updated code
3. Deploy the changes

### Step 4: Verify Railway Configuration
**IMPORTANT:** Check that Railway has the required environment variable:

1. Go to Railway dashboard: https://railway.app
2. Select your project
3. Click on "Variables" tab
4. **Check if `UPLOAD_FOLDER` exists:**
   - ✅ If it exists: Good! (should be `/data/uploads` or similar)
   - ❌ If missing: **Add it now:**
     ```
     UPLOAD_FOLDER=/data/uploads
     ```

### Step 5: Test on iOS App
1. Open the StoryKeep iOS app on your device
2. Go to Profile screen
3. Tap the camera icon to upload a profile picture
4. Select an image from your library

### Step 6: Check Railway Logs (If Still Failing)
If the upload still fails, check Railway logs to see the detailed error:

1. Go to Railway dashboard: https://railway.app
2. Select your project
3. Click on "Deployments"
4. Click on the latest deployment
5. View the logs to see the detailed error messages with emojis:
   - Look for 📸 (upload started)
   - Check where the process stops
   - Find any ❌ or ⚠️ error messages
   - Check the full traceback for the exact error

## Common Issues on Railway

### 1. File System Permissions
**Symptom**: Error when saving file: "Permission denied"
**Solution**: Ensure UPLOAD_FOLDER is set to a writable directory (like `/data/uploads`)

### 2. Missing UPLOAD_FOLDER
**Symptom**: Error creating directory
**Solution**: Add `UPLOAD_FOLDER` environment variable in Railway settings

### 3. Pillow/PIL Issues
**Symptom**: Error during image resize: "No module named 'PIL'"
**Solution**: Ensure Pillow is in requirements.txt and deployed correctly

### 4. Database Connection
**Symptom**: Error during database commit
**Solution**: Check DATABASE_URL is configured correctly in Railway

## Next Steps

After deploying:
1. Test the profile picture upload on iOS
2. If it works: ✅ Done!
3. If it still fails: Check Railway logs for the detailed error with the emoji tracking
4. Share the Railway logs to identify the specific issue

The enhanced logging will help pinpoint exactly where the failure occurs on Railway.
