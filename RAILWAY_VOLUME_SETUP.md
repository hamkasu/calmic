# 📸 How to Fix Missing Photos on Railway

## 🔴 The Problem (Right Now)

```
┌─────────────────────────────────────────────┐
│  Railway Container (TEMPORARY STORAGE)      │
│                                             │
│  📁 /data/uploads/2/                        │
│     ├── hamka.20251018.601978.jpg  ✅       │
│     ├── hamka.20251018.495177.jpg  ✅       │
│     └── hamka.20251018.558558.jpg  ✅       │
│                                             │
│  [Container RESTARTS] 🔄                    │
│                                             │
│  📁 /data/uploads/2/                        │
│     └── (EMPTY - All files deleted!) ❌     │
│                                             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Database (PERSISTENT - Keeps Records)      │
│                                             │
│  Photo ID  |  filename              | path │
│  ──────────────────────────────────────────│
│     1      | hamka.20251018.601978  | /... │
│     2      | hamka.20251018.495177  | /... │
│     3      | hamka.20251018.558558  | /... │
│                                             │
│  (Database still thinks files exist!)  ⚠️   │
└─────────────────────────────────────────────┘

Result: Database ✅  Files ❌  = Placeholders shown
```

---

## ✅ The Solution (Railway Volume)

```
┌─────────────────────────────────────────────┐
│  Railway Container                          │
│                                             │
│  📁 /data/ (MOUNTED VOLUME)                 │
│     └── uploads/2/                          │
│         ├── hamka.20251018.601978.jpg  ✅   │
│         ├── hamka.20251018.495177.jpg  ✅   │
│         └── hamka.20251018.558558.jpg  ✅   │
│                                             │
│  [Container RESTARTS] 🔄                    │
│                                             │
│  📁 /data/ (VOLUME = FILES PERSIST!)        │
│     └── uploads/2/                          │
│         ├── hamka.20251018.601978.jpg  ✅   │
│         ├── hamka.20251018.495177.jpg  ✅   │
│         └── hamka.20251018.558558.jpg  ✅   │
│                                             │
└─────────────────────────────────────────────┘

Result: Database ✅  Files ✅  = Photos shown! 🎉
```

---

## 🚀 Quick Fix (5 Minutes)

### Step 1: Open Railway Dashboard
Go to: https://railway.app/dashboard

### Step 2: Find Your PhotoVault Service
Click on your PhotoVault project → PhotoVault service

### Step 3: Add Volume
1. Click **"Settings"** tab (left sidebar)
2. Scroll down to **"Volumes"** section
3. Click **"+ New Volume"** button
4. Fill in:
   ```
   Mount Path: /data
   ```
5. Click **"Add"** or **"Create Volume"**

### Step 4: Check Environment Variable
1. Click **"Variables"** tab
2. Look for `UPLOAD_FOLDER`
3. If it exists and equals `/data/uploads` → ✅ Good!
4. If missing, add it:
   - Variable: `UPLOAD_FOLDER`
   - Value: `/data/uploads`

### Step 5: Redeploy
Railway will automatically redeploy. If not:
1. Go to **"Deployments"** tab
2. Click **"Redeploy"**

### Step 6: Clean Up Old Records
After the volume is mounted, SSH into Railway or run locally against Railway DB:

```bash
# This removes database records for files that no longer exist
python cleanup_orphaned_photos.py
```

It will:
- ✅ Find all photo records with missing files
- ✅ Ask for confirmation before deleting
- ✅ Clean up the database so placeholders disappear

---

## 🧪 Test It Works

1. **Upload a new photo** (web or mobile app)
2. **Manually restart** Railway service (Settings → Restart)
3. **Check photo still shows** ✅

If the photo persists after restart = **Volume working!** 🎉

---

## 📊 What You'll See After Fix

### Before (With Ephemeral Storage):
```
Gallery: [Placeholder] [Placeholder] [Placeholder]
Database: 50 photos ❌ Files: 0 photos
```

### After (With Persistent Volume):
```
Gallery: [Photo 1] [Photo 2] [Photo 3]
Database: 50 photos ✅ Files: 50 photos
```

---

## 🎯 Summary

**Problem**: Railway deletes uploaded photos on restart  
**Cause**: No persistent volume configured  
**Fix**: Add Railway Volume at `/data` mount path  
**Time**: 5 minutes  
**Cost**: Free (included in Railway plan)

---

## 💡 Important Notes

1. **Old photos are gone**: Files uploaded before the volume won't come back
2. **Database still has records**: Use cleanup script to remove orphaned records
3. **Re-upload needed**: Users need to upload photos again after volume is set up
4. **Future uploads safe**: Once volume is mounted, all new photos will persist! ✅

---

## Alternative: Object Storage (Advanced)

If you want unlimited storage without Railway limits:
- Use AWS S3, Google Cloud Storage, or similar
- PhotoVault already has object storage code built-in
- Just set environment variables for your storage provider
- More expensive but unlimited and CDN-delivered

For now, **Railway Volume is the quickest fix!** 🚀
