# Deploy Dark Blue Background to Railway

## Changes Made
Updated the application background to a dark blue gradient:
- **File Changed**: `static/css/style.css`
- **Background Changed**: From white/gray gradient to dark blue gradient
- **New Colors**: `linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%)`
- **Text Color**: Changed to white (#ffffff) for visibility on dark background

## Deploy to Railway

### Step 1: Push Changes to GitHub
```bash
git add static/css/style.css
git commit -m "Update background to dark blue gradient"
git push origin main
```

### Step 2: Railway Auto-Deploy
Railway will automatically detect the changes and redeploy your app. Wait 2-3 minutes for the deployment to complete.

### Step 3: Clear Browser Cache
After Railway deploys:
1. Open your Railway app in a browser
2. Hard refresh the page:
   - **Windows/Linux**: Press `Ctrl + Shift + R` or `Ctrl + F5`
   - **Mac**: Press `Cmd + Shift + R`
3. Verify the dark blue background appears

## Visual Change
- **Before**: Light gray/white gradient background
- **After**: Professional dark blue gradient background
- **Text**: White text color for better contrast

The dark blue creates a more modern, professional look for your photo management platform.
