# Railway Data Loss - Complete Fix Guide

## 🎯 Quick Fix Steps (Run These Now)

### Step 1: Check Current Status
```bash
railway run python check_deployment_status.py
```

This will show you:
- ✅ What's configured correctly
- 🔴 What needs to be fixed
- 📊 Database statistics
- 🗑️ How many orphaned photo records exist

---

### Step 2: Fix Database Persistence (If Not Using PostgreSQL)

**Via Railway Dashboard:**
1. Go to Railway dashboard → Your PhotoVault project
2. Click **"+ New"** → **"Database"** → **"PostgreSQL"**
3. Railway auto-sets `DATABASE_URL`
4. Redeploy

**Verify:**
```bash
railway run python verify_railway_config.py
# Should show: ✅ Using PostgreSQL
```

---

### Step 3: Fix File Storage Persistence (Critical!)

**Via Railway Dashboard:**
1. Go to your service → **Settings** → **Volumes**
2. Click **"New Volume"**
3. Set **Mount path:** `/data`
4. Set **Size:** 10GB+ (based on usage)
5. Click **Create**

**Set Environment Variable:**
```bash
railway variables set UPLOAD_FOLDER=/data/uploads
```

**Verify:**
```bash
railway run python verify_railway_config.py
# Should show: ✅ File storage configured with Railway Volume
```

---

### Step 4: Clean Up Missing Photos (If Any)

**Preview what will be deleted:**
```bash
railway run python cleanup_missing_photos.py
```

**Execute cleanup:**
```bash
railway run python cleanup_missing_photos.py --execute
```

This removes database records for files that were lost during previous restarts.

---

### Step 5: Set Secret Key (Recommended)

```bash
railway variables set SECRET_KEY=$(openssl rand -base64 32)
```

Without this, user sessions reset on every deployment.

---

### Step 6: Final Verification

```bash
# Complete status check
railway run python check_deployment_status.py

# Configuration verification
railway run python verify_railway_config.py
```

Both should show ✅ for all critical items.

---

## 🧪 Test Data Persistence

After setup, verify files persist:

```bash
# 1. Upload a test photo via the app
# 2. Note the filename/ID
# 3. Redeploy: railway up
# 4. Check if photo still exists in gallery
```

---

## 📊 Available Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `check_deployment_status.py` | Complete status overview | `railway run python check_deployment_status.py` |
| `verify_railway_config.py` | Configuration verification | `railway run python verify_railway_config.py` |
| `cleanup_missing_photos.py` | Remove orphaned records | `railway run python cleanup_missing_photos.py --execute` |

---

## ✅ Success Checklist

- [ ] PostgreSQL database added to Railway
- [ ] Railway Volume created at `/data`
- [ ] Environment variable `UPLOAD_FOLDER=/data/uploads` set
- [ ] Environment variable `SECRET_KEY` set
- [ ] Orphaned photo records cleaned up
- [ ] Status check shows all green ✅
- [ ] Test upload persists after redeploy

---

## 🆘 If Issues Persist

1. **Check logs:**
   ```bash
   railway logs
   ```

2. **View environment variables:**
   ```bash
   railway variables
   ```

3. **Ensure Volume is mounted:**
   - Railway dashboard → Service → Settings → Volumes
   - Should show `/data` mounted

4. **Restart service:**
   ```bash
   railway up
   ```

---

## 📝 What Changed

The configuration now:
- ❌ **Removed** SQLite fallback (was causing data loss)
- ✅ **Added** fail-safe checks (app won't start without PostgreSQL)
- ✅ **Added** warnings for ephemeral file storage
- ✅ **Added** Railway Volume support
- ✅ **Added** comprehensive status checking scripts
