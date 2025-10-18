# Profile Picture Database Query Fix - Railway Deployment Guide

## 🔍 Issue Discovered
The iOS app was showing `profile_picture: null` in the API response, even though the database `profile_picture` column contained the filename `avatar_20251014_083812.jpg`.

### Root Cause Analysis:
The backend API was using `getattr(current_user, 'profile_picture', None)` which returned `None` because:
- The SQLAlchemy User model doesn't have the `profile_picture` attribute defined
- Even though the database column exists, SQLAlchemy can't access it without the model definition
- This happens when migrations add columns but the model code isn't updated

## ✅ Solution Applied

### Changed Approach:
**Before** (Using SQLAlchemy getattr - BROKEN):
```python
profile_picture = getattr(current_user, 'profile_picture', None)
# Returns None even though database has value
```

**After** (Direct SQL Query - WORKS):
```python
result = db.session.execute(
    db.text("SELECT profile_picture FROM \"user\" WHERE id = :user_id"),
    {"user_id": current_user.id}
).fetchone()

profile_picture = result[0] if result and result[0] else None
# Returns actual value from database: "avatar_20251014_083812.jpg"
```

### Why This Works:
- Bypasses SQLAlchemy model completely
- Queries the database column directly using raw SQL
- Works regardless of whether the model has the attribute defined
- Reads the actual stored value in the `profile_picture` column

## 📝 Changes Made

### Modified File:
- `photovault/routes/mobile_api.py`

### Endpoint Changed:
- `GET /api/auth/profile`

### Added Features:
1. **Direct Database Query**: Uses `db.text()` to execute raw SQL
2. **Comprehensive Logging**: 
   - `📸 Profile picture from database for user {username}: {value}`
   - `✅ Built profile picture URL: {url}`
   - `⚠️ No profile picture in database for user {username}`
3. **Error Tracking**: Detailed traceback logging for debugging

## 🚂 Railway Deployment

### 1. Backend Changes (Apply to Railway)
```bash
# Push the backend changes to GitHub
git add photovault/routes/mobile_api.py
git commit -m "Fix: Query profile_picture directly from database to bypass model limitation"
git push origin main

# Railway will auto-deploy the changes
```

### 2. iOS App Changes (Already Applied)
The iOS Dashboard code is already updated to:
- Fetch fresh profile data on every load
- Use unique filenames to avoid cache
- Show loading spinner during fetch

No additional iOS changes needed.

## 🧪 Testing Steps

### Test on Local Replit (Already Working):
```bash
# 1. Check server logs when API is called
# Look for: "📸 Profile picture from database for user hamka: avatar_20251014_083812.jpg"

# 2. Test the endpoint directly
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5000/api/auth/profile

# Expected response:
{
  "username": "hamka",
  "email": "hamka.suleiman@calmic.com.my",
  "profile_picture": "/uploads/USER_ID/avatar_20251014_083812.jpg",
  "subscription_plan": "standard",
  "created_at": "2025-10-05T13:02:23.122025"
}
```

### Test on Railway Production:
1. **After deployment, reload the iOS app**
2. **Login and go to Dashboard**
3. **Check Expo console logs**:
   - Should show: `Fresh profile data from database: {"profile_picture": "/uploads/...", ...}`
   - Should NOT show: `"profile_picture": null`
4. **Verify profile picture appears** on Dashboard header
5. **Navigate to Profile screen** - profile picture should also show
6. **Return to Dashboard** - profile picture should remain visible

## 📊 Expected Behavior After Fix

### ✅ Working Correctly:
- API returns actual profile_picture value from database
- Dashboard shows profile picture from database
- Profile screen shows profile picture (already working)
- Logs show database value being fetched and URL being built

### 📋 Log Examples (Success):
```
📸 Profile picture from database for user hamka: avatar_20251014_083812.jpg
✅ Built profile picture URL: /uploads/8/avatar_20251014_083812.jpg
```

### 🔴 Error Indicators (Need to Fix):
```
⚠️ No profile picture in database for user hamka
```
This means the database column is actually empty.

## 🎯 How It Works Now

### Backend Flow:
1. iOS app calls `/api/auth/profile` with JWT token
2. Backend extracts user_id from token
3. Executes SQL query: `SELECT profile_picture FROM "user" WHERE id = user_id`
4. Gets actual value from database (e.g., `avatar_20251014_083812.jpg`)
5. Builds URL: `/uploads/{user_id}/{filename}`
6. Returns JSON with profile_picture URL

### iOS Flow:
1. Dashboard calls `authAPI.getProfile()`
2. Receives profile_picture URL from API
3. Downloads image with auth token using FileSystem
4. Displays cached image

## 🔧 Why Previous Approach Failed

### SQLAlchemy Model Limitation:
```python
# User model doesn't have this attribute defined
class User(db.Model):
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
    # profile_picture = db.Column(db.String(255))  <- MISSING!
```

Even though the database column exists, `getattr(user, 'profile_picture', None)` returns `None` because the attribute isn't in the model definition.

### Raw SQL Solution:
Bypasses the model entirely and reads directly from the database table, working regardless of model definition.

## 📈 Summary

**Issue**: API returned `null` for profile_picture despite database having value  
**Root Cause**: SQLAlchemy model missing profile_picture attribute definition  
**Solution**: Direct SQL query bypasses model and reads column value  
**Status**: ✅ Fixed locally, ready for Railway deployment  
**Next Step**: Push to GitHub and test on Railway production  

The fix is backward-compatible and works whether the column exists in the model or not.
