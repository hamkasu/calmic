# Railway Database Fix - Missing Columns (October 30, 2025)

## Current Problem
Your Railway production database is missing two columns that exist in your local development:
- `grid_thumbnail_path` - Small 200x200 thumbnails for gallery grid display
- `blurhash` - Instant placeholder preview hashes

**Symptoms:**
- ❌ Dashboard shows 0 photos (even though data exists in database)
- ❌ iOS app gets 502 errors
- ❌ Error: `column photo.grid_thumbnail_path does not exist`

## Problem Analysis
Looking at your Railway database, the photo records exist:
- Photos 16, 17, 18, 19, 34 are in the database for user "hamka"
- File paths: `/data/2/hamka.20251018.706607.jpg`, etc.
- **But the Photo model queries fail** because the schema is missing columns

## Solution Overview
Apply the database migration to add the missing columns. The migration is safe and can run multiple times.

---

## Method 1: Direct SQL (Recommended ✅)

**Why this method?**  
The migration chain has broken links, so the direct SQL approach is the most reliable solution.

**1. Access Railway PostgreSQL**
- Go to Railway Dashboard → Your StoryKeep Project
- Click on the PostgreSQL database service
- Click "Connect" tab → Select "PostgreSQL (psql)"
- Copy the connection command

**2. Run the SQL Commands**

In your Railway PostgreSQL console, run:

```sql
-- Add missing columns (safe - won't error if they exist)
ALTER TABLE photo 
ADD COLUMN IF NOT EXISTS grid_thumbnail_path VARCHAR(500);

ALTER TABLE photo 
ADD COLUMN IF NOT EXISTS blurhash VARCHAR(100);

-- Verify columns were added
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'photo' 
AND column_name IN ('grid_thumbnail_path', 'blurhash')
ORDER BY column_name;
```

**3. Expected Output**
```
     column_name      | data_type | character_maximum_length
----------------------+-----------+-------------------------
 blurhash            | varchar   |                      100
 grid_thumbnail_path | varchar   |                      500
(2 rows)
```

**4. Verify Fix Immediately**
- Refresh your web dashboard - should show 5 photos
- Test iOS app - should load without 502 errors

---

## Method 2: Automatic Fallback (No Action Needed)

Your app has a built-in fallback mechanism that automatically adds missing columns on startup.

**What happens:**
1. Railway deployment runs `python release.py`
2. App detects missing columns
3. Fallback adds them automatically
4. Server starts normally

**Check Railway logs for:**
```
✅ Database schema updated successfully
```

**Note:** The columns will be added automatically on the next Railway deployment, even without pushing changes.

---

## Method 3: Manual Migration (If You Prefer)

**Note:** The migration chain has some broken links, so this may fail. Use Method 1 (Direct SQL) if issues occur.

**1. Access Railway PostgreSQL**
- Railway Dashboard → Your Database → Connect → PostgreSQL

**2. Run SQL Commands**
```sql
-- Add missing columns
ALTER TABLE photo 
ADD COLUMN IF NOT EXISTS grid_thumbnail_path VARCHAR(500);

ALTER TABLE photo 
ADD COLUMN IF NOT EXISTS blurhash VARCHAR(100);

-- Verify columns exist
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'photo' 
AND column_name IN ('grid_thumbnail_path', 'blurhash')
ORDER BY column_name;
```

**Expected Output:**
```
     column_name      | data_type | character_maximum_length
----------------------+-----------+-------------------------
 blurhash            | varchar   |                      100
 grid_thumbnail_path | varchar   |                      500
```

---

## Verification Steps

After applying the fix:

### ✅ Web Dashboard Test
1. Go to https://storykeep.calmic.com.my
2. Login as "hamka"
3. **Expected**: Dashboard shows "5" in Total Photos (instead of 0)
4. **Expected**: "My Photos" section displays your 5 photos

### ✅ iOS App Test
1. Open StoryKeep app
2. Login with credentials
3. **Expected**: Dashboard loads without 502 errors
4. **Expected**: Gallery shows your existing photos

### ✅ Railway Logs Check
```
✅ Added grid_thumbnail_path column to photo table
✅ Added blurhash column to photo table
[INFO] Database schema updated successfully
```

---

## What the Migration Does

**File:** `migrations/versions/20251030_add_grid_thumbnail_and_blurhash.py`

```python
# Safely adds columns only if they don't exist
def upgrade():
    if not column_exists('photo', 'grid_thumbnail_path'):
        op.add_column('photo', sa.Column('grid_thumbnail_path', sa.String(500)))
    
    if not column_exists('photo', 'blurhash'):
        op.add_column('photo', sa.Column('blurhash', sa.String(100)))
```

**Why It's Safe:**
- ✅ Checks if columns exist before adding
- ✅ Won't fail if run multiple times
- ✅ Nullable columns (won't affect existing data)
- ✅ Includes rollback function

---

## Troubleshooting

### Issue: "Auto-migration via Alembic failed: 'NoneType' object is not iterable"
- **Cause**: Railway's auto-migration in release.py has an edge case
- **Solution**: Use Method 2 (Manual Migration) or Method 3 (Direct SQL)

### Issue: Dashboard still shows 0 photos
1. Clear browser cache (Ctrl+Shift+R)
2. Check Railway logs for migration success
3. Verify columns using Method 2 Step 3

### Issue: iOS still gets 502 errors
1. Check Railway deployment completed successfully
2. Verify app is using correct URL: `https://storykeep.calmic.com.my`
3. Check Railway logs for other errors

---

## Timeline

- **Before Fix**: Dashboard 0 photos, iOS 502 errors
- **After Fix**: Dashboard shows 5 photos, iOS app works
- **Deployment Time**: ~2-3 minutes for Railway to build and deploy

---

## Files Modified

- ✅ `migrations/versions/20251030_add_grid_thumbnail_and_blurhash.py` - New migration
- ✅ `RAILWAY_DATABASE_FIX.md` - This guide

## Schema Changes

| Column | Type | Purpose |
|--------|------|---------|
| `grid_thumbnail_path` | VARCHAR(500) | 200x200 thumbnail for fast gallery grid |
| `blurhash` | VARCHAR(100) | Instant placeholder preview hash |

---

**Status**: Migration created and ready to deploy  
**Action**: Push to GitHub and Railway will auto-deploy  
**Impact**: Fixes dashboard and iOS app immediately
