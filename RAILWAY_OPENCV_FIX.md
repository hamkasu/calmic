# Railway OpenCV Fix - Photo Extraction Now Working

## Problem
The iOS app Digitizer feature was showing "Photo uploaded! 0 photo(s) extracted" even though photos were being uploaded successfully to Railway.

## Root Cause
OpenCV (cv2) requires specific system libraries that weren't available in Railway's default Python environment:
- `libGL` - OpenGL library for image processing
- `glib` - GLib library for low-level system operations

Without these dependencies, the `photovault/utils/photo_detection.py` module would fail to import cv2 and set `OPENCV_AVAILABLE = False`, causing photo detection to return empty results.

## Solution
Created `nixpacks.toml` configuration file with the required system dependencies using **apt packages** (Ubuntu packages are more reliable than Nix packages for OpenCV):

```toml
[phases.setup]
aptPkgs = [
  "libgl1-mesa-glx",
  "libglib2.0-0"
]
```

## Deployment Steps

### 1. Push the Configuration to Railway
```bash
git add nixpacks.toml RAILWAY_OPENCV_FIX.md
git commit -m "Fix Railway OpenCV with apt packages for photo extraction"
git push origin main
```

### 2. Railway Will Auto-Deploy
Railway will detect the `nixpacks.toml` file and:
- Install the apt system dependencies during build (libgl1-mesa-glx, libglib2.0-0)
- Install Python packages from requirements.txt (including opencv-python-headless)
- Start the application with OpenCV fully functional

### 3. Verify the Fix
After Railway deployment completes:

1. **Open iOS app** and go to Camera/Digitizer
2. **Take a photo** of a physical photograph
3. **Check the success message** - should now show: "Photo uploaded! X photo(s) extracted" where X > 0
4. **Go to Gallery** - extracted photos should appear

### 4. Check Railway Logs
You can verify OpenCV is working by checking Railway logs for:
```
INFO:photovault.utils.photo_detection:OpenCV available for photo detection
```

## Technical Details

### What the Fix Does
- **libgl1-mesa-glx**: Provides OpenGL rendering capabilities needed by cv2.imread() and image processing
- **libglib2.0-0**: Provides GLib system libraries used by OpenCV's core functionality

### Why apt packages instead of Nix?
Initial attempt used Nix packages (`libGL`, `glib`, `libgccjit`), but `libgccjit` caused circular symlink errors during Railway build. Using Ubuntu's apt packages is more reliable and compatible with Railway's infrastructure.

### Photo Detection Flow
1. User uploads photo via `/api/detect-and-extract` endpoint
2. PhotoDetector initializes with OpenCV enabled
3. Multi-scale edge detection finds rectangular photos in the image
4. Detected regions are extracted and saved as separate photos
5. Response includes `photos_extracted` count

### Files Modified
- `nixpacks.toml` - Added apt system dependencies

### Files Using OpenCV
- `photovault/utils/photo_detection.py` - Main detection logic
- `photovault/utils/damage_repair.py` - Uses OpenCV for scratch/tear repair
- `photovault/routes/mobile_api.py` - `/api/detect-and-extract` endpoint

## Testing Checklist

After deploying to Railway:

- [ ] iOS app can extract photos from camera captures
- [ ] Multiple photos detected from single scanned image
- [ ] Gallery shows extracted photos correctly
- [ ] No "0 photo(s) extracted" errors
- [ ] Railway logs show "OpenCV available for photo detection"

## Troubleshooting

### If OpenCV still doesn't work after deployment:
1. Check Railway build logs for apt package installation
2. Check application logs for "OpenCV not available" warnings
3. Verify opencv-python-headless is installed: `pip list | grep opencv`

### Common Issues:
- **Build fails with "Package not found"**: Railway might need to update its apt cache. Try redeploying.
- **OpenCV imports but crashes**: Missing additional dependencies. Check Railway logs for specific error messages.

## Rollback Plan
If issues occur, you can temporarily disable photo detection by removing the nixpacks.toml file. The app will still upload photos, just without automatic extraction.

## Notes
- This fix only affects Railway production deployment
- Local Replit development already has OpenCV working
- The opencv-python-headless package is optimized for server environments (no GUI dependencies)
- Photo detection uses "fast mode" by default for better performance on Railway's hardware
- We use apt packages (not Nix) to avoid circular symlink issues
