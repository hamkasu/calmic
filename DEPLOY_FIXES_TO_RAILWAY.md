# Deploy iOS Fixes to Railway

## Issues Fixed
1. ✅ **Delete Photo Feature** - Added DELETE `/api/photos/<id>` endpoint
2. ✅ **Logout Feature** - Fixed logout to properly clear session and navigate
3. ⚠️ **Sharpen Photo Feature** - Endpoint exists, may need testing on Railway

## Backend Changes (mobile_api.py)
- Added delete photo endpoint with:
  - Ownership verification
  - Safe file deletion (original/thumbnail/edited)
  - Complete cleanup of voice memos, vault associations, tags, comments
  - Transaction rollback on errors

## iOS App Changes
- **DashboardScreen.js** - Improved logout flow
- **SettingsScreen.js** - Improved logout flow
- Logout now:
  1. Removes authToken first to trigger auth check
  2. Waits briefly for state change detection
  3. Clears all remaining storage and biometric data
  4. App.js automatically navigates to Login screen

## Deployment Steps

### 1. Commit Your Changes
```bash
# Backend fix
git add photovault/routes/mobile_api.py

# iOS fixes
git add StoryKeep-iOS/src/screens/DashboardScreen.js
git add StoryKeep-iOS/src/screens/SettingsScreen.js

git commit -m "Fix iOS delete photo, logout, and investigate sharpen issues

Backend:
- Add DELETE /api/photos/<id> endpoint for mobile app
- Complete deletion with ownership verification
- Safe file operations with error handling

iOS:
- Fix logout to properly clear session
- Improved navigation after logout
- Better error handling"
```

### 2. Push to GitHub
```bash
git push origin main
```

### 3. Railway Auto-Deploy
Railway will automatically detect the push and deploy the changes.

### 4. Wait for Deployment
- Check Railway dashboard for deployment status
- Wait for "Deployed" status before testing

### 5. Test on iOS App
1. **Logout Test**:
   - Tap Settings
   - Tap Logout button
   - Confirm logout
   - Should navigate to Login screen ✅
   
2. **Delete Photo Test**:
   - Login again
   - Go to a photo detail screen
   - Tap delete icon
   - Confirm deletion
   - Should delete photo successfully ✅
   
3. **Sharpen Photo Test**:
   - Go to Enhance Photo screen
   - Tap Sharpen button
   - Check if it works or shows error

## Troubleshooting

### If Sharpen Still Fails:
The sharpen endpoint exists but might have issues on Railway:
- Check Railway logs for error messages
- Possible issues:
  - File permissions on Railway
  - Missing dependencies (PIL/Pillow)
  - Disk space/memory limits

### If Delete Still Fails:
- Verify deployment completed successfully
- Check Railway logs for errors
- Ensure iOS app cache is cleared (force quit and reopen)

## Railway Logs
To check logs on Railway:
1. Go to Railway dashboard
2. Select your project
3. Click on "Deployments"
4. View logs for errors

## Next Steps
After deploying:
1. Test both delete and sharpen features
2. If sharpen still fails, check Railway logs and report the error
3. Clear iOS app cache if needed (force quit and reopen)
