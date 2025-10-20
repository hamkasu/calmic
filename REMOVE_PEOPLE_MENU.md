# Remove People Menu - Deployment Guide

## Change Made
Removed the "People" menu item from the main navigation bar due to persistent modal bouncing issues on mobile devices.

## File Changed
- `photovault/templates/base.html` - Removed People navigation link (lines 131-134)

## What Was Removed
The People menu link that appeared in the navigation bar:
```html
<a class="nav-link" href="/people">
    <i class="bi bi-people"></i> People
</a>
```

## Impact
- People menu no longer visible in navigation
- Users cannot access the People management page from the menu
- The People page route still exists (can be accessed directly via URL if needed)
- All other features remain unchanged

## Deploy to Railway

### Step 1: Push to GitHub
```bash
git add photovault/templates/base.html
git commit -m "Remove People menu from navigation"
git push origin main
```

### Step 2: Railway Auto-Deploy
Railway will automatically detect the push and redeploy your application.

### Step 3: Verify
1. Wait for Railway deployment to complete (2-3 minutes)
2. Open your Railway app
3. Check navigation bar - People menu should be gone
4. All other menu items (Dashboard, Upload, Detection, Gallery, Toolkit, Family, Subscription, About) remain

## Status
- ✅ Local Replit: People menu removed, server running
- ⏳ Railway Production: Pending deployment
