# 🔧 Railway Profile Picture Fix - Deployment Guide

## 📋 Problem Summary
iOS app shows "Failed to save photo" when downloading profile pictures, and profile picture upload shows 500 error.

**Root Causes:**
1. ❌ **Missing Database Column**: Railway database doesn't have `profile_picture` column in User table
2. ❌ **Code Error**: `gallery.py` tried to access non-existent `user.profile_picture` attribute causing AttributeError

**Error on Railway:**
```python
AttributeError: 'User' object has no attribute 'profile_picture'
```

---

## ✅ Fixes Applied (Local)

### 1. **Safe Attribute Access** ✅
**File**: `photovault/routes/gallery.py` (Line 350)
- Changed from: `user.profile_picture == filename`
- Changed to: `getattr(user, 'profile_picture', None)` - Safe check that won't crash if column is missing

### 2. **Database Migration** ✅
**File**: `migrations/versions/20251013_add_profile_picture_to_user.py`
- Adds `profile_picture` column to User table (String, 500 chars, nullable)

---

## 🚀 Railway Deployment Steps

### Step 1: Push Code Changes to GitHub
```bash
# From your local machine (not Replit)
git add photovault/routes/gallery.py
git add migrations/versions/20251013_add_profile_picture_to_user.py
git commit -m "Fix profile picture - safe attribute access and add migration"
git push origin main
```

### Step 2: Run Database Migration on Railway
After Railway auto-deploys your code, you need to run the migration:

**Option A: Via Railway CLI (Recommended)**
```bash
# Connect to Railway project
railway login
railway link

# Run migration
railway run flask db upgrade
```

**Option B: Via Railway Dashboard**
1. Go to Railway Dashboard → Your Project
2. Click on **Variables** tab
3. Click **+ New Variable**
4. Add: `FLASK_APP=main.py`
5. Go to **Deployments** tab
6. Click **⋯** (three dots) on latest deployment
7. Select **Run Command**
8. Enter: `flask db upgrade`
9. Click **Run**

**Option C: Via Railway Shell**
1. Go to Railway Dashboard → Your Project
2. Click on your service
3. Click **Shell** tab
4. Run:
```bash
flask db upgrade
```

### Step 3: Verify Migration Success
Check the Railway logs for:
```
INFO  [alembic.runtime.migration] Running upgrade ... -> 20251013_profile_pic, add profile_picture to user table
```

### Step 4: Test Profile Picture on iOS App
1. **Upload Profile Picture**:
   - Go to Profile screen
   - Tap camera icon
   - Select photo from library
   - Confirm "Success - Profile picture updated" appears
   - ✅ Should NOT show "Download failed with status: 500"

2. **View Profile Picture**:
   - Close and reopen app
   - Profile picture should display
   - No gray placeholder

3. **Download Photo**:
   - Go to any photo detail screen
   - Tap "Download" button
   - ✅ Should download successfully without "Failed to save photo" error

---

## 📊 Database Schema Change

**Before:**
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80),
    email VARCHAR(120),
    password_hash VARCHAR(255)
    -- No profile_picture column ❌
);
```

**After:**
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80),
    email VARCHAR(120),
    password_hash VARCHAR(255),
    profile_picture VARCHAR(500)  -- ✅ New column added
);
```

---

## 🔍 How to Verify Fix

### Check Database Column Exists
```bash
# On Railway shell
flask shell
>>> from photovault.models import User
>>> User.__table__.columns.keys()
['id', 'username', 'email', 'password_hash', 'profile_picture']  # ✅ Should see profile_picture
```

### Check Logs for Errors
After deployment, check Railway logs for:
- ✅ **No AttributeError** on profile picture access
- ✅ **No 500 errors** on `/uploads/1/avatar_*.jpg` requests
- ✅ **Successful profile picture updates** logged

---

## 🎯 Expected Behavior After Fix

### ✅ Profile Picture Upload
```
iOS App → Upload Photo → Railway receives request
→ Saves to users/1/avatar_20251014_062456.jpg
→ Updates user.profile_picture = "avatar_20251014_062456.jpg"
→ Returns 200 Success
```

### ✅ Profile Picture Display
```
iOS App → Requests /uploads/1/avatar_20251014_062456.jpg
→ Railway checks: getattr(user, 'profile_picture', None)
→ Finds file in App Storage
→ Returns image with 200 OK
```

### ✅ Photo Download
```
iOS App → Download Photo → Railway serves file
→ No AttributeError (safe getattr check)
→ Returns image successfully
```

---

## 📝 Code Changes Summary

### `photovault/routes/gallery.py`
```python
# BEFORE (Line 346) - ❌ Crashes on Railway
if user and user.profile_picture == filename:
    ...

# AFTER (Line 350) - ✅ Safe on all environments
user_profile_pic = getattr(user, 'profile_picture', None) if user else None
if user and user_profile_pic == filename:
    ...
```

---

## 🐛 Troubleshooting

### Issue: Migration fails with "column already exists"
**Solution**: Column was manually added earlier. Mark migration as applied:
```bash
railway run flask db stamp 20251013_profile_pic
```

### Issue: Still getting AttributeError after deployment
**Solution**: 
1. Verify code was pushed to GitHub
2. Check Railway deployment logs show latest commit hash
3. Force redeploy if needed

### Issue: Profile picture shows but won't download
**Solution**: Check App Storage permissions and file upload was successful

---

## ✅ Success Checklist

- [ ] Code pushed to GitHub (`gallery.py` with safe attribute access)
- [ ] Railway auto-deployed latest code
- [ ] Migration run successfully (`flask db upgrade`)
- [ ] Database has `profile_picture` column
- [ ] iOS app can upload profile picture (no 500 error)
- [ ] iOS app can view profile picture (no placeholder)
- [ ] iOS app can download photos (no "Failed to save" error)
- [ ] No AttributeError in Railway logs

---

## 📌 Notes

- **Local Environment**: Already has the migration applied and working
- **Railway Environment**: Needs migration to be run manually
- **The Fix**: Makes code backward-compatible - works with or without the column
- **Safety**: Uses `getattr()` with default value to prevent crashes

---

## 🎉 After Successful Deployment

Your iOS app will:
1. ✅ Upload profile pictures without errors
2. ✅ Display profile pictures correctly
3. ✅ Download photos without "Failed to save" errors
4. ✅ Work seamlessly with Railway production database

**Estimated Time**: 5-10 minutes (code push + migration + testing)
