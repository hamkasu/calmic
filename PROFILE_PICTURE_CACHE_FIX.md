# Profile Picture Cache Fix - Railway Deployment Guide

## Problem
Profile pictures were not updating on the Dashboard after being changed. The image showed correctly on the Profile screen but the Dashboard showed the old cached image.

## Root Cause
React Native's Image component caches images by their URL. When you upload a new profile picture with the same filename (e.g., `avatar.jpg`), the URL stays the same, so React Native shows the cached old image instead of the new one.

## Solution
Completely rewrote Dashboard to use the **same working approach as Profile screen**: download image to local cache using `FileSystem.downloadAsync()` before displaying.

## Files Changed
- `StoryKeep-iOS/src/screens/DashboardScreen.js`:
  - Added `FileSystem` import from `expo-file-system/legacy`
  - Added `profileImageUri` state (stores local file URI)
  - Added `loadProfileImage()` function (downloads image to local cache)
  - Updated `useFocusEffect` to reload profile image on screen focus
  - Changed Image component to use local file URI instead of remote URL

## How It Works (Same as Profile Screen)
1. When Dashboard loads or comes into focus:
   - Fetches profile data from API
   - If profile picture exists, calls `loadProfileImage()`
2. `loadProfileImage()` downloads image to local cache:
   - Uses `FileSystem.downloadAsync()` with authentication headers
   - Saves to: `${FileSystem.cacheDirectory}dashboard_profile_picture.jpg`
   - Sets `profileImageUri` to local file path
3. Image component displays from local cache:
   - No HTTP caching issues
   - Always shows latest image
   - Proper authentication (downloaded with Bearer token)

## Deployment Steps for Railway

### Option 1: Using Railway Dashboard
1. Open your Railway project dashboard
2. Go to your web service
3. Click on "Variables" tab
4. Click "Redeploy" to trigger a new deployment with latest code from GitHub

### Option 2: Using Git Push
1. Make sure all changes are committed:
   ```bash
   git add StoryKeep-iOS/src/screens/DashboardScreen.js
   git commit -m "Fix profile picture cache issue on Dashboard"
   git push origin main
   ```

2. Railway will automatically detect the push and redeploy

### Option 3: Manual Trigger
1. In Railway dashboard, click your service
2. Click "Deployments" tab
3. Click "Deploy" > "Deploy latest commit"

## Testing After Deployment
1. Open StoryKeep app on your iOS device
2. Go to Profile screen
3. Upload a new profile picture
4. Navigate back to Dashboard
5. Profile picture should now show the updated image immediately

## Important Notes
- This fix only affects the iOS app (StoryKeep-iOS)
- No backend/Python code changes required
- No database migration needed
- The fix works by adding a query parameter that doesn't affect the server
- Works on both Replit (development) and Railway (production)

## Verification
After deployment, check that:
- ✅ Profile picture updates immediately on Dashboard after changing it
- ✅ No duplicate requests (cache key only updates when profile data changes)
- ✅ Image loads with authentication headers (shows private images correctly)
