# Deploy Photo Detection Feature to Railway

## 🚨 Issue
The iOS app photo detection/cropping feature is not working on Railway because the `/api/detect-and-extract` endpoint only exists in your **local Replit code** and hasn't been deployed to **Railway production** yet.

## ✅ Solution
Push your local code to GitHub so Railway can automatically deploy the new endpoint.

## 📋 Step-by-Step Deployment Instructions

### Step 1: Check Current Git Status
```bash
git status
```

### Step 2: Stage All Changes
```bash
git add .
```

### Step 3: Commit Your Changes
```bash
git commit -m "Add photo detection and extraction endpoint for iOS Digitizer feature"
```

### Step 4: Push to GitHub
```bash
git push origin main
```
(Or use `master` if that's your main branch name)

### Step 5: Verify Railway Deployment
1. Go to your Railway dashboard: https://railway.app
2. Select your PhotoVault project
3. Go to the "Deployments" tab
4. Wait for the new deployment to complete (usually 2-5 minutes)
5. Look for a green checkmark ✅ indicating successful deployment

### Step 6: Test in iOS App
1. Open the StoryKeep iOS app
2. Go to the Digitizer (camera)
3. Take a photo of a physical photograph
4. The app should now automatically detect and crop the photo

## 🔍 What This Deployment Includes

The `/api/detect-and-extract` endpoint that:
- ✅ Accepts uploaded images from iOS camera
- ✅ Uses OpenCV AI to detect photo boundaries
- ✅ Automatically crops and extracts photos
- ✅ Applies perspective correction
- ✅ Saves extracted photos to your gallery
- ✅ Handles cases where no photos are detected

## 🐛 Troubleshooting

### If deployment fails:
1. Check Railway build logs for errors
2. Verify all dependencies are in `requirements.txt`
3. Check that OpenCV packages are installed:
   - opencv-python-headless==4.12.0.88
   - opencv-contrib-python-headless==4.12.0.88

### If detection still doesn't work after deployment:
1. Check Railway logs: `railway logs`
2. Look for errors like:
   - "No module named 'cv2'" → OpenCV not installed
   - "PhotoDetector not found" → Import error
   - "No image file provided" → iOS app sending wrong format

### Test the endpoint directly:
```bash
curl -X POST https://web-production-535bd.up.railway.app/api/detect-and-extract \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "image=@/path/to/photo.jpg"
```

## 📝 Files Deployed

These files contain the detection feature:
- `photovault/routes/mobile_api.py` - Main API endpoint (line 654)
- `photovault/utils/photo_detection.py` - Photo detection logic
- `photovault/utils/file_handler.py` - File validation utilities

## ⏱️ Expected Timeline
- **Commit & Push**: 1 minute
- **Railway Build**: 2-5 minutes  
- **Total Time**: ~5 minutes until feature is live

---

**After deployment, your iOS Digitizer feature will work on Railway production! 📸**
