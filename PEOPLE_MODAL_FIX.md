# People Modal Bouncing Fix - Deployment Guide

## Issue Fixed
The "Add New Person" modal was bouncing up and down repeatedly on mobile devices, making it impossible to enter text. This was caused by the mobile browser's virtual keyboard triggering viewport resizes, which made Bootstrap modals recalculate their position continuously.

## Solution Applied
Added CSS to `photovault/templates/people.html` that:
- Fixes the modal position to the center of the screen
- Prevents repositioning when keyboard appears/disappears  
- Makes the modal content scrollable instead of moving the entire modal
- Optimized for mobile devices

## Files Changed
- `photovault/templates/people.html` - Added CSS to fix modal positioning

## Deploy to Railway

### Step 1: Push to GitHub
```bash
git add photovault/templates/people.html
git commit -m "Fix: Prevent Add Person modal from bouncing on mobile"
git push origin main
```

### Step 2: Railway Auto-Deploy
Railway will automatically detect the push and redeploy your application.

### Step 3: Verify
1. Wait for Railway deployment to complete (2-3 minutes)
2. Open your Railway app on mobile
3. Go to People page
4. Click "Add New Person"
5. Tap into any field - modal should stay stable now

## What Changed
The modal now:
- Stays centered on screen (doesn't move)
- Allows scrolling inside the form if keyboard covers content
- Works smoothly on both mobile and desktop
- No longer bounces when keyboard appears

## Testing
- ✅ Local Replit: Fixed and tested
- ⏳ Railway Production: Pending deployment
