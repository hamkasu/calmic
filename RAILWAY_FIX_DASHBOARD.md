# Railway Dashboard Fix - Deployment Guide

## Problem
Your iOS app's dashboard is failing to load on Railway with this error:
```
ERROR: column photo.original_photo_id does not exist
```

This happens because your Railway production database is missing columns that were added to the Photo model for enhanced photo tracking.

## What's Missing
The Photo table on Railway needs these columns:
- `original_photo_id` - Links enhanced photos to their originals
- `is_enhanced_version` - Boolean flag for enhanced photos
- `enhancement_type` - Type of enhancement applied (colorized, sharpened, etc.)

## Solution
I've created a database migration file that will automatically add these columns when you deploy to Railway.

### Steps to Deploy

1. **Commit the migration file**
   ```bash
   git add migrations/versions/g2a3b4c5d6e7_add_enhanced_photo_tracking_columns.py
   git commit -m "Add enhanced photo tracking columns migration"
   ```

2. **Push to GitHub**
   ```bash
   git push origin main
   ```

3. **Railway will automatically:**
   - Pull the new code
   - Run the migration during deployment
   - Add the missing columns to your database
   - Restart your app

4. **Verify the fix**
   - Open your iOS app
   - Login
   - The dashboard should now load successfully

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

After deployment, check the Railway logs to confirm the migration ran:
```
INFO  [alembic.runtime.migration] Running upgrade f1a2b3c4d5e6 -> g2a3b4c5d6e7, add_enhanced_photo_tracking_columns
```

Your iOS dashboard should then load without errors!

## Notes
- This migration is **safe** - it only adds new nullable columns
- Existing data will not be affected
- The migration can be rolled back if needed
- The local Replit environment already has these columns (that's why it works here)
