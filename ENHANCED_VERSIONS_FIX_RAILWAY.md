# Enhanced Versions Fix - Railway Deployment Guide

## Problem Fixed
The Enhanced Versions gallery in the iOS app was showing empty because photo enhancement endpoints (sharpen, colorize, enhance, colorize-ai) were updating the original photo's `edited_filename` field instead of creating separate enhanced version records.

## Solution
Updated all four enhancement endpoints in `photovault/routes/mobile_api.py` to create NEW photo records with proper linking:
- Set `original_photo_id` to link back to the original photo
- Set `is_enhanced_version = True` to mark as enhanced
- Set `enhancement_type` to indicate the type of enhancement ('sharpened', 'colorized', 'enhanced', 'colorized_ai')

## Files Changed
- `photovault/routes/mobile_api.py`: Updated 4 endpoints:
  1. `/api/photos/<int:photo_id>/sharpen` (line ~2786)
  2. `/api/photos/<int:photo_id>/enhance` (line ~2313)
  3. `/api/photos/<int:photo_id>/colorize` (line ~2434)
  4. `/api/photos/<int:photo_id>/colorize-ai` (line ~2568)

## Deployment Steps

### 1. Push Code to Railway
```bash
# Make sure you're on the main branch
git status

# Add the changes
git add photovault/routes/mobile_api.py

# Commit with descriptive message
git commit -m "Fix: Create separate photo records for enhanced versions

- Sharpen, colorize, enhance, and colorize-ai now create new photos
- Set original_photo_id, is_enhanced_version, enhancement_type
- Enhanced Versions gallery will now display all enhancements"

# Push to GitHub (Railway will auto-deploy)
git push origin main
```

### 2. Monitor Railway Deployment
1. Go to Railway dashboard: https://railway.app/
2. Watch the deployment logs for any errors
3. Wait for "Deployment successful" message

### 3. Test on iOS App
After Railway deploys:

1. **Open an existing photo in the app**
2. **Tap "Enhance" button**
3. **Apply sharpening or other enhancement**
4. **Tap the "Enhanced" button in PhotoDetail**
5. **Verify Enhanced Versions gallery shows the enhancement**

Expected behavior:
- Each enhancement creates a new photo in the gallery
- Enhanced Versions screen shows all enhancements for that photo
- Each card displays: thumbnail, enhancement type, date
- Tapping an enhanced version opens it in PhotoDetail

### 4. Verify Database
After testing, check that enhanced photos have correct fields:
```sql
SELECT id, filename, original_photo_id, is_enhanced_version, enhancement_type 
FROM photo 
WHERE is_enhanced_version = TRUE 
ORDER BY created_at DESC 
LIMIT 10;
```

## What Changed

### Before (BROKEN)
```python
# Old code: Updated original photo's edited_filename
photo.edited_filename = enhanced_filename
db.session.commit()
```

### After (FIXED)
```python
# New code: Create separate enhanced version
new_photo = Photo()
new_photo.user_id = current_user.id
new_photo.filename = enhanced_filename
new_photo.original_photo_id = photo_id  # Link to original
new_photo.is_enhanced_version = True    # Mark as enhanced
new_photo.enhancement_type = 'sharpened'  # Set type
db.session.add(new_photo)
db.session.commit()
```

## Benefits
1. ✅ Multiple enhancements per photo (sharpen, colorize, etc.)
2. ✅ Original photo stays untouched
3. ✅ Enhanced Versions gallery now works correctly
4. ✅ Each enhancement tracked with metadata and timestamp
5. ✅ Users can compare multiple enhancement versions

## Rollback (if needed)
If something goes wrong, Railway keeps previous deployments:
1. Go to Railway dashboard
2. Click on your service
3. Go to "Deployments" tab
4. Find the previous working deployment
5. Click "Redeploy"

## Notes
- This fix is backward compatible - existing photos are not affected
- Future enhancements will automatically create proper enhanced versions
- The `/api/photos/<int:photo_id>/enhanced-versions` endpoint will now return all linked enhancements
