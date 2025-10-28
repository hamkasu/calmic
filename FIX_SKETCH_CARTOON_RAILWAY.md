# Fix Sketch & Cartoon 400 Error on Railway

## Problem
iOS app gets "Bad request" (400 error) when using Sketch and Cartoon enhancement features.

## Root Cause - Two Bugs Found
1. **Function signature mismatch**: The `@hybrid_auth` decorator passes `current_user` as the first parameter, but the functions weren't accepting it
2. **CSRF protection blocking mobile**: The endpoints lacked `@csrf.exempt`, causing mobile API calls to fail with "CSRF token is missing"

## Fixes Applied
Updated both endpoints in `photovault/routes/photo.py`:

### Fix 1: Add current_user parameter
**Before:**
```python
@photo_bp.route('/api/photos/<int:photo_id>/sketch', methods=['POST'])
@hybrid_auth
def sketch_photo_route(photo_id):  # ❌ Missing current_user parameter
```

**After:**
```python
@photo_bp.route('/api/photos/<int:photo_id>/sketch', methods=['POST'])
@csrf.exempt  # ✅ Allow mobile API calls
@hybrid_auth
def sketch_photo_route(current_user, photo_id):  # ✅ Accepts current_user from decorator
```

### Fix 2: Add @csrf.exempt decorator
Mobile apps (iOS/Android) cannot send CSRF tokens, so API endpoints need `@csrf.exempt`. This was already present on other mobile endpoints but missing on sketch/cartoon.

### Changes Summary
- ✅ Added `current_user` parameter to `sketch_photo_route(current_user, photo_id)`
- ✅ Added `current_user` parameter to `cartoon_photo_route(current_user, photo_id)`
- ✅ Added `@csrf.exempt` decorator to sketch endpoint
- ✅ Added `@csrf.exempt` decorator to cartoon endpoint

## Deploy to Railway

### Option 1: Using Git (Recommended)
```bash
# 1. Commit the fix
git add photovault/routes/photo.py
git commit -m "Fix sketch and cartoon endpoints for iOS - add current_user param and CSRF exemption"

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
3. Try "Sketch" - should work ✅
4. Try "Cartoonify" - should work ✅
5. Should create the effect successfully instead of showing "Bad request"

## Testing Results (Replit Dev Server)
- ✅ Server starts without errors
- ✅ Endpoint responds with 401 Unauthorized (not 400 Bad Request) when called without auth
- ✅ No CSRF errors in logs
- ✅ Function signatures accept parameters correctly

## Endpoints Fixed
- ✅ `/api/photos/<int:photo_id>/sketch` - Creates pencil/pen sketch effect
- ✅ `/api/photos/<int:photo_id>/cartoon` - Creates cartoon/comic effect

## Authentication Pattern
Both endpoints now follow the mobile API pattern:
```python
@photo_bp.route('/api/photos/<int:photo_id>/endpoint', methods=['POST'])
@csrf.exempt          # Skip CSRF validation for mobile
@hybrid_auth          # Accept both session (web) and JWT (mobile) auth
def endpoint(current_user, photo_id):  # current_user injected by @hybrid_auth
    # current_user is the authenticated User object
    # Access permissions and create enhanced photos
```

## Notes
- Sharpen, Colorize, and AI Restoration endpoints were already working correctly
- This fix only affects Sketch and Cartoon features
- No database changes required
- Changes tested locally on Replit dev server
- No impact on web interface (uses session auth)
- Mobile app uses JWT authentication via Authorization header
