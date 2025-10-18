# Railway Deployment Guide - Data Persistence Setup

## ⚠️ Critical: Ensure Data Persistence on Railway

Railway uses ephemeral containers that **reset on every deployment**. Without proper configuration, you will lose:
- 🔴 All database data (users, photos, settings)
- 🔴 All uploaded files (photos, images)

This guide ensures your data persists across deployments.

---

## 🗄️ Database Persistence (CRITICAL)

### Step 1: Add PostgreSQL Database

1. Go to your **Railway dashboard**
2. Navigate to your **PhotoVault project**
3. Click **"+ New"** → **"Database"** → **"PostgreSQL"**
4. Railway will automatically:
   - Create a PostgreSQL database
   - Set the `DATABASE_URL` environment variable
   - Connect it to your service

### Step 2: Verify Database Configuration

Run this command to verify:
```bash
railway run python verify_railway_config.py
```

Or check manually in Railway dashboard:
- Go to **Variables** tab
- Look for `DATABASE_URL` (should start with `postgresql://`)

### What happens without PostgreSQL?
- ❌ App will **fail to start** with clear error message
- ❌ No SQLite fallback (prevents data loss)

---

## 📁 File Storage Persistence (IMPORTANT)

Uploaded photos are stored in local directories by default, which get deleted on restart.

### Option 1: Railway Volumes (Recommended)

1. Go to **Railway → Your service → Settings → Volumes**
2. Click **"New Volume"**
3. Configure:
   - **Mount path**: `/data`
   - **Size**: 10GB+ (based on your needs)
4. Click **Create**
5. Add environment variable in **Variables** tab:
   ```
   UPLOAD_FOLDER=/data/uploads
   ```
6. **Redeploy** your app

### Option 2: External Object Storage

Alternative: Use AWS S3, Google Cloud Storage, or similar:
1. Set up external storage bucket
2. Update file upload logic to use storage SDK
3. Set credentials in environment variables

### Verify File Storage

Run the verification script:
```bash
railway run python verify_railway_config.py
```

Look for: ✅ File storage configured with Railway Volume: /data/uploads

---

## 🔑 Security Configuration

### Set SECRET_KEY (Required)

Generate and set a secure secret key:

```bash
# Using Railway CLI
railway variables set SECRET_KEY=$(openssl rand -base64 32)
```

Or in Railway dashboard:
- Go to **Variables** tab
- Add: `SECRET_KEY` = (random 32+ character string)

**Why?** Without this:
- User sessions reset on every deployment
- Authentication breaks
- Security vulnerability

---

## 📋 Complete Environment Variables Checklist

In your Railway **Variables** tab, ensure you have:

### Required:
- ✅ `DATABASE_URL` - Auto-set when you add PostgreSQL
- ✅ `SECRET_KEY` - Random 32+ character string
- ✅ `FLASK_CONFIG=production`

### For File Persistence:
- ✅ `UPLOAD_FOLDER=/data/uploads` - If using Railway Volume

### Optional Services:
- ⚪ `OPENAI_API_KEY` - For AI features
- ⚪ `SENDGRID_API_KEY` - For email notifications
- ⚪ `STRIPE_SECRET_KEY` - For payments

---

## 🚀 Deployment Process

### Initial Setup:

```bash
# 1. Add PostgreSQL database (via dashboard)
# 2. Create Railway Volume at /data (via dashboard)

# 3. Set environment variables
railway variables set FLASK_CONFIG=production
railway variables set SECRET_KEY=$(openssl rand -base64 32)
railway variables set UPLOAD_FOLDER=/data/uploads

# 4. Deploy
railway up
```

### Verification:

```bash
# Run verification script
railway run python verify_railway_config.py

# Check logs
railway logs
```

Look for in logs:
- ✅ `Database: PostgreSQL` (NOT SQLite)
- ✅ No warnings about ephemeral storage

---

## 🔍 Troubleshooting

### "Data lost on restart"

**Database Issues:**
1. Check if PostgreSQL is added to project
2. Verify `DATABASE_URL` is set
3. Look for error: "No PostgreSQL database configured"
4. Solution: Add PostgreSQL via Railway dashboard

**File Storage Issues:**
1. Check if Railway Volume is mounted at `/data`
2. Verify `UPLOAD_FOLDER=/data/uploads` is set
3. Look for warning: "ephemeral directory"
4. Solution: Create Railway Volume and set environment variable

### "App won't start"

Check logs for:
- "DATABASE_URL environment variable must be set" → Add PostgreSQL
- "SECRET_KEY not provided" → Set SECRET_KEY variable

### Verify Configuration

The app now includes built-in checks that will:
- ❌ Fail startup if no database configured
- ⚠️  Warn if files are in ephemeral storage
- 📝 Log all configuration issues clearly

---

## 📊 Monitoring Data Persistence

### After deployment, verify:

1. **Database**:
   ```bash
   railway run flask shell
   >>> from photovault.models import User
   >>> User.query.count()  # Should show user count
   ```

2. **Files**:
   - Upload a test photo
   - Trigger a deployment
   - Check if photo still exists

3. **Sessions**:
   - Log in
   - Trigger a deployment  
   - Verify you're still logged in

---

## ✅ Success Checklist

Before considering deployment complete:

- [ ] PostgreSQL database added to Railway project
- [ ] `DATABASE_URL` environment variable set (auto)
- [ ] `SECRET_KEY` environment variable set (manual)
- [ ] Railway Volume created at `/data` (if using volumes)
- [ ] `UPLOAD_FOLDER=/data/uploads` set (if using volumes)
- [ ] `FLASK_CONFIG=production` set
- [ ] Verification script passes all checks
- [ ] Test upload → redeploy → file persists
- [ ] Test user creation → redeploy → user persists

---

## 🎯 Quick Command Reference

```bash
# Verify configuration
railway run python verify_railway_config.py

# View environment variables
railway variables

# Check logs
railway logs

# Open shell
railway run flask shell

# Deploy
railway up
```

---

## 📞 Support

If you continue experiencing data loss:
1. Run verification script and share output
2. Check Railway logs for error messages
3. Verify PostgreSQL service is "Active" in dashboard
4. Ensure Volume is properly mounted

The configuration is now hardened to prevent data loss - the app will fail loudly if persistence isn't configured correctly, rather than silently losing data.
