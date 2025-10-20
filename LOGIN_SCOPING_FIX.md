# Railway Production Deployment Fix

## Problems Fixed

### 1. Login/Registration Crash - Variable Scoping Issue
Login and registration were crashing on Railway with this error:
```
NameError: cannot access free variable 'User' where it is not associated with a value in enclosing scope
```

### 2. Missing AI Package - Import Error
Server failing to start on Railway with this error:
```
ModuleNotFoundError: No module named 'google.generativeai'
```

## Root Causes

### Issue 1: Variable Scoping
Python nested functions inside route handlers were trying to access models (`User`, `PasswordResetToken`, `db`) from the outer scope, causing a scoping error when the code was deployed to Railway.

### Issue 2: Wrong Package Name
The `requirements.txt` had the wrong package name: `google-genai` instead of `google-generativeai`

## Solutions

### Fix 1: Variable Scoping
Fixed all nested functions in `photovault/routes/auth.py` by importing models **inside** each nested function instead of relying on outer scope imports.

### Fix 2: AI Package Name
Changed `google-genai` to `google-generativeai` in `requirements.txt` (line 65)

## Files Changed
- `photovault/routes/auth.py` - Fixed nested function scoping
- `requirements.txt` - Fixed AI package name

## Detailed Changes

### Auth Route Changes

1. **Login route** - `find_user()` function (line 68-72):
   - Added: `from photovault.models import User as UserModel`
   - Changed references from `User` to `UserModel`

2. **Register route** - `check_existing_user()` function (line 236-240):
   - Added: `from photovault.models import User as UserModel`
   - Changed references from `User` to `UserModel`

3. **Register route** - `create_user()` function (line 262-271):
   - Added: `from photovault.models import User as UserModel, db as database`
   - Changed references accordingly

4. **Forgot Password route** - `find_user_by_email()` function (line 424-426):
   - Converted lambda to named function
   - Added: `from photovault.models import User as UserModel`

5. **Forgot Password route** - `create_reset_token()` function (line 441-451):
   - Added: `from photovault.models import PasswordResetToken as ResetToken, db as database`
   - Changed references accordingly

## Testing
✅ Tested locally on Replit - server starts successfully
✅ All authentication routes working correctly
✅ Ready for Railway deployment

## Deployment to Railway

### Step 1: Push to GitHub
```bash
git add photovault/routes/auth.py requirements.txt
git commit -m "Fix Railway crashes: scoping issue + AI package name"
git push origin main
```

### Step 2: Verify on Railway
1. Railway will automatically detect the push and deploy
2. Wait for deployment to complete
3. Test login at: https://storykeep.calmic.com.my/auth/login
4. Test registration at: https://storykeep.calmic.com.my/auth/register

### Step 3: Test Mobile App
1. Open StoryKeep iOS app
2. Try logging in with existing credentials
3. Try registering a new account
4. Both should now work without 500 Internal Server Error

## Expected Result
- ✅ Web login works
- ✅ Web registration works
- ✅ Mobile login works
- ✅ Mobile registration works
- ✅ Password reset works
- ✅ No more NameError exceptions

## Technical Details
This fix ensures that all model imports happen in the correct scope, preventing Python's closure mechanism from causing variable access errors when nested functions are executed in different contexts (like production vs development environments).
