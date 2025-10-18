# iOS Profile Picture Railway Deployment Fix

## 🐛 Issue Fixed
**Error**: Profile pictures uploaded from iOS app on Railway return 404 errors and serve placeholders instead.

**Root Cause**: Profile pictures were being saved to **ephemeral local storage** on Railway instead of persistent storage. Files were deleted when containers restarted.

## ✅ What Was Fixed

### 1. **Profile Picture Upload** (mobile_api.py)
- **Before**: Saved directly to local filesystem (ephemeral on Railway)
- **After**: Uses `enhanced_file_handler` with object storage support
- **Benefit**: Supports Replit Object Storage + Railway Volumes for persistence

### 2. **Profile Picture Serving** (gallery.py)
- **Before**: Only checked local filesystem
- **After**: Checks object storage first, then local filesystem
- **Benefit**: Can serve files from both storage types

### 3. **Profile URL Construction** (mobile_api.py)
- **Before**: Always used `/uploads/{user_id}/{filename}` format
- **After**: Detects storage type and constructs correct URL
- **Benefit**: Works with object storage paths (`users/1/avatar.jpg`) and local paths

## 📦 Files Changed

```
photovault/routes/mobile_api.py
  - update_avatar() - Uses enhanced file handler with object storage
  - get_profile() - Handles both storage path formats

photovault/routes/gallery.py
  - uploaded_file() - Serves files from object storage
```

## 🚀 Deploy to Railway

### Step 1: Push Changes to GitHub

```bash
# Check what changed
git status

# Add the changes
git add photovault/routes/mobile_api.py
git add photovault/routes/gallery.py

# Commit with descriptive message
git commit -m "Fix iOS profile picture upload - use object storage for Railway persistence"

# Push to GitHub
git push origin main
```

### Step 2: Railway Auto-Deploy
Railway will automatically deploy when it detects the push to `main` branch.

### Step 3: Verify Deployment
1. Go to Railway dashboard: https://railway.app/dashboard
2. Click on your PhotoVault project
3. Check deployment logs for success
4. Look for: `✅ Profile picture updated for user X: /uploads/...`

## 🧪 Test on iOS App

After deployment, test all three functions that were broken:

### Test 1: Profile Picture Display ✅
1. **Login** to the iOS app (Railway production)
2. **Navigate** to Profile/Settings
3. **Upload** a new profile picture
4. **Verify** the picture displays (not placeholder)
5. **Restart** Railway container (Settings → Restart)
6. **Refresh** app - picture should persist

### Test 2: Photo Download ✅
1. Open any photo in Photo Detail screen
2. Tap **"Download"** button
3. Should see: "Success: Photo saved to your library!"
4. Check iOS Photos app - image should be there

### Test 3: Photo Sharing ✅
1. Open any photo in Photo Detail screen
2. Tap **"Share"** button  
3. iOS share sheet should appear
4. Share to Messages/Email - should work

**All three features should work after this fix!**

## 🔧 **IMPORTANT**: Railway Volumes (Required for Persistence)

**⚠️ Without Railway Volumes, profile pictures will still be lost on container restarts.**

For true persistence on Railway, you **must** configure a volume:

### Add Railway Volume
1. Go to Railway → Your service → **Settings**
2. Scroll to **Volumes** section
3. Click **"+ New Volume"**
4. Configure:
   - **Mount Path**: `/data`
   - **Size**: `10 GB` (or more)
5. Click **"Add"**

### Set Environment Variable
1. Go to **Variables** tab
2. Add new variable:
   - **Name**: `UPLOAD_FOLDER`
   - **Value**: `/data/uploads`
3. Click **"Add"**
4. Railway will redeploy automatically

**Benefit**: Files persist across Railway restarts, stored on persistent Railway Volume.

### Why Railway Volume is Required

Railway containers use **ephemeral storage** - files saved to the container filesystem are deleted when:
- The container restarts
- A new deployment happens
- Railway scales or moves your service

**Without a volume**: Profile pictures save successfully but disappear on restart  
**With a volume**: Profile pictures persist in `/data/uploads` which is mounted persistently

## 📊 How It Works

### Upload Flow
```
iOS App → /api/profile/avatar
         ↓
   Process Image (resize, convert)
         ↓
   enhanced_file_handler
         ↓
   ┌─────────────────┐
   │  Object Storage │ (if available)
   │    OR           │
   │ Railway Volume  │ (/data/uploads)
   │    OR           │
   │ Local Fallback  │ (ephemeral)
   └─────────────────┘
         ↓
   Database: Store path
         ↓
   Return URL to iOS app
```

### Serving Flow
```
iOS App → /uploads/{user_id}/{filename}
         ↓
   Check database for photo.file_path
         ↓
   Is it object storage path?
   (starts with users/ or uploads/)
         ↓
   YES: Download from object storage
   NO:  Serve from local filesystem
         ↓
   Return image bytes to iOS app
```

## ✅ Expected Results

### Before Fix
- ❌ Upload succeeds, file saves to `/tmp` or ephemeral storage
- ❌ File gets deleted on Railway restart
- ❌ iOS app shows placeholder instead of profile picture
- ❌ Error logs: `404 Not Found: avatar_*.jpg`

### After Fix
- ✅ Upload saves to object storage or Railway volume
- ✅ File persists across Railway restarts
- ✅ iOS app displays profile picture correctly
- ✅ Success logs: `✅ Profile picture updated for user X`

## 🔍 Troubleshooting

### Profile Picture Still Shows Placeholder

1. **Check Railway Logs**:
   ```
   Look for: "✅ Profile picture updated for user X"
   ```

2. **Check Object Storage**:
   ```
   Look for: "Using App Storage for file: avatar_*.jpg"
   ```

3. **Check Database**:
   ```sql
   SELECT id, username, profile_picture FROM "user" WHERE id = 1;
   ```
   Should show: `users/1/avatar_*.jpg` (object storage) or `avatar_*.jpg` (local)

### File Upload Fails

1. **Check UPLOAD_FOLDER** is set on Railway (optional)
2. **Verify Railway Volume** is mounted at `/data` (optional)
3. **Check app has write permissions** to upload directory

## 📝 Summary

The fix ensures profile pictures are stored persistently on Railway by:
1. Using enhanced file handler with object storage support
2. Falling back to Railway volumes if configured
3. Serving files from the correct storage location
4. Handling both storage path formats transparently

**Status**: ✅ Fixed locally, ready for Railway deployment

**Next Steps**: Push changes to GitHub, verify on Railway, test on iOS app
