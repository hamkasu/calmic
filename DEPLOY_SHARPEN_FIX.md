# 🚀 Deploy Dashboard Sharpen Fix to Railway

## Current Situation
✅ **Fixed on Replit** - Dashboard sharpen works locally  
❌ **Broken on Railway** - Still showing "Authorization token is missing"  
🎯 **Solution** - Push the fix to GitHub → Railway auto-deploys

## What Was Fixed (Already on Replit)
**File**: `photovault/routes/photo.py`

1. **Added CSRF Exemption** (line 1375):
   ```python
   @photo_bp.route('/api/photos/<int:photo_id>/enhance', methods=['POST'])
   @csrf.exempt  # ← ADDED THIS
   @login_required
   ```

2. **Added Sharpen Type Detection** (lines 1432-1447):
   ```python
   if enhancement_type == 'sharpen':
       from photovault.utils.image_enhancement import sharpen_image
       output_path, applied_settings = sharpen_image(
           full_file_path,
           temp_enhanced_filepath,
           radius=radius,
           amount=amount,
           threshold=threshold,
           method=method
       )
   ```

## Deploy to Railway (Copy & Paste These)

### Open Replit Shell and run:

```bash
# Step 1: Stage the fix
git add photovault/routes/photo.py

# Step 2: Commit
git commit -m "Fix dashboard sharpen - add CSRF exempt and type detection"

# Step 3: Push to GitHub (Railway auto-deploys)
git push origin main
```

### Then Wait 2-3 Minutes
Railway will automatically deploy. Watch progress at: https://railway.app/

### Test on Production
1. Go to: `https://web-production-535bd.up.railway.app`
2. Login
3. Click **Sharpen** button on any photo
4. Should work without errors! ✅

## If You Get Errors

### "Git index locked" Error:
The repository is locked for safety. Try again in Shell.

### "Authentication failed" Error:
GitHub needs credentials:
```bash
git config user.name "YourGitHubUsername"
git config user.email "your@email.com"
git push origin main
```

### Need GitHub Token:
1. Go to: https://github.com/settings/tokens
2. Generate new token (classic)
3. Select `repo` scope
4. Use token as password when pushing

## Quick Single Command
```bash
git add photovault/routes/photo.py && git commit -m "Fix dashboard sharpen - CSRF exempt and type detection" && git push origin main
```

---

**Status**: Waiting for you to push to GitHub 🚀
