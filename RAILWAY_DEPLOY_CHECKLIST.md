# 🚀 Railway Deployment Checklist - PhotoVault

## ✅ What's Fixed

✨ **PhotoVault now auto-detects Railway Volumes!**

No manual environment variable configuration needed. Just add a volume in Railway dashboard and the app automatically uses it for persistent photo storage.

---

## 📋 Deployment Steps

### **1️⃣ Push Latest Code to GitHub**

The following files were updated with auto-detection:
```bash
git add photovault/config.py railway_diagnose.py
git commit -m "feat: Auto-detect Railway Volume for persistent photo storage"
git push origin main
```

### **2️⃣ Add Railway Volume**

1. Go to **Railway Dashboard** → Your PhotoVault service
2. **Settings** → **Volumes** section
3. Click **"+ New Volume"**
4. Click **"Add"** (Railway auto-configures everything)
5. Railway will automatically redeploy ✅

### **3️⃣ Verify in Logs**

After deployment completes, check Railway logs for:
```
✅ Railway Volume detected and mounted at: /data
   Files will be saved to: /data/uploads
   Storage: Persistent (survives restarts) ✅
```

### **4️⃣ Clean Up Old Database Records** (Optional)

Remove orphaned photo records from when storage was ephemeral:

**Via Railway Shell:**
1. Go to service → **"Shell"** tab
2. Run:
```bash
python cleanup_orphaned_photos.py
```
3. Type `yes` to confirm deletion

### **5️⃣ Test Photo Upload**

1. Open mobile app or web interface
2. Upload a new photo
3. Go to Railway → Settings → Click **"Restart"**
4. Check photo still appears after restart ✅

---

## 🎯 What Changed

### **Before This Fix:**
- Manual `UPLOAD_FOLDER` environment variable required
- Users had to know exact mount path
- Easy to misconfigure

### **After This Fix:**
- ✅ Automatic Railway Volume detection
- ✅ No environment variables needed
- ✅ Works out of the box
- ✅ Logs confirm when volume is detected

---

## 📊 Current Status

### **Development (Replit):**
✅ Working - Uses local storage

### **Production (Railway):**
⚠️ **Needs volume added** - See Step 2 above
📝 After volume is added → ✅ Will work perfectly!

---

## 🔍 Diagnostic Tool

Run this anytime to check Railway configuration:
```bash
# Via Railway CLI:
railway run python railway_diagnose.py

# Or via Railway Shell:
python railway_diagnose.py
```

Checks:
- ✅ Database configuration
- ✅ Secret key setup
- ✅ Volume detection
- ✅ Upload folder path
- ✅ Optional services (OpenAI, SendGrid, Stripe)

---

## 💾 Storage Details

### **Volume Configuration (Auto):**
- **Mount Path**: Set by Railway (typically `/data`)
- **Upload Path**: Auto-detected as `{mount}/uploads`
- **Detection**: Via `RAILWAY_VOLUME_MOUNT_PATH` env var
- **Size**: 100 MB (shown in your screenshot) ✅

### **Current Usage:**
- **Used**: 2.7 MB
- **Available**: 97.3 MB remaining
- **Limit**: 100 MB (Railway Hobby plan)

---

## 🎉 Success Criteria

You'll know everything is working when:

1. ✅ Railway logs show "Railway Volume detected"
2. ✅ Photos upload successfully via mobile/web
3. ✅ Photos persist after Railway service restart
4. ✅ No more "Photo Placeholder" in gallery
5. ✅ Storage usage shows in Railway dashboard

---

## 📱 Mobile App Configuration

### **Already Configured:**
✅ iOS app points to: `https://web-production-535bd.up.railway.app`  
✅ Android app points to: `https://web-production-535bd.up.railway.app`  
✅ Both apps ready to test after Railway is fixed

### **Files Using Railway Backend:**
- `StoryKeep-iOS/src/services/api.js`
- `StoryKeep-iOS/src/screens/*.js` (all screens)
- `StoryKeep-iOS/src/utils/sharePhoto.js`

All hardcoded to production Railway URL ✅

---

## 🔧 Quick Commands

```bash
# Push code to Railway (via GitHub):
git push origin main

# Check Railway logs:
railway logs

# Run diagnostics:
railway run python railway_diagnose.py

# Clean up orphaned photos:
railway run python cleanup_orphaned_photos.py

# Test database connection:
railway run python -c "from photovault import create_app; app = create_app(); print('✅ App created successfully')"
```

---

## 🆘 If Something Goes Wrong

### **Photos still showing placeholders:**
1. Verify volume is actually added in Railway dashboard
2. Check logs for "Railway Volume detected" message
3. Make sure app redeployed after adding volume
4. Run cleanup script to remove orphaned records

### **Volume not detected:**
1. Check Railway → Settings → Volumes section
2. Verify mount path was created
3. Restart service manually
4. Check `RAILWAY_VOLUME_MOUNT_PATH` is set (automatic)

### **Database issues:**
1. Make sure PostgreSQL addon is connected
2. Run: `railway run python railway_diagnose.py`
3. Check for database connection errors

---

## ✨ Next Steps

1. **Immediate**: Push code to GitHub (triggers Railway redeploy)
2. **Then**: Add Railway Volume (2 minutes)
3. **Finally**: Test photo upload and restart
4. **Optional**: Run cleanup script for old records

**Estimated Time**: 5 minutes total ⚡

---

## 📞 Support

If issues persist after following this checklist:
- Check Railway logs for specific errors
- Run diagnostic script for detailed status
- Verify all environment variables in Railway dashboard

---

**Status**: 🎯 Ready to deploy! Push code → Add volume → Test → Done! ✅
