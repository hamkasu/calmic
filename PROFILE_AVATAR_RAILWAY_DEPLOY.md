# Profile Picture Upload - New Implementation Deployment Guide

## ✨ What Changed

**Complete rewrite** of the profile picture upload feature with a simpler, more reliable approach.

### Old System (DELETED):
- Endpoint: `/api/auth/profile/picture`
- Complex error handling, multiple validation steps
- Form field: `file`
- Issues: Database column conflicts, prone to errors

### New System (SIMPLE):
- Endpoint: `/api/profile/avatar`
- Minimal, clean implementation
- Form field: `image`
- Direct SQL updates to avoid model issues
- 300x300 resize for optimal performance
- **HEIC/HEIF support** for iOS devices (auto-converts to JPEG)

## 📝 Files Changed

1. **Backend:**
   - `photovault/routes/mobile_api.py` - New `/profile/avatar` endpoint
   - `photovault/__init__.py` - HEIC decoder registration
   - `requirements.txt` - Added `pillow-heif==1.1.1` for iOS image support

2. **iOS App:**
   - `StoryKeep-iOS/src/services/api.js` - New `uploadAvatar()` function
   - `StoryKeep-iOS/src/screens/ProfileScreen.js` - Updated to use new API
   - Fixed deprecation warning: `ImagePicker.MediaTypeOptions` → `['images']`

## 🚀 Deployment Steps

### Step 1: Ensure Database Column Exists

**Check if `profile_picture` column exists in Railway:**

```bash
railway login
railway link
railway connect postgres
```

In psql:
```sql
-- Check if column exists
\d user

-- If profile_picture is missing, add it:
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS profile_picture VARCHAR(500);

-- Exit
\q
```

**IMPORTANT:** If you see Stripe customer IDs (`cus_xxxxx`) in the `profile_picture` column:

```sql
-- Add stripe_customer_id column if missing
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);

-- Move Stripe data to correct column
UPDATE "user" SET stripe_customer_id = profile_picture WHERE profile_picture LIKE 'cus_%';

-- Clear profile_picture column
UPDATE "user" SET profile_picture = NULL WHERE profile_picture LIKE 'cus_%';
```

### Step 2: Push Code to Railway

```bash
# Stage all changes
git add photovault/routes/mobile_api.py
git add photovault/__init__.py
git add requirements.txt
git add StoryKeep-iOS/src/services/api.js
git add StoryKeep-iOS/src/screens/ProfileScreen.js
git add PROFILE_AVATAR_RAILWAY_DEPLOY.md

# Commit
git commit -m "Add HEIC support for iOS profile pictures with pillow-heif"

# Push to Railway
git push origin main
```

**Important:** Railway will automatically install `pillow-heif` from requirements.txt during deployment.

### Step 3: Wait for Railway Deployment

- Railway will automatically detect the push and deploy
- Check deployment logs in Railway dashboard
- Wait for "Deployed" status

### Step 4: Test in iOS App

1. Open StoryKeep app
2. Go to **Profile** screen
3. Tap the profile picture area
4. Select an image from your device
5. **Expected Results:**
   - ✅ Upload completes without errors
   - ✅ Success message appears
   - ✅ Profile picture displays immediately
   - ✅ Picture persists after app restart

## 🔧 How It Works

### Backend Flow:
```
1. Receive POST to /api/profile/avatar with 'image' field
2. Validate file type (png, jpg, jpeg, webp, heic, heif)
3. Register HEIC decoder (pillow-heif) for iOS images
4. Save to temp file with original extension
5. Convert HEIC → JPEG, resize to 300x300
6. Save final file to /uploads/{user_id}/
7. Clean up temp file
8. Update database with direct SQL (avoids model issues)
9. Return avatar_url for immediate display
```

**Supported Image Formats:**
- ✅ HEIC/HEIF (iOS default) → auto-converted to JPEG
- ✅ JPEG/JPG → optimized and resized
- ✅ PNG → converted to JPEG (no transparency)
- ✅ WebP → kept as WebP

### iOS Flow:
```
1. User picks image from library
2. Call authAPI.uploadAvatar(imageUri)
3. FormData with 'image' field
4. POST to /api/profile/avatar
5. Update local state with avatar_url
6. Display new profile picture
```

## ✅ Success Indicators

After deployment, you should see:

**In Railway Logs:**
```
[INFO] Avatar upload successful for user: hamka
```

**In iOS App:**
- No deprecation warnings
- No 500 errors
- Profile picture uploads and displays correctly
- Picture URL: `/uploads/{user_id}/avatar_timestamp.ext`

## 🐛 Troubleshooting

### Issue: Still getting 500 error
**Solution:** Check Railway database - ensure `profile_picture` column exists and doesn't contain Stripe IDs

### Issue: "No image file provided" error
**Solution:** The old `/api/auth/profile/picture` endpoint may still be cached. Clear app and try again.

### Issue: Picture uploads but doesn't display
**Solution:** Check that image URL matches pattern: `/uploads/{user_id}/avatar_*.{ext}`

## 📊 Database Schema

Correct `user` table schema:
```sql
CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    profile_picture VARCHAR(500),    -- For profile pictures
    stripe_customer_id VARCHAR(255), -- For Stripe data
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);
```

## 🎯 Expected Outcome

After successful deployment:
- ✅ Profile picture upload works reliably
- ✅ No database conflicts
- ✅ Clean, maintainable code
- ✅ No deprecation warnings
- ✅ Responsive user experience
