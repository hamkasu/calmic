# 🚨 Railway Storage Fix - Photos Not Persisting

## Problem
Photos upload successfully but disappear after Railway restarts because `/data/uploads/` is in **ephemeral storage** (temporary).

**Evidence:**
- Database has photo records ✅
- File paths stored correctly: `/data/uploads/2/hamka.20251018.601978.jpg` ✅
- Actual files missing from filesystem ❌
- Server logs: "File not found" + serving placeholders ❌

## Root Cause
Railway containers use **ephemeral storage** by default. When the container restarts:
- All files in `/data/` are **deleted**
- Database records remain
- Result: Photos show as placeholders

## Solution: Add Railway Persistent Volume

### Step 1: Create Volume in Railway Dashboard
1. Go to **Railway Dashboard** → Your PhotoVault service
2. Click **Settings** tab
3. Scroll to **Volumes** section
4. Click **"New Volume"** or **"+ Add Volume"**
5. Configure:
   - **Mount Path**: `/data`
   - **Name**: `photovault-uploads` (or any name)
6. Click **Add** or **Create**

### Step 2: Verify Environment Variable
The app is already configured to use `/data/uploads`. Check that Railway has:
- **Variable**: `UPLOAD_FOLDER`
- **Value**: `/data/uploads`

If not set:
1. Go to **Variables** tab
2. Add **New Variable**:
   - **Name**: `UPLOAD_FOLDER`
   - **Value**: `/data/uploads`
3. Click **Add**

### Step 3: Redeploy
Railway will automatically redeploy after adding the volume. If not:
1. Click **Deployments** tab
2. Click **"Deploy"** or **"Redeploy"**

### Step 4: Re-upload Photos
**Important**: Existing photos in the database point to files that are now gone. You'll need to:

**Option A - Fresh Start** (if photos aren't critical):
1. Users re-upload all photos after volume is mounted
2. Old database records will continue showing placeholders

**Option B - Clean Database** (recommended):
1. After volume is mounted, run a cleanup:
   ```bash
   # Connect to Railway and run:
   python cleanup_orphaned_photos.py
   ```
2. This removes database records for missing files
3. Users re-upload photos

## Alternative: Use Object Storage (Cloud-Based)

Instead of Railway volumes, use cloud storage like:
- AWS S3
- Google Cloud Storage
- Replit Object Storage (if available on Railway)

**Advantage**: Files never lost, even on restarts  
**Disadvantage**: Additional setup and costs

### Enable Object Storage
The app has object storage support built-in but needs configuration:

1. Sign up for cloud storage (S3, GCS, etc.)
2. Set Railway environment variables:
   ```
   USE_OBJECT_STORAGE=true
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   AWS_BUCKET_NAME=your_bucket
   AWS_REGION=us-east-1
   ```
3. Redeploy

## Comparison

| Solution | Pros | Cons |
|----------|------|------|
| **Railway Volume** | ✅ Simple, no extra cost, fast | ⚠️ Limited by Railway storage limits |
| **Object Storage** | ✅ Unlimited, never lost, CDN delivery | ⚠️ Extra setup, ongoing costs |

## Recommended: Railway Volume + Future Migration

1. **Now**: Add Railway Volume (quick fix)
2. **Later**: Migrate to object storage as you scale

## Verification After Fix

Once the volume is mounted and app redeployed:

1. Upload a new photo via web or mobile app
2. Restart Railway service manually (Settings → Restart)
3. Check if photo still shows after restart ✅

If photos persist after restart = **Problem solved!** 🎉

## Current Status

❌ **No persistent storage configured**  
⚠️ **All uploaded photos are lost on restart**  
🔧 **Fix: Add Railway Volume at `/data` mount path**

## Next Steps

1. Add Railway Volume now (5 minutes)
2. Redeploy automatically
3. Test photo upload
4. Restart Railway to verify persistence
5. Clean up orphaned database records
6. Users can re-upload photos safely

---

**Priority**: 🔴 **CRITICAL** - Without this, all photos are temporary and will disappear!
