# Deploy Dashboard Text Visibility Fix to Railway

## What Was Fixed

Improved the visibility of the dashboard welcome text that was barely readable due to low contrast.

### Changes Made:
- **Welcome Header**: "Welcome back, [username]!" 
  - Added text shadow: `text-shadow: 2px 2px 4px rgba(0,0,0,0.5)`
  - Increased font weight to 600 for better readability
  
- **Overview Subtitle**: "Here's your StoryKeep overview"
  - Added text shadow: `text-shadow: 1px 1px 3px rgba(0,0,0,0.5)`
  - Increased font size to 1.1rem
  - Removed low opacity that was making text hard to see

## File Modified:
- `photovault/templates/dashboard.html` (lines 32-33)

## How to Deploy to Railway

### Option 1: Via Git Push (Recommended)
```bash
# Make sure you're on the latest code
git status

# Add the dashboard fix
git add photovault/templates/dashboard.html

# Commit the fix
git commit -m "Fix dashboard welcome text visibility with text shadows"

# Push to Railway
git push origin main
```

Railway will automatically detect the push and redeploy your app.

### Option 2: Manual Railway Redeploy
1. Go to your Railway dashboard
2. Navigate to your PhotoVault service
3. Click "Redeploy" to use the latest code

## Verification After Deployment

1. Visit your Railway app URL
2. Log in to your account
3. Check the dashboard - the welcome text should now be clearly visible with improved contrast
4. The text should have a subtle shadow effect making it stand out against the dark background

## Visual Improvement

**Before**: White text with 90% opacity - hard to read on dark blue background
**After**: White text with text shadow - clear and easy to read with better depth

---

## Deploy Together With Database Fixes

If you haven't deployed the database fixes yet, you can deploy everything together:

```bash
# Add all pending fixes
git add migrations/versions/e4254a8d276f_add_mfa_secret_table.py
git add photovault/templates/dashboard.html
git add FIX_RAILWAY_DATABASE.md
git add DEPLOY_TEXT_VISIBILITY_FIX.md

# Commit everything
git commit -m "Fix dashboard text visibility and add MFA migration"

# Push to Railway
git push origin main
```

Then follow the database migration steps in `FIX_RAILWAY_DATABASE.md` to:
1. Run `flask db upgrade` on Railway
2. Clean up corrupted photo filenames

---

**Ready to deploy when you are!** ✅
