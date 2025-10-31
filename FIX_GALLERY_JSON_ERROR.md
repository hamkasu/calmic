# Fix iOS Gallery JSON Parse Error

## Problem
iOS app shows "Failed to load photos" with error: `SyntaxError: JSON Parse error: Unexpected character: <`

This means the `/api/photos` endpoint on Railway is returning HTML instead of JSON, likely an error page.

## Root Causes
1. **Corrupted photo data in database** - Photos with filenames like `2/(f,"'int' object is not iterable")` break JSON serialization
2. **Missing error handling** - When JSON serialization fails, Flask returns HTML error page instead of JSON error response

## Solution

### Part 1: Update Mobile API Code (Already Fixed Locally)

The `/api/photos` endpoint in `photovault/routes/mobile_api.py` has been updated with:
- ✅ Skip photos with corrupted filenames containing `(` or error messages
- ✅ Safe type conversion for all JSON fields
- ✅ Per-photo try-catch to prevent one bad photo from breaking the entire response
- ✅ Proper logging of skipped/corrupted photos

### Part 2: Clean Up Corrupted Photos in Railway Database

**Option A: Delete Corrupted Photos (Recommended)**
```sql
-- Find corrupted photos
SELECT id, user_id, filename, edited_filename 
FROM photo 
WHERE filename LIKE '%(%' 
   OR filename LIKE '%object is not iterable%'
   OR edited_filename LIKE '%(%'
   OR edited_filename LIKE '%object is not iterable%';

-- Delete them (BACKUP FIRST!)
DELETE FROM photo 
WHERE filename LIKE '%(%' 
   OR filename LIKE '%object is not iterable%'
   OR edited_filename LIKE '%(%'
   OR edited_filename LIKE '%object is not iterable%';
```

**Option B: Fix Corrupted Filenames**
```sql
-- Update corrupted filenames to NULL
UPDATE photo 
SET filename = NULL 
WHERE filename LIKE '%(%' 
   OR filename LIKE '%object is not iterable%';

UPDATE photo 
SET edited_filename = NULL 
WHERE edited_filename LIKE '%(%' 
   OR edited_filename LIKE '%object is not iterable%';
```

### Part 3: Deploy Fix to Railway

#### Step 1: Push Code to GitHub
```bash
git add photovault/routes/mobile_api.py
git commit -m "Fix: Add robust error handling to /api/photos endpoint for iOS gallery

- Skip photos with corrupted filenames
- Add per-photo try-catch to prevent JSON serialization errors
- Safe type conversion for all fields
- Proper logging of issues"
git push origin main
```

#### Step 2: Railway Will Auto-Deploy
Railway automatically deploys when you push to `main` branch.

#### Step 3: Clean Database (via Railway Dashboard)
1. Go to Railway project dashboard
2. Click on PostgreSQL database
3. Click "Query" tab
4. Run the SQL cleanup script from Option A or B above

#### Step 4: Test iOS App
1. Open StoryKeep app on iPhone
2. Login with your account
3. Go to Gallery
4. Should now load photos successfully (skipping any corrupted ones)

## Verification

### Check Railway Logs
Look for these log messages after deployment:
```
⚠️ Skipping photo X with corrupted filename: 2/(f,"'int' object is not iterable")
✅ Returning page 1/X (Y photos) to mobile app
```

### Test API Directly
```bash
# Replace with your actual JWT token
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     https://storykeep.calmic.com.my/api/photos

# Should return valid JSON with success: true
```

## Prevention
The updated code prevents this issue by:
1. Validating all data before JSON serialization
2. Skipping corrupted records instead of crashing
3. Logging warnings so you can identify and fix bad data
4. Always returning valid JSON, even when errors occur

## Notes
- This fix is already applied to local Replit environment
- Must be deployed to Railway for iOS app to benefit
- Corrupted photos should be cleaned from database for best results
- The fix allows the app to work even with some corrupted data
