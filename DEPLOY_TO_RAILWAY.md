# 🚀 Deploy Voice Memo Fix to Railway

## The Problem
Your iOS app connects to Railway (`https://web-production-535bd.up.railway.app`), but all the voice memo fixes are only on this Replit server. Railway still has the old broken code!

## Files That Need to be Deployed
1. ✅ `photovault/routes/mobile_api.py` - Voice memo API with @csrf.exempt and duration support
2. ✅ `StoryKeep-iOS/src/services/api.js` - Upload function with duration parameter
3. ✅ `StoryKeep-iOS/src/screens/PhotoDetailScreen.js` - Duration capture and display

## Deploy Steps

### Option 1: Use Replit Shell (Recommended)
Open the Shell tab in Replit and run:

```bash
git add photovault/routes/mobile_api.py
git add StoryKeep-iOS/src/services/api.js  
git add StoryKeep-iOS/src/screens/PhotoDetailScreen.js
git commit -m "Fix voice memo: add CSRF exempt and duration support"
git push origin main
```

### Option 2: Manual Git from Your Computer
If you have this repo cloned locally:

```bash
git pull origin main
git add photovault/routes/mobile_api.py StoryKeep-iOS/src/services/api.js StoryKeep-iOS/src/screens/PhotoDetailScreen.js
git commit -m "Fix voice memo: add CSRF exempt and duration support"
git push origin main
```

## After Pushing

1. **Wait 2-3 minutes** for Railway to auto-deploy
2. **Check Railway logs** to confirm deployment
3. **Test on iOS app**:
   - Open any photo
   - Tap Record under Voice Notes
   - Record for 5-10 seconds
   - Tap Stop
   - ✅ Should see "Voice note recorded successfully"
   - ✅ Duration should display (e.g., "00:08")

## What Changed

### Backend (`photovault/routes/mobile_api.py`)
```python
@csrf.exempt  # ← This fixes the 400 error!
@jwt_required()
def upload_voice_memo(photo_id):
    duration = request.form.get('duration', '0')  # ← Now accepts duration
    # ... rest of code
```

### iOS App (`StoryKeep-iOS/src/services/api.js`)
```javascript
uploadVoiceMemo: async (photoId, audioUri, duration) => {
  formData.append('duration', duration.toString());  // ← Sends duration
  // ...
}
```

### iOS App (`StoryKeep-iOS/src/screens/PhotoDetailScreen.js`)
```javascript
// Extract duration from recording
const status = await recording.getStatusAsync();
const durationSeconds = status.durationMillis ? status.durationMillis / 1000 : 0;

// Upload with duration
await voiceMemoAPI.uploadVoiceMemo(photo.id, uri, durationSeconds);
```

## Troubleshooting

### If Still Getting 400 Error After Deploy:
1. Check Railway deployment logs for errors
2. Verify Railway redeployed (check timestamp)
3. Clear iOS app cache and restart
4. Check Railway environment variables are set

### If Duration Shows 00:00:
- This means the recording duration wasn't captured
- Check iOS permissions for microphone
- Try recording longer (>3 seconds)

## Railway Environment Variables
Make sure these are set in Railway:
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Your JWT secret
- `FLASK_ENV=production`
- `SECRET_KEY` - Flask secret key

## Success Indicators ✅
- No 400 error when uploading voice memo
- Voice memo uploads successfully
- Duration displays correctly (e.g., "00:15" for 15 seconds)
- Can play and delete voice memos
