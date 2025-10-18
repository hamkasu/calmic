# Railway Deployment Guide - Colorization Models Fix

## Issue Identified ✅

The iOS app colorization feature was **failing on Railway** because the DNN colorization model files were missing from the deployment. 

### Root Cause
- **DNN Colorization** requires 3 model files totaling ~123MB
- These files were not included in the Railway deployment
- The colorization endpoints exist but fail because the model can't initialize

## Files Fixed on Replit

The following colorization model files have been downloaded and are now working on Replit:

```
photovault/utils/models/colorization/
├── colorization_deploy_v2.prototxt     (9.8 KB)
├── colorization_release_v2.caffemodel  (123 MB) ⭐ Main model
└── pts_in_hull.npy                     (5 KB)
```

**Status on Replit:** ✅ Colorization working
**Status on Railway:** ❌ Models missing - colorization fails

## Deployment Options for Railway

### Option 1: Download Models on Railway Startup (RECOMMENDED)

Add a startup script to Railway that downloads models automatically:

**Step 1:** Create a startup script
```bash
# File: scripts/download_models.sh
#!/bin/bash
echo "🎨 Downloading colorization models..."
python photovault/utils/download_models.py
echo "✅ Colorization models ready"
```

**Step 2:** Update Railway configuration

In `nixpacks.toml` or `Procfile`:
```toml
# Add to nixpacks.toml
[phases.setup]
cmds = ['chmod +x scripts/download_models.sh', './scripts/download_models.sh']

# OR update Procfile
release: python photovault/utils/download_models.py
web: gunicorn --bind=0.0.0.0:$PORT --reuse-port main:app
```

**Advantages:**
- ✅ No need to commit large files to Git
- ✅ Always gets latest model versions
- ✅ Smaller repository size
- ✅ Automatic setup on each deployment

**Step 3:** Deploy to Railway
```bash
git add scripts/download_models.sh
git add nixpacks.toml  # or Procfile
git commit -m "Add automatic colorization model download for Railway"
git push origin main
```

### Option 2: Commit Models to Git (NOT RECOMMENDED)

⚠️ **Warning:** This adds 123MB to your repository

```bash
# Add models to git
git add photovault/utils/models/colorization/
git commit -m "Add colorization model files for Railway deployment"
git push origin main
```

**Disadvantages:**
- ❌ Large repository size (123MB)
- ❌ Slow git operations
- ❌ GitHub may reject push (file size limits)

### Option 3: Use Railway Persistent Storage

Store models in Railway's persistent volume:

1. Add persistent storage volume in Railway dashboard
2. Mount to `/app/photovault/utils/models/colorization`
3. Run model download once
4. Models persist across deployments

## Testing Colorization on Replit (Local)

The models are now working locally. Test with this simple script:

```python
from photovault.utils.colorization import get_colorizer

colorizer = get_colorizer()
print(f"Initialized: {colorizer.initialized}")
print(f"Model loaded: {colorizer.net is not None}")
```

**Expected output:**
```
Initialized: True
Model loaded: True
```

## iOS App Colorization Endpoints

The iOS app uses two colorization methods:

### 1. DNN Colorization (Requires Models)
```
POST /api/photos/{photo_id}/colorize
Authorization: Bearer <jwt_token>
Body: { "method": "auto" }
```

**This endpoint requires the downloaded models to work!**

### 2. AI Colorization (Requires Gemini API)
```
POST /api/photos/{photo_id}/colorize-ai
Authorization: Bearer <jwt_token>
```

**This endpoint uses Google Gemini AI - works without DNN models**

## Verification Steps

### After Railway Deployment:

1. **Check if models exist on Railway:**
```bash
# SSH into Railway container (if available)
ls -lh /app/photovault/utils/models/colorization/
```

2. **Test DNN Colorization via API:**
```bash
# Replace with your JWT token
curl -X POST \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"method":"auto"}' \
  https://web-production-535bd.up.railway.app/api/photos/1/colorize
```

**Expected success response:**
```json
{
  "success": true,
  "message": "Photo colorized successfully",
  "photo": {
    "id": 1,
    "colorized_url": "/uploads/1/filename_colorized.jpg"
  }
}
```

**If models missing, you'll get:**
```json
{
  "success": false,
  "error": "Colorization failed: DNN colorization model not initialized"
}
```

3. **Test in iOS app:**
   - Open any black & white photo
   - Tap "Enhance Photo"
   - Tap "Colorize (DNN)"
   - Should colorize successfully

## Current Status Summary

| Environment | DNN Models | Status | Action Needed |
|-------------|-----------|---------|---------------|
| **Replit (Local)** | ✅ Downloaded | ✅ Working | None - Already fixed |
| **Railway (Production)** | ❌ Missing | ❌ Broken | Deploy using Option 1 above |

## Recommended Deployment Plan

1. ✅ **Already Done:** Downloaded models on Replit
2. ✅ **Already Done:** Verified colorization works locally
3. ⏳ **Next Step:** Create startup script for Railway (Option 1)
4. ⏳ **Next Step:** Deploy to Railway with auto-download
5. ⏳ **Next Step:** Test iOS colorization on Railway production

## Model Download Script

The download script already exists at `photovault/utils/download_models.py`:

**Downloads from:**
- `colorization_deploy_v2.prototxt` - GitHub (Richard Zhang's colorization repo)
- `colorization_release_v2.caffemodel` - Dropbox (123MB model)
- `pts_in_hull.npy` - GitHub (color points data)

**Run manually:**
```bash
cd photovault/utils
python download_models.py
```

## Troubleshooting

### Issue: Models not downloading on Railway
**Cause:** Network restrictions or download timeout
**Solution:** Pre-download and commit to Git (Option 2)

### Issue: Railway out of memory during model load
**Cause:** 123MB model + other services exceed memory limit
**Solution:** Upgrade Railway plan or use AI colorization only

### Issue: Colorization still fails after deployment
**Cause:** Models downloaded but initialization failed
**Solution:** Check Railway logs for error messages

## Questions?

The colorization feature works on Replit now. To deploy to Railway, use **Option 1** (automatic download on startup) as it's the cleanest solution.
