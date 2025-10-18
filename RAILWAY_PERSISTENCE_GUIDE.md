# Complete Railway Data Persistence Setup

## The Problem
Railway containers are **ephemeral** - everything gets wiped on restart unless properly configured.

## The Solution: 2-Part Setup

### Part 1: Database Persistence (REQUIRED)

**What**: PostgreSQL for all data (users, photos metadata, etc.)

**Setup**:
1. Open Railway Dashboard → Your PhotoVault project
2. Click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
3. Railway automatically sets `DATABASE_URL` environment variable
4. **Verify**: Go to Variables tab, confirm `DATABASE_URL` exists

**Status**: ✅ This should already be done based on your setup

---

### Part 2: File Storage Persistence (REQUIRED)

**What**: Railway Volume for uploaded photo files

#### Step-by-Step Volume Setup:

1. **Go to Railway Dashboard** → Your PhotoVault service (not the database)
2. Click **"Settings"** tab (left sidebar)
3. Scroll down to **"Volumes"** section
4. Click **"+ New Volume"**
5. Configure:
   - **Mount Path**: `/data` (exactly this, no trailing slash)
   - **Size**: `10` GB (or more based on needs)
6. Click **"Add"** or **"Create Volume"**

#### Step-by-Step Environment Variable:

1. Stay in same service, click **"Variables"** tab
2. Click **"+ New Variable"**
3. Add:
   - **Variable Name**: `UPLOAD_FOLDER`
   - **Value**: `/data/uploads`
4. Click **"Add"**

#### Redeploy:

1. Go to **"Deployments"** tab
2. Click **"Redeploy"** on latest deployment
3. Wait for deployment to complete

---

## Verification Checklist

After setup, verify with this script on Railway:

```bash
# Run this on Railway to verify
railway run python -c "
import os
print('=== PERSISTENCE CHECK ===')
print(f'DATABASE_URL: {'✅ SET' if os.environ.get('DATABASE_URL') else '❌ MISSING'}')
print(f'UPLOAD_FOLDER: {os.environ.get('UPLOAD_FOLDER', '❌ NOT SET')}')
print(f'Volume mounted: {'✅ YES' if os.path.exists('/data') else '❌ NO'}')
"
```

**Expected Output**:
```
=== PERSISTENCE CHECK ===
DATABASE_URL: ✅ SET
UPLOAD_FOLDER: /data/uploads
Volume mounted: ✅ YES
```

---

## Common Mistakes

### ❌ Wrong Mount Path
```
Mount Path: /data/uploads  ← WRONG (too specific)
```
```
Mount Path: /data          ← CORRECT
```

### ❌ Wrong Environment Variable
```
UPLOAD_FOLDER=/uploads     ← WRONG (not in volume)
```
```
UPLOAD_FOLDER=/data/uploads ← CORRECT
```

### ❌ Forgot to Redeploy
After adding volume/variable, **MUST redeploy** for changes to take effect.

---

## Test It Works

### 1. Upload a Test Photo
- Upload any photo through your app
- Note the filename

### 2. Check File Exists on Railway
```bash
railway run ls -la /data/uploads/1/
```
You should see your uploaded file.

### 3. Trigger Redeploy
- Go to Deployments → Redeploy
- Wait for completion

### 4. Check File Still Exists
```bash
railway run ls -la /data/uploads/1/
```
File should **still be there** ✅

---

## What Happens to Old Photos?

Photos uploaded **before** volume setup are **permanently lost**. They were stored in ephemeral storage and deleted on restart.

**Solution**: Clean up orphaned database records:
```bash
railway run python cleanup_orphaned_photos.py
```

---

## Final Architecture

```
Railway Service
├── PostgreSQL Database (separate service)
│   └── Stores: users, photo metadata, settings
│
├── Volume mounted at /data
│   └── /data/uploads/{user_id}/
│       └── Stores: actual photo files
│
└── Environment Variables
    ├── DATABASE_URL → Points to PostgreSQL
    └── UPLOAD_FOLDER=/data/uploads → Points to volume
```

---

## Troubleshooting

### "Photos still disappearing"
- Verify volume is created in **Volumes** tab
- Verify `UPLOAD_FOLDER=/data/uploads` in **Variables** tab
- Verify you **redeployed** after making changes
- Check volume is mounted: `railway run ls -la /data`

### "New uploads work, old ones don't"
- Old photos are gone (uploaded before volume)
- Run cleanup script: `railway run python cleanup_orphaned_photos.py`

### "Can't see /data folder"
- Volume only exists **after redeploy**
- Check Volumes tab shows volume attached to service
- Redeploy again if needed

---

## Success Criteria

✅ PostgreSQL database added  
✅ Volume created at `/data`  
✅ `UPLOAD_FOLDER=/data/uploads` set  
✅ Service redeployed  
✅ Test photo upload → redeploy → still exists  
