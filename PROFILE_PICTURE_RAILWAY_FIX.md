# Profile Picture Upload Fix for Railway

## 🐛 Issue
Profile picture upload is failing with error 500 on Railway because the `profile_picture` column is missing from the User table in the production database.

## 🔍 Root Cause
- The User model has a `profile_picture` column defined in the code
- The initial database migration did NOT include this column
- Railway's production database is missing the `profile_picture` column
- When the app tries to save `current_user.profile_picture = filename`, it fails with a database error

## ✅ Solution
A new migration has been created to add the `profile_picture` column to the User table.

## 📝 Deployment Steps

### Step 1: Push Migration to GitHub
```bash
git add migrations/versions/20251013_add_profile_picture_to_user.py
git commit -m "Add profile_picture column migration for user profile photos"
git push origin main
```

### Step 2: Run Migration on Railway
After Railway automatically deploys the new code:

**Option A: Using Railway CLI (Recommended)**
```bash
railway run flask db upgrade
```

**Option B: Using Railway Dashboard**
1. Go to your Railway project dashboard
2. Click on your service (web-production-535bd)
3. Go to the "Variables" tab
4. Add a temporary variable to trigger migration:
   - Name: `RUN_MIGRATION`
   - Value: `true`
5. Click "Deploy" to redeploy
6. After deployment succeeds, remove the `RUN_MIGRATION` variable

**Option C: Manual SQL (If migration doesn't work)**
1. Go to Railway Dashboard → Your Database
2. Click "Query" tab
3. Run this SQL:
```sql
ALTER TABLE "user" ADD COLUMN profile_picture VARCHAR(500);
```

### Step 3: Verify Fix
1. Open the StoryKeep iOS app
2. Go to Profile screen
3. Tap the profile picture area to upload a photo
4. Select an image from your device
5. Verify that:
   - ✅ Upload completes successfully
   - ✅ Success message appears
   - ✅ Profile picture displays correctly
   - ✅ No 500 error occurs

## 📊 What This Migration Does
```python
# Adds the profile_picture column to the user table
ALTER TABLE "user" 
ADD COLUMN profile_picture VARCHAR(500) NULL;
```

This allows the User model to store the profile picture filename, which is used to:
- Display user profile pictures in the iOS app
- Store profile photos in `/uploads/{user_id}/profile_{user_id}_*.jpg`
- Update and delete old profile pictures when new ones are uploaded

## 🔧 Files Changed
1. `migrations/versions/20251013_add_profile_picture_to_user.py` (NEW)
   - Migration to add profile_picture column

## 🎯 Expected Result
After deploying this fix, users will be able to:
- ✅ Upload profile pictures without errors
- ✅ See their profile pictures in the Profile screen
- ✅ Update their profile pictures at any time
- ✅ Have old profile pictures automatically deleted when uploading new ones
