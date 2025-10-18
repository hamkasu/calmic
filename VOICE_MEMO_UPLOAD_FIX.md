# Voice Memo Upload Fix - Railway Deployment Guide

## Problem Identified
Voice memo uploads from the iOS app were failing with "Bad request" error because:

1. **Route Conflict**: Two endpoints handle `/api/photos/<photo_id>/voice-memos`:
   - `photo.py` (registered first) - was missing `@csrf.exempt`
   - `mobile_api.py` (registered second) - has `@csrf.exempt`

2. **CSRF Validation**: Since `photo_bp` is registered before `mobile_api_bp`, requests go to `photo.py` which was requiring CSRF tokens that mobile apps don't send.

3. **Camera Upload Works**: The camera upload (`/api/detect-and-extract`) works because it only exists in `mobile_api.py` with `@csrf.exempt`.

## Solution Applied
Added `@csrf.exempt` decorator to the voice memo upload endpoint in `photovault/routes/photo.py`:

```python
@photo_bp.route('/api/photos/<int:photo_id>/voice-memos', methods=['POST'])
@csrf.exempt  # ← ADDED THIS LINE
@hybrid_auth
def upload_voice_memo(current_user, photo_id):
    """Upload a voice memo for a photo"""
    # ... rest of the code
```

## Railway Deployment Steps

### 1. Verify Local Changes
The fix has been applied to your Replit workspace. The change is in:
- File: `photovault/routes/photo.py`
- Line: 881 (added `@csrf.exempt` decorator)

### 2. Deploy to Railway
Since your iOS app connects to Railway production, you need to deploy this fix:

```bash
# Stage the change
git add photovault/routes/photo.py

# Commit the fix
git commit -m "Fix: Add @csrf.exempt to voice memo upload endpoint for mobile app compatibility"

# Push to trigger Railway deployment
git push origin main
```

### 3. Wait for Railway Deployment
- Railway will automatically detect the push and redeploy
- Wait 2-3 minutes for deployment to complete
- Check Railway dashboard for deployment status

### 4. Test Voice Memo Upload
Once deployed:
1. Open the iOS app (StoryKeep)
2. Navigate to any photo detail
3. Record a voice memo
4. Tap "Upload"
5. Should now show "Success" instead of "Bad request"

## Technical Details

### Why This Fix Works
- **CSRF Protection**: Designed for web browsers with cookies/sessions
- **Mobile Apps**: Don't use cookies, they use JWT Bearer tokens
- **@csrf.exempt**: Tells Flask to skip CSRF validation for this endpoint
- **@hybrid_auth**: Already supports both session and JWT authentication

### Files Modified
- ✅ `photovault/routes/photo.py` - Added @csrf.exempt to line 881

### Already Working Endpoints (for reference)
All these mobile endpoints already have @csrf.exempt:
- `/api/auth/login` - Mobile login
- `/api/auth/register` - Mobile registration  
- `/api/detect-and-extract` - Camera photo upload
- `/api/photos` - Gallery fetch
- `/api/dashboard` - Dashboard stats
- `/api/family/vaults` - Family vaults

## Expected Result
After deployment, voice memo uploads should work exactly like camera uploads - no errors, smooth upload with success confirmation.

## Verification
Check Railway logs for successful voice memo uploads:
```
🎤 === VOICE MEMO UPLOAD START ===
📱 User ID: X, Photo ID: Y
💾 Saved successfully: voice_X_timestamp.m4a (size bytes / size MB, duration: Xs)
✅ Voice memo X uploaded successfully
🎤 === VOICE MEMO UPLOAD COMPLETE ===
```
