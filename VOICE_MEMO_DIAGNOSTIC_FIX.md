# Voice Memo Diagnostic Fix for Railway

## What Was Changed

### Enhanced Logging
Added comprehensive diagnostic logging to the voice memo upload endpoint (`/api/photos/<photo_id>/voice-memos`) that will help us identify exactly where the upload is failing on Railway.

**New logging includes:**
- 🎤 Upload start/complete markers
- 📱 User ID and Photo ID
- 📦 Request files, form data, and headers
- 📦 Content-Length and Content-Type
- ⚙️ Maximum upload size configuration
- 📄 Audio file details (filename, content-type)
- 💾 File save location and size
- ✅/❌ Success/failure with detailed error types

### New Diagnostic Endpoint
Added `/api/voice-memo-test` endpoint that the iOS app can call to verify:
- Maximum upload size configuration
- Upload folder paths
- Directory creation permissions
- User has photos to attach voice memos to

## How to Test on iOS with Railway

### Step 1: Call the Diagnostic Endpoint (Optional)
Before recording, you can test the configuration by calling:
```
GET https://web-production-535bd.up.railway.app/api/voice-memo-test
```
with your JWT token in the Authorization header.

### Step 2: Record and Upload a Voice Memo
1. Open the StoryKeep iOS app
2. Navigate to any photo detail screen
3. Tap the microphone button to record
4. Record for 5-10 seconds
5. Stop the recording
6. Upload will happen automatically

### Step 3: Check Railway Logs
After attempting to upload, immediately check your Railway logs:

1. Go to Railway dashboard
2. Click on your PhotoVault service
3. Go to "Deployments" → "Logs"
4. Look for the emoji markers:
   - `🎤 === VOICE MEMO UPLOAD START ===` - Upload started
   - `✅ Voice memo X uploaded successfully` - Upload worked!
   - `❌ === VOICE MEMO UPLOAD FAILED ===` - Upload failed (shows error details)

### Step 4: Identify the Issue
The enhanced logging will show you exactly where it fails:

**Common Issues:**
1. **"Request entity too large"** → File size exceeds MAX_CONTENT_LENGTH (50MB limit)
2. **"No audio file provided"** → iOS app not sending the 'audio' field correctly
3. **"Photo not found"** → Photo ID doesn't exist or doesn't belong to user
4. **Permission errors** → Directory creation fails on Railway
5. **Database errors** → VoiceMemo model or database issue

## Deployment to Railway

### Option 1: Via Git Push
```bash
# Commit the changes
git add photovault/routes/mobile_api.py
git commit -m "Add enhanced voice memo diagnostic logging"

# Push to your repository
git push origin main
```

Railway will automatically deploy the changes.

### Option 2: Via Railway CLI
```bash
# Deploy directly
railway up
```

### Option 3: Redeploy from Railway Dashboard
1. Go to Railway dashboard
2. Click on your PhotoVault service
3. Click "Deploy" → "Redeploy"

## What to Share After Testing

After you test on the iOS app, share the Railway log output that includes:
- The `🎤 === VOICE MEMO UPLOAD START ===` section
- Any error messages with `❌`
- The complete error traceback if it fails

This will tell us exactly what's wrong with the voice memo upload on Railway!

## Expected Working Output

If it works, you should see in the logs:
```
🎤 === VOICE MEMO UPLOAD START ===
📱 User ID: 1, Photo ID: 123
📦 Request files: ['audio']
📦 Request form: {'duration': '10.5'}
⚙️ Max upload size: 50.00 MB
⏱️ Recording duration: 10.5 seconds
📄 Audio file: voice-memo.m4a
📄 Content-Type: audio/m4a
📁 Save directory: uploads/voice_memos/1
💾 Saving to: uploads/voice_memos/1/voice_1_20251011_120000_abc123.m4a
💾 Saved successfully: voice_1_20251011_120000_abc123.m4a (1234567 bytes / 1.18 MB, duration: 10.5s)
✅ Voice memo 42 uploaded successfully
🎤 === VOICE MEMO UPLOAD COMPLETE ===
```

## Current Configuration
- **Max Upload Size:** 50 MB (set in config.py)
- **Recording Quality:** MEDIUM_QUALITY (iOS app)
- **Audio Format:** m4a
- **CSRF Protection:** Exempt for mobile API
- **Authentication:** JWT token required
