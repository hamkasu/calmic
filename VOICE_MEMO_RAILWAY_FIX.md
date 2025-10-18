# Voice Memo iOS Fix - Railway Deployment Guide

## Issues Fixed ✅

### 1. **Missing Audio Format Support**
- **Problem**: iOS sends voice memos in `audio/m4a` format, but backend only accepted webm, wav, mp3, ogg, mp4, mpeg
- **Solution**: Added `audio/m4a` and `audio/x-m4a` to allowed audio types in `photovault/routes/photo.py` (line 898)

### 2. **Authentication Mismatch**  
- **Problem**: Voice memo endpoints used `@login_required` (session-based auth), but iOS app uses JWT tokens
- **Solution**: Changed all voice memo endpoints to use `@hybrid_auth` decorator that supports both session and JWT authentication

## Files Changed

### `photovault/routes/photo.py`
1. **Line 37**: Added import for `hybrid_auth`
   ```python
   from photovault.utils.jwt_auth import hybrid_auth
   ```

2. **Line 872-873**: Changed POST upload endpoint
   ```python
   @photo_bp.route('/api/photos/<int:photo_id>/voice-memos', methods=['POST'])
   @hybrid_auth
   def upload_voice_memo(current_user, photo_id):
   ```

3. **Line 898**: Added iOS audio formats
   ```python
   allowed_audio_types = {'audio/webm', 'audio/wav', 'audio/mp3', 'audio/ogg', 'audio/mp4', 'audio/mpeg', 'audio/m4a', 'audio/x-m4a'}
   ```

4. **Line 981-982**: Changed GET voice memos endpoint
   ```python
   @photo_bp.route('/api/photos/<int:photo_id>/voice-memos', methods=['GET'])
   @hybrid_auth
   def get_voice_memos(current_user, photo_id):
   ```

5. **Line 1021-1022**: Changed GET audio file endpoint
   ```python
   @photo_bp.route('/api/voice-memos/<int:memo_id>', methods=['GET'])
   @hybrid_auth
   def serve_voice_memo(current_user, memo_id):
   ```

6. **Line 1050-1051**: Changed PUT update endpoint
   ```python
   @photo_bp.route('/api/voice-memos/<int:memo_id>', methods=['PUT'])
   @hybrid_auth
   def update_voice_memo(current_user, memo_id):
   ```

7. **Line 1095-1096**: Changed DELETE endpoint
   ```python
   @photo_bp.route('/api/voice-memos/<int:memo_id>', methods=['DELETE'])
   @hybrid_auth
   def delete_voice_memo(current_user, memo_id):
   ```

## Deploy to Railway

### Prerequisites
- Git configured with Railway remote
- Railway CLI installed (optional) OR GitHub integration

### Option 1: Deploy via Git Push

1. **Stage the changes**:
   ```bash
   git add photovault/routes/photo.py
   git add replit.md
   git add VOICE_MEMO_RAILWAY_FIX.md
   ```

2. **Commit with descriptive message**:
   ```bash
   git commit -m "Fix: Add iOS m4a audio format support and JWT auth for voice memos"
   ```

3. **Push to Railway**:
   ```bash
   git push railway main
   ```
   
   Or if using GitHub integration:
   ```bash
   git push origin main
   ```

4. **Monitor deployment**:
   - Go to Railway dashboard: https://railway.app
   - Check deployment logs for your PhotoVault app
   - Wait for "Build successful" and "Deployment live" messages

### Option 2: Deploy via Railway CLI

1. **Login to Railway**:
   ```bash
   railway login
   ```

2. **Link project** (if not already linked):
   ```bash
   railway link
   ```

3. **Deploy**:
   ```bash
   railway up
   ```

## Testing After Deployment

### 1. Test Voice Memo Recording on iOS
1. Open StoryKeep app on your phone
2. Go to any photo in Gallery
3. Tap on the photo to open Photo Detail
4. Scroll down to "Voice Notes" section
5. Tap the red "Record" button
6. Speak a voice memo
7. Tap "Stop" when done
8. You should see "Voice memo uploaded successfully"
9. The memo should appear in the list with a play button

### 2. Test Voice Memo Playback
1. In the Voice Notes section, find your recorded memo
2. Tap the play button (▶️)
3. The audio should play successfully
4. You should see a pause button while playing

### 3. Test Voice Memo Delete
1. In the Voice Notes section, tap the delete button (🗑️) on a memo
2. Confirm deletion
3. The memo should be removed from the list

## Expected Results

✅ **Before Fix**: 
- Recording fails with "Failed to save voice note"
- Error shows: "AxiosError: Request failed with status code 400"

✅ **After Fix**:
- Recording works and shows "Voice memo uploaded successfully"
- Playback works with download-then-play pattern
- Delete works and removes memo from server

## Rollback Instructions

If issues occur, rollback to previous version:

```bash
git revert HEAD
git push railway main
```

## Additional Notes

- **Splash Screen Sound**: Currently disabled until audio file added (see `SPLASH_SOUND_SETUP.md`)
- **Expo AV Deprecation**: Warning about expo-av is expected in SDK 54, feature still works
- **Local Testing**: Changes work on local Replit server at port 5000
- **Production**: Must deploy to Railway for iOS app to access the API

## Support

If voice memos still don't work after deployment:
1. Check Railway deployment logs for errors
2. Verify the deployment completed successfully
3. Try logout/login on the iOS app to refresh JWT token
4. Check network connection on your phone
