# Railway Dashboard Fix - Deployment Guide

## Problem
Your iOS app's dashboard is failing to load on Railway with this error:
```
ERROR: AxiosError: Request failed with status code 500
Dashboard error: column photo.original_photo_id does not exist
```

This happens because your Railway production database is missing columns that were added to the Photo model for enhanced photo tracking.

## What's Missing
The Photo table on Railway needs these columns:
- `original_photo_id` - Links enhanced photos to their originals
- `is_enhanced_version` - Boolean flag for enhanced photos
- `enhancement_type` - Type of enhancement applied (colorized, sharpened, etc.)

## Solution - Automatic Migration
I've updated the app to automatically add these columns when Railway restarts. The fallback migration system will detect the missing columns and add them automatically.

### Steps to Deploy

1. **Commit the automatic migration fix**
   ```bash
   git add photovault/__init__.py
   git add migrations/versions/g2a3b4c5d6e7_add_enhanced_photo_tracking_columns.py
   git add RAILWAY_FIX_DASHBOARD.md
   git commit -m "Fix: Add automatic migration for enhanced photo tracking columns"
   ```

2. **Push to Railway**
   ```bash
   git push origin main
   ```

3. **Railway will automatically:**
   - Pull the new code
   - Detect the missing columns during startup
   - Add them automatically using the fallback migration system
   - Restart your app with the correct schema

4. **Verify the fix**
   - Wait for Railway deployment to complete (watch the logs)
   - Open your iOS app
   - Login
   - The dashboard should now load successfully with all your data

## What This Migration Does

```sql
-- Adds these columns to the photo table:
ALTER TABLE photo ADD COLUMN original_photo_id INTEGER;
ALTER TABLE photo ADD COLUMN is_enhanced_version BOOLEAN DEFAULT FALSE;
ALTER TABLE photo ADD COLUMN enhancement_type VARCHAR(50);
ALTER TABLE photo ADD CONSTRAINT fk_photo_original_photo_id 
  FOREIGN KEY (original_photo_id) REFERENCES photo (id);
```

## Verification

After deployment, check the Railway logs to confirm the columns were added:
```
INFO: Attempting direct column addition as fallback...
INFO: Adding missing column: original_photo_id
INFO: ✅ Added original_photo_id column
INFO: Adding missing column: is_enhanced_version
INFO: ✅ Added is_enhanced_version column
INFO: Adding missing column: enhancement_type
INFO: ✅ Added enhancement_type column
INFO: ✅ Database schema updated successfully
```

Your iOS dashboard should then load without errors!

## Notes
- This migration is **safe** - it only adds new nullable columns
- Existing data will not be affected
- The migration can be rolled back if needed
- The local Replit environment already has these columns (that's why it works here)
