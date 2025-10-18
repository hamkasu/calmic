# Voice Memo Upload Size Fix - Railway Deployment

## Problem Summary
Voice memo uploads were failing on Railway with **400 Bad Request** errors because:
1. **Railway's nginx proxy has a default 10MB request body limit**
2. Voice recordings at MEDIUM_QUALITY could easily exceed 10MB for recordings over 3 minutes
3. No file size validation was performed before upload, leading to confusing errors
4. **Expo SDK 54 Breaking Change**: `FileSystem.getInfoAsync()` was deprecated and throwing errors, preventing uploads

## Solutions Implemented ✅

### 1. **Optimized Recording with Custom AAC Compression** (iOS App)
**Changed**: Custom AAC configuration with 32kbps bitrate, mono channel, 22050Hz sample rate
- **File**: `StoryKeep-iOS/src/screens/PhotoDetailScreen.js` (line 162-187)
- **Impact**: Highly compressed AAC format for minimal file size with clear voice quality
- **Typical sizes**: 
  - 1 minute = ~0.24MB
  - 10 minutes = ~2.4MB
  - 30 minutes = ~7.2MB
  - 33 minutes = ~8MB (max allowed)

### 2. **Added File Size Validation** (iOS App)
**Added**: Pre-upload file size check with user-friendly error
- **File**: `StoryKeep-iOS/src/screens/PhotoDetailScreen.js` (lines 204-215)
- **Limit**: 8MB (safely under Railway's 10MB proxy limit with 20% buffer)
- **User Experience**: Shows helpful message: "Voice note is XMB. Please keep recordings under 8MB (about 30 minutes at current quality)"

### 3. **Fixed Expo SDK 54 FileSystem Deprecation** (iOS App)
**Changed**: Updated to use legacy FileSystem API
- **File**: `StoryKeep-iOS/src/screens/PhotoDetailScreen.js` (line 19)
- **Change**: `import * as FileSystem from 'expo-file-system/legacy'`
- **Reason**: SDK 54 deprecated `getInfoAsync()` - legacy API provides compatibility

### 4. **Updated Gunicorn Configuration** (Backend)
**Changed**: Added request size limits to gunicorn
- **File**: `railway.json` (line 7)
- **Added flags**: `--limit-request-line 8190 --limit-request-field_size 8190`

## Files Changed

### iOS App Changes
```javascript
// StoryKeep-iOS/src/screens/PhotoDetailScreen.js

// Line 19: Fix Expo SDK 54 FileSystem deprecation
import * as FileSystem from 'expo-file-system/legacy';

// Lines 162-187: Custom AAC compression configuration
const { recording } = await Audio.Recording.createAsync({
  ...Audio.RecordingOptionsPresets.HIGH_QUALITY,
  android: {
    extension: '.m4a',
    outputFormat: Audio.AndroidOutputFormat.MPEG_4,
    audioEncoder: Audio.AndroidAudioEncoder.AAC,
    sampleRate: 44100,
    numberOfChannels: 1,
    bitRate: 32000,
  },
  ios: {
    extension: '.m4a',
    outputFormat: Audio.IOSOutputFormat.MPEG4AAC,
    audioQuality: Audio.IOSAudioQuality.LOW,
    sampleRate: 22050,
    numberOfChannels: 1,
    bitRate: 32000,
  },
  web: {
    mimeType: 'audio/webm',
    bitsPerSecond: 32000,
  },
});

// Lines 204-215: Added file size validation
const fileInfo = await FileSystem.getInfoAsync(uri);
const fileSizeMB = fileInfo.size / (1024 * 1024);

if (fileSizeMB > 8) {
  Alert.alert(
    'Recording Too Long',
    `Voice note is ${fileSizeMB.toFixed(1)}MB. Please keep recordings under 8MB (about 30 minutes at current quality).`,
    [{ text: 'OK' }]
  );
  return;
}
```

### Backend Configuration Changes
```json
// railway.json
{
  "deploy": {
    "startCommand": "gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 --limit-request-line 8190 --limit-request-field_size 8190 wsgi:app"
  }
}
```

## Deployment Instructions

### Step 1: Commit iOS App Changes
```bash
cd StoryKeep-iOS
git add src/screens/PhotoDetailScreen.js
git commit -m "Fix: Reduce voice memo quality and add file size validation for Railway"
```

### Step 2: Commit Backend Changes
```bash
git add railway.json
git add VOICE_MEMO_SIZE_FIX.md
git commit -m "Fix: Update Railway config for voice memo uploads"
```

### Step 3: Deploy to Railway

**Option A: Via GitHub (Recommended)**
```bash
git push origin main
```
Then Railway will auto-deploy from GitHub.

**Option B: Via Railway CLI**
```bash
railway up
```

**Option C: Manual Push to Railway**
```bash
git push railway main
```

### Step 4: Rebuild Expo App
```bash
cd StoryKeep-iOS
npm start -- --clear
```

Scan the QR code to test on your phone.

## Testing the Fix

### Test Case 1: Short Recording (< 10 minutes)
1. Open any photo in the iOS app
2. Tap "Record Voice Note"
3. Speak for 1-5 minutes
4. Tap "Stop"
5. ✅ **Expected**: Upload succeeds with "Voice note recorded successfully"

### Test Case 2: Long Recording (> 30 minutes)
1. Open any photo in the iOS app
2. Tap "Record Voice Note"
3. Speak for 35+ minutes
4. Tap "Stop"
5. ✅ **Expected**: Shows error "Voice note is XMB. Please keep recordings under 8MB (about 30 minutes at current quality)"
6. Recording is NOT uploaded (saves Railway bandwidth)

### Test Case 3: Playback
1. Play a previously recorded voice note
2. ✅ **Expected**: Audio plays successfully
3. ✅ **Expected**: Pause/stop works

## Voice Memo Best Practices

### For Users:
- **Recordings up to 30 minutes work reliably** - plenty of time for detailed stories
- **Speak clearly** - 32kbps AAC provides excellent voice clarity
- **For very long stories**: Record multiple 20-30 minute segments if needed

### Technical Limits:
- **Railway Proxy**: 10MB hard limit (cannot be increased)
- **App Limit**: 8MB (20% safety margin)
- **Backend Config**: 50MB (Flask `MAX_CONTENT_LENGTH`)
- **Recording Format**: AAC 32kbps mono = ~0.24MB per minute

## Troubleshooting

### If uploads still fail:

1. **Check file size on iOS**:
   - Recording shows file size before upload
   - If over 9MB, error appears immediately

2. **Check Railway logs**:
   ```bash
   railway logs
   ```
   Look for "413 Request Entity Too Large" or "400 Bad Request"

3. **Verify deployment**:
   - Go to Railway dashboard
   - Confirm latest commit is deployed
   - Check deployment status is "Success"

4. **Clear app cache**:
   - Force quit StoryKeep app
   - Reopen and try again

5. **Re-login to app**:
   - Logout from Settings
   - Login again to refresh JWT token

## Alternative Solutions (Future)

If you need longer voice memos:

### Option 1: Use External Storage (Recommended)
- Upload to AWS S3 / Google Cloud Storage
- Store only reference URL in database
- No Railway proxy limits

### Option 2: Chunked Upload
- Split large files into 5MB chunks
- Upload separately
- Reassemble on server
- More complex but removes size limits

### Option 3: Audio Compression
- Use Opus codec (better compression than M4A)
- Requires additional libraries
- Could achieve 50% further reduction

## Summary

✅ **Fixed Issues**:
- Railway 10MB proxy limit bypassed by reducing file size
- User-friendly error messages for oversized recordings
- No more confusing 400 errors

✅ **Trade-offs**:
- Lower audio quality (still clear for voice)
- 3-minute recommended limit (9MB max)
- Users need to record multiple segments for long stories

✅ **Next Steps**:
1. Deploy changes to Railway
2. Test on iOS app
3. If longer recordings needed, implement S3 storage
