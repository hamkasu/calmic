# Deploy Enhancement & Colorization Endpoints to Railway

## Problem Fixed
The iOS app was getting 404 and 400 errors when trying to enhance or colorize photos because the endpoints didn't exist in the mobile API with JWT authentication.

## What Was Changed

### Added to `photovault/routes/mobile_api.py`:

1. **`/api/photos/<photo_id>/enhance` endpoint**
   - Uses JWT authentication (`@token_required`)
   - Applies image enhancement using the enhancer service
   - Updates `photo.edited_filename` with the enhanced version
   - Returns enhanced photo URL

2. **`/api/photos/<photo_id>/colorize` endpoint**
   - Uses JWT authentication (`@token_required`)
   - Checks if photo is grayscale before colorizing
   - Uses the colorizer service to add color
   - Updates `photo.edited_filename` with the colorized version
   - Returns colorized photo URL

## How to Deploy to Railway

### Option 1: Using Git (Recommended)

```bash
# 1. Stage the changes
git add photovault/routes/mobile_api.py

# 2. Commit the changes
git commit -m "Add mobile enhancement and colorization endpoints with JWT auth"

# 3. Push to GitHub
git push origin main
```

Railway will automatically detect the push and redeploy your app.

### Option 2: Manual Railway Deploy

1. Go to your Railway dashboard: https://railway.app/
2. Open your project
3. Click "Deploy" → "Deploy from GitHub"
4. Wait for the deployment to complete

## Verify After Deployment

1. Open the StoryKeep iOS app
2. Go to a photo
3. Tap "Enhance Photo"
4. Try "Auto Enhance" - should work without 400 error
5. Try "Colorize" on a black & white photo - should work without 404 error

## What the Endpoints Do

### Enhance Endpoint
- Accepts: `POST /api/photos/<photo_id>/enhance`
- Headers: `Authorization: Bearer <jwt_token>`
- Body: `{ "settings": {} }` (optional enhancement settings)
- Returns: Enhanced photo URL

### Colorize Endpoint  
- Accepts: `POST /api/photos/<photo_id>/colorize`
- Headers: `Authorization: Bearer <jwt_token>`
- Body: `{ "method": "auto" }` (auto, dnn, or basic)
- Returns: Colorized photo URL

## Error Messages Fixed
- ✅ "AxiosError: Request failed with status code 404" (colorize)
- ✅ "AxiosError: Request failed with status code 400" (enhance)

Both endpoints now properly authenticate via JWT and process photos correctly!
