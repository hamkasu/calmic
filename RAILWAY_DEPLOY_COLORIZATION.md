# Railway Deployment Guide - Automatic Colorization Models

## ✅ What's Been Set Up

I've configured automatic colorization model downloads for Railway deployment. The models will be downloaded automatically during the release phase.

### Files Created/Modified:

1. **`scripts/download_colorization_models.sh`** ✨ NEW
   - Shell script to download and verify colorization models
   - Includes error handling and size verification
   - Won't fail deployment if download fails

2. **`release.py`** 📝 UPDATED
   - Added `download_colorization_models()` function
   - Automatically downloads models during Railway deployment
   - Shows download progress and file sizes in logs
   - Gracefully handles failures (won't break deployment)

### How It Works:

```
Railway Deployment Flow:
1. Build phase (install dependencies)
2. Release phase (nixpacks.toml runs release.py)
   ├── Download colorization models (NEW!)
   ├── Verify environment variables
   └── Run database migrations
3. Start application
```

## Deployment Instructions

### Step 1: Commit Changes to Git

```bash
# Add the new/modified files
git add release.py
git add scripts/download_colorization_models.sh
git add RAILWAY_DEPLOY_COLORIZATION.md

# Commit with descriptive message
git commit -m "Add automatic colorization model download for Railway

- Updated release.py to download models during deployment
- Created download script with error handling
- Models download automatically on Railway startup
- Won't fail deployment if download fails (uses fallback)"

# Push to GitHub
git push origin main
```

### Step 2: Monitor Railway Deployment

Railway will automatically:
1. Detect the push to main branch
2. Start building the new version
3. Run the release phase with model download
4. Deploy the updated server

**Watch the Railway logs for:**
```
PhotoVault Release: Checking colorization models...
PhotoVault Release: Downloading colorization models (this may take a minute)...
PhotoVault Release: ✓ colorization_deploy_v2.prototxt (0.0MB)
PhotoVault Release: ✓ colorization_release_v2.caffemodel (123.0MB)
PhotoVault Release: ✓ pts_in_hull.npy (0.0MB)
PhotoVault Release: Colorization models downloaded successfully
```

### Step 3: Verify Deployment

After Railway deployment completes, test the colorization:

#### Test 1: Check Model Status via API
```bash
# This will fail if models aren't loaded
curl -X POST \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"method":"dnn"}' \
  https://web-production-535bd.up.railway.app/api/photos/PHOTO_ID/colorize
```

**Success response:**
```json
{
  "success": true,
  "message": "Photo colorized successfully",
  "photo": {
    "id": 123,
    "colorized_url": "/uploads/1/filename_colorized.jpg",
    "method_used": "dnn"
  }
}
```

**If models missing (failure):**
```json
{
  "success": false,
  "error": "Colorization failed: DNN colorization model not initialized"
}
```

#### Test 2: iOS App - DNN Colorization
1. Open StoryKeep iOS app
2. Select a black & white photo
3. Tap "Enhance Photo"
4. Tap **"Colorize (DNN)"** (green icon)
5. ✅ Photo should colorize successfully

#### Test 3: iOS App - AI Colorization
1. Select same photo
2. Tap "Enhance Photo"
3. Tap **"Colorize (AI)"** (purple sparkles icon)
4. ✅ Photo should colorize with AI analysis

## Model Download Details

### What Gets Downloaded:
```
photovault/utils/models/colorization/
├── colorization_deploy_v2.prototxt     (9.8 KB)   - Model architecture
├── colorization_release_v2.caffemodel  (123 MB)   - Trained weights
└── pts_in_hull.npy                     (5 KB)     - Color points data
```

### Download Sources:
- **prototxt**: GitHub (Richard Zhang's colorization repo)
- **caffemodel**: Dropbox (direct download link)
- **npy**: GitHub (color points array)

### Railway Resources:
- **Download time**: ~30-60 seconds (depends on Railway network)
- **Storage**: ~123 MB on Railway filesystem
- **Memory impact**: Models loaded into memory when colorization runs

## Troubleshooting

### Issue 1: Download Fails on Railway
**Symptoms:** Railway logs show download errors
**Cause:** Network restrictions or timeout
**Solution:** Models download during release phase - check Railway logs for specific error

### Issue 2: Models Download But Colorization Still Fails
**Symptoms:** Download succeeds but API returns model initialization error
**Cause:** OpenCV or numpy version mismatch
**Solution:** 
```bash
# Check Railway Python environment
pip list | grep opencv
pip list | grep numpy
```

### Issue 3: Railway Runs Out of Memory
**Symptoms:** Deployment fails with OOM (Out of Memory) error
**Cause:** 123MB model + other services exceed memory limit
**Solution:** 
- Upgrade Railway plan for more memory
- OR use AI colorization only (no model download needed)
- OR reduce number of gunicorn workers

### Issue 4: Download Takes Too Long and Times Out
**Symptoms:** Release phase times out during model download
**Cause:** Slow network connection to Dropbox
**Solution:**
```bash
# Increase timeout in nixpacks.toml
[phases.release]
cmd = "timeout 300 python release.py"  # 5 minute timeout
```

## Current Status

| Environment | DNN Models | AI Models | Status |
|-------------|-----------|-----------|--------|
| **Replit (Local)** | ✅ Downloaded | ✅ Ready | ✅ Working |
| **Railway (Production)** | ⏳ Will download on next deploy | ✅ Ready | ⏳ Pending deployment |

## What Happens Next

1. **You push to GitHub** → Railway detects changes
2. **Railway builds** → Installs Python dependencies
3. **Release phase runs** → Downloads colorization models automatically
4. **App starts** → Models ready for use
5. **iOS app colorization** → Both DNN and AI methods work!

## Safety Features

✅ **Non-blocking**: If model download fails, deployment continues
✅ **Fallback method**: Basic colorization still works without models
✅ **Idempotent**: Won't re-download if models already exist
✅ **Logging**: Shows download progress in Railway logs
✅ **Size verification**: Confirms all 3 files are present

## Testing Locally (Already Done on Replit)

The models are already working on Replit:
```bash
# Test locally
python -c "
from photovault.utils.colorization import get_colorizer
colorizer = get_colorizer()
print(f'Initialized: {colorizer.initialized}')
print(f'Model loaded: {colorizer.net is not None}')
"
```

**Output:**
```
Initialized: True
Model loaded: True
```

## Ready to Deploy!

Just run these commands:
```bash
git add release.py scripts/download_colorization_models.sh
git commit -m "Add automatic colorization model download for Railway"
git push origin main
```

Then watch the Railway deployment logs to see the models download automatically! 🚀
