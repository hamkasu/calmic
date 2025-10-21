# Fix Login Crash on Railway - Critical Bug Fix

## Problem
Login crashes with error: `NameError: cannot access free variable 'User' where it is not associated with a value in enclosing scope`

This affects:
- User login
- User registration  
- Password reset

## Root Cause
Lambda functions in `photovault/routes/auth.py` cannot access the `User` model due to Python scope rules.

## Fix Applied (Local Environment)
Modified `photovault/routes/auth.py` - replaced lambda functions with proper nested functions in 3 locations:

### 1. Login Route (Line ~69)
**Before:**
```python
user = safe_db_query(
    lambda: User.query.filter(
        (User.username == username) | (User.email == username)
    ).first(),
    operation_name="user lookup"
)
```

**After:**
```python
def query_user():
    return User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()

user = safe_db_query(
    query_user,
    operation_name="user lookup"
)
```

### 2. Register Route (Line ~239)
**Before:**
```python
existing_user = safe_db_query(
    lambda: User.query.filter(
        (User.username == username) | (User.email == email)
    ).first(),
    operation_name="existing user check"
)
```

**After:**
```python
def query_existing_user():
    return User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

existing_user = safe_db_query(
    query_existing_user,
    operation_name="existing user check"
)
```

### 3. Forgot Password Route (Line ~428)
**Before:**
```python
user = safe_db_query(
    lambda: User.query.filter_by(email=email).first(),
    operation_name="user lookup by email"
)
```

**After:**
```python
def query_user_by_email():
    return User.query.filter_by(email=email).first()

user = safe_db_query(
    query_user_by_email,
    operation_name="user lookup by email"
)
```

## Deploy to Railway

### Step 1: Commit Changes
The changes have been made to your local Replit environment. You need to push them to GitHub:

```bash
git add photovault/routes/auth.py
git commit -m "Fix login crash - replace lambda with nested functions in auth routes"
git push origin main
```

### Step 2: Railway Auto-Deploy
Railway is connected to your GitHub repository and will automatically:
1. Detect the new commit
2. Build the updated code
3. Deploy to production

This typically takes 2-3 minutes.

### Step 3: Verify the Fix
After Railway finishes deploying:
1. Go to https://storykeep.calmic.com.my/auth/login
2. Try logging in with valid credentials
3. Login should work without crashes

## Status
✅ **Local Fix Applied**: All 3 lambda scope issues fixed in auth.py
⏳ **Railway Deployment**: Pending - requires git push
🔧 **Impact**: Fixes login, registration, and password reset for all users

## Timeline
- **Fix Applied**: 2025-10-20 17:26 UTC
- **Deployment**: Waiting for git push to trigger Railway auto-deploy
- **ETA**: 5 minutes after push

---
**Note**: This is a critical bug fix that should be deployed immediately to restore login functionality for all users.
