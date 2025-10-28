# Fix Sketch & Cartoon 400 Error on Railway

## Problem
iOS app gets "Bad request" (400 error) when using Sketch and Cartoon enhancement features.

## Root Cause
The `@hybrid_auth` decorator passes `current_user` as the first parameter, but the `sketch_photo_route()` and `cartoon_photo_route()` functions weren't accepting it. This caused a function signature mismatch resulting in 400 errors.

## Fix Applied
Updated function signatures in `photovault/routes/photo.py`:

**Before:**
```python
@photo_bp.route('/api/photos/<int:photo_id>/sketch', methods=['POST'])
@hybrid_auth
def sketch_photo_route(photo_id):  # ❌ Missing current_user parameter
```

**After:**
```python
@photo_bp.route('/api/photos/<int:photo_id>/sketch', methods=['POST'])
@hybrid_auth
def sketch_photo_route(current_user, photo_id):  # ✅ Accepts current_user from decorator
```

Same fix applied to `cartoon_photo_route()`.

## Deploy to Railway

### Option 1: Using Git (Recommended)
```bash
# 1. Commit the fix
git add photovault/routes/photo.py
git commit -m "Fix sketch and cartoon endpoints for iOS - accept current_user parameter"

# 2. Push to Railway (deploys automatically)
git push origin main
```

### Option 2: Railway CLI
```bash
railway up
```

## Verify the Fix

After deploying, test with the iOS app:
1. Open StoryKeep app
2. Select a photo → Enhance Photo
3. Try "Sketch" or "Cartoonify"
4. Should create the effect successfully instead of showing "Bad request"

## Endpoints Fixed
- ✅ `/api/photos/<int:photo_id>/sketch` - Creates pencil/pen sketch effect
- ✅ `/api/photos/<int:photo_id>/cartoon` - Creates cartoon/comic effect

## Notes
- Sharpen, Colorize, and AI Restoration endpoints were already working correctly
- This fix only affects Sketch and Cartoon features
- No database changes required
- Changes tested locally on Replit dev server
