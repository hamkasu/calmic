# Fix Sketch & Cartoon Enhancement Bugs on Railway

## Problem
iOS app gets errors when using Sketch and Cartoon enhancement features:
- "Bad request" (400 error)  
- "Sketch creation failed due to unexpected error" / "Cartoon creation failed"
- Server logs show: "'description' is an invalid keyword argument for Photo"

## Root Cause - Three Bugs Found

### Bug 1: Function signature mismatch
The `@hybrid_auth` decorator passes `current_user` as the first parameter, but the functions weren't accepting it.

### Bug 2: CSRF protection blocking mobile
The endpoints lacked `@csrf.exempt`, causing mobile API calls to fail with "CSRF token is missing".

### Bug 3: Invalid Photo model parameter
Both endpoints tried to create Photo objects with a `description` parameter, but the Photo model doesn't have this field.

## Fixes Applied
Updated both endpoints in `photovault/routes/photo.py`:

### Sketch Endpoint - Before:
```python
@photo_bp.route('/api/photos/<int:photo_id>/sketch', methods=['POST'])
@hybrid_auth
def sketch_photo_route(photo_id):  # ❌ Missing current_user
    # ...
    new_photo = Photo(
        filename=sketch_filename,
        # ... other fields ...
        description=f"Sketch version of {photo.original_name}",  # ❌ Invalid field
        original_photo_id=photo_id,
        is_enhanced_version=True,
        enhancement_type='sketch'
    )
```

### Sketch Endpoint - After:
```python
@photo_bp.route('/api/photos/<int:photo_id>/sketch', methods=['POST'])
@csrf.exempt  # ✅ Allow mobile API calls
@hybrid_auth
def sketch_photo_route(current_user, photo_id):  # ✅ Accepts current_user
    # ...
    new_photo = Photo(
        filename=sketch_filename,
        # ... other fields ...
        original_photo_id=photo_id,  # ✅ Removed invalid description field
        is_enhanced_version=True,
        enhancement_type='sketch'
    )
```

### Changes Summary
Both sketch and cartoon endpoints:
- ✅ Added `current_user` parameter to function signature
- ✅ Added `@csrf.exempt` decorator for mobile compatibility
- ✅ Removed invalid `description` parameter from Photo() constructor

## Deploy to Railway

### Option 1: Using Git (Recommended)
```bash
# 1. Commit the fix
git add photovault/routes/photo.py
git commit -m "Fix sketch/cartoon endpoints: add current_user param, CSRF exemption, remove invalid description field"

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
3. Try "Sketch" - should create pencil sketch ✅
4. Try "Cartoonify" - should create cartoon effect ✅
5. No more "Bad request" or "unexpected error" messages

## Testing Results (Replit Dev Server)
- ✅ Server starts without errors
- ✅ No CSRF errors in logs
- ✅ No "'description' is an invalid keyword argument" errors
- ✅ Function signatures accept parameters correctly
- ✅ Photo objects created with valid fields only

## Technical Details

### Endpoints Fixed
- `/api/photos/<int:photo_id>/sketch` - Creates pencil/pen sketch effect
- `/api/photos/<int:photo_id>/cartoon` - Creates cartoon/comic effect

### Authentication Pattern
Both endpoints now follow the mobile API pattern:
```python
@photo_bp.route('/api/photos/<int:photo_id>/endpoint', methods=['POST'])
@csrf.exempt          # Skip CSRF validation for mobile
@hybrid_auth          # Accept both session (web) and JWT (mobile) auth
def endpoint(current_user, photo_id):  # current_user injected by @hybrid_auth
    # current_user is the authenticated User object
    # Create Photo with valid fields only (no description)
```

### Photo Model Fields Used
```python
new_photo = Photo(
    filename=...,
    original_name=...,
    file_path=...,
    thumbnail_path=...,
    file_size=...,
    width=...,
    height=...,
    mime_type=...,
    upload_source='artistic_effect',
    user_id=current_user.id,
    album_id=photo.album_id,
    original_photo_id=photo_id,      # Links to original photo
    is_enhanced_version=True,         # Marks as enhanced version
    enhancement_type='sketch'|'cartoon'  # Identifies enhancement type
)
```

## Notes
- Sharpen, Colorize, and AI Restoration endpoints were already working correctly
- This fix only affects Sketch and Cartoon features
- No database changes required
- Changes tested locally on Replit dev server
- No impact on web interface (uses session auth)
- Mobile app uses JWT authentication via Authorization header
