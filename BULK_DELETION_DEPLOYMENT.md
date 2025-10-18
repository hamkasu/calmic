# Bulk Deletion Feature - Railway Deployment Guide

## Overview
This guide covers deployment of the bulk deletion feature for the StoryKeep iOS mobile app. Users can now select multiple photos and delete them in one action.

**Created:** October 13, 2025  
**Status:** Ready for Production Deployment

---

## What's New

### Backend Changes
1. **New API Endpoint**: `POST /api/photos/bulk-delete`
   - Accepts array of photo IDs
   - JWT authentication required
   - Deletes all associated files and data
   - Returns deletion statistics

2. **File Cleanup**: Comprehensive deletion of:
   - Original photos
   - Thumbnails
   - Edited versions
   - Voice memo files

3. **Database Cleanup**: Cascading deletion of:
   - VaultPhoto entries
   - PhotoTag entries
   - PhotoComment entries
   - Voice memo records

### iOS Changes
1. **Selection Mode**:
   - "Select" button in gallery header
   - Long press to enter selection mode
   - Checkboxes on each photo

2. **Multi-Select UI**:
   - Visual feedback for selected photos
   - Selected count in header
   - Delete button (trash icon)

3. **User Flow**:
   - Tap "Select" or long press photo
   - Tap photos to select/deselect
   - Tap delete button
   - Confirm deletion
   - See success/error alerts

---

## Files Modified

### Backend
- `photovault/routes/mobile_api.py` - Added `/api/photos/bulk-delete` endpoint

### iOS App
- `StoryKeep-iOS/src/services/api.js` - Added `bulkDeletePhotos()` method
- `StoryKeep-iOS/src/screens/GalleryScreen.js` - Multi-select UI and logic

---

## Deployment Steps

### Step 1: Commit and Push to Railway

```bash
# Ensure you're on main branch
git checkout main

# Stage all changes
git add photovault/routes/mobile_api.py
git add StoryKeep-iOS/src/services/api.js
git add StoryKeep-iOS/src/screens/GalleryScreen.js

# Commit with descriptive message
git commit -m "feat: Add bulk deletion feature for iOS app

- New POST /api/photos/bulk-delete endpoint with JWT auth
- Comprehensive file cleanup (original/thumbnail/edited/voice memos)
- Database cleanup (vault links, tags, comments)
- iOS multi-select mode with checkboxes
- Delete button with confirmation dialog
- Success/error feedback"

# Push to Railway
git push railway main
```

### Step 2: Monitor Deployment

1. **Watch Railway Logs**:
   ```
   railway logs
   ```

2. **Check for Errors**:
   - Look for successful deployment message
   - Verify no import errors
   - Check Flask app starts correctly

3. **Verify Endpoint**:
   ```bash
   curl -X POST https://web-production-535bd.up.railway.app/api/photos/bulk-delete \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"photo_ids": []}'
   ```
   
   Expected response:
   ```json
   {
     "message": "No photos selected for deletion",
     "deleted_count": 0,
     "failed_count": 0
   }
   ```

### Step 3: Test on iOS App

1. **Open StoryKeep App** on your iPhone/simulator

2. **Navigate to Gallery**

3. **Test Selection Mode**:
   - Tap "Select" button
   - Verify checkboxes appear
   - Select multiple photos
   - Verify header shows "X selected"

4. **Test Long Press**:
   - Long press any photo
   - Verify selection mode auto-activates
   - Verify that photo is selected

5. **Test Bulk Delete**:
   - Select 2-3 photos
   - Tap delete button (trash icon)
   - Verify confirmation dialog shows correct count
   - Confirm deletion
   - Verify photos are removed from gallery
   - Verify success alert appears

6. **Test Cancel**:
   - Enter selection mode
   - Select photos
   - Tap "Cancel" button
   - Verify selection mode exits
   - Verify checkboxes disappear

---

## API Endpoint Reference

### POST /api/photos/bulk-delete

**Authentication**: JWT token required

**Request Body**:
```json
{
  "photo_ids": [1, 2, 3, 4, 5]
}
```

**Success Response** (200):
```json
{
  "message": "Deleted 5 photos successfully",
  "deleted_count": 5,
  "failed_count": 0,
  "errors": []
}
```

**Partial Success Response** (200):
```json
{
  "message": "Deleted 3 photos, 2 failed",
  "deleted_count": 3,
  "failed_count": 2,
  "errors": [
    {"photo_id": 4, "error": "Photo not found"},
    {"photo_id": 5, "error": "Not authorized"}
  ]
}
```

**Error Response** (400):
```json
{
  "error": "photo_ids is required"
}
```

**Error Response** (401):
```json
{
  "error": "Invalid or expired token"
}
```

---

## Database Impact

### Tables Affected
1. **photos** - Main deletion
2. **vault_photos** - Cascade deletion
3. **photo_tags** - Cascade deletion
4. **photo_comments** - Cascade deletion
5. **voice_memos** - Explicit deletion

### File System Impact
- Deletes from `uploads/<username>/` directory:
  - Original photos
  - Thumbnails (`.thumbnail.jpg`)
  - Edited versions (`.edited.*`)
  - Voice memos (`.m4a`)

---

## Security Notes

1. **JWT Authentication**: All requests require valid JWT token
2. **Ownership Verification**: Users can only delete their own photos
3. **Transaction Safety**: Database rollback on critical failures
4. **Error Logging**: All deletion errors logged to server logs

---

## Rollback Plan

If issues occur after deployment:

1. **Revert Git Commit**:
   ```bash
   git revert HEAD
   git push railway main
   ```

2. **Monitor Logs**:
   ```bash
   railway logs
   ```

3. **Database Recovery**:
   - Deleted photos cannot be recovered
   - Use Replit checkpoints if needed for database restore

---

## Testing Checklist

- [ ] Deployment successful on Railway
- [ ] Endpoint returns 200 for valid requests
- [ ] JWT authentication working
- [ ] Selection mode UI works in iOS
- [ ] Checkboxes appear/disappear correctly
- [ ] Multi-select works (tap photos)
- [ ] Long press enters selection mode
- [ ] Delete button appears when photos selected
- [ ] Confirmation dialog shows correct count
- [ ] Photos deleted from gallery after confirmation
- [ ] Success alert appears
- [ ] Cancel button exits selection mode
- [ ] Files deleted from filesystem
- [ ] Database records deleted
- [ ] Error handling works (invalid photo IDs)

---

## Support

If you encounter issues:
1. Check Railway logs for errors
2. Verify JWT token is valid (30-day expiration)
3. Ensure iOS app is using correct API URL
4. Test endpoint with curl/Postman
5. Check database for orphaned records

---

## Next Steps

After successful deployment:
1. Monitor user feedback
2. Track deletion statistics
3. Consider adding:
   - Undo deletion (within 30 days)
   - Bulk restore from trash
   - Archive instead of delete option
