# Railway Database Fix Guide: AI Enhancement Quotas

## Problem
Your production website is crashing with this error:
```
column user_subscription.ai_enhancements_used does not exist
```

This happens because the database schema on Railway is missing the new AI enhancement tracking columns.

## Solution: Quick 2-Minute Fix

### Step 1: Open Railway Database
1. Go to https://railway.app
2. Open your StoryKeep project
3. Click on the **PostgreSQL** service (your database)
4. Click on the **Data** tab at the top
5. Click **Query** button to open the SQL query editor

### Step 2: Run the Fix SQL Script
Copy and paste this SQL into the query editor and click **Run**:

```sql
-- Add AI enhancement tracking columns
ALTER TABLE user_subscription 
ADD COLUMN IF NOT EXISTS ai_enhancements_used INTEGER NOT NULL DEFAULT 0;

ALTER TABLE user_subscription 
ADD COLUMN IF NOT EXISTS ai_enhancements_reset_date TIMESTAMP;

ALTER TABLE subscription_plan 
ADD COLUMN IF NOT EXISTS ai_enhancement_quota INTEGER NOT NULL DEFAULT 0;
```

### Step 3: Verify the Fix
Run this verification query to confirm the columns were added:

```sql
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'user_subscription' 
AND column_name IN ('ai_enhancements_used', 'ai_enhancements_reset_date')
ORDER BY column_name;
```

You should see two rows:
- `ai_enhancements_reset_date` (timestamp)
- `ai_enhancements_used` (integer with default 0)

### Step 4: Restart Your Railway Service
1. Go back to your Railway project dashboard
2. Click on your **web service** (PhotoVault)
3. Click the **Restart** button (⟳ icon) or redeploy

### Step 5: Test Your Website
Visit https://storykeep.calmic.com.my and verify it's working again!

---

## What These Columns Do

- **ai_enhancements_used**: Tracks how many AI enhancements (colorization, sharpening, etc.) a user has used this month
- **ai_enhancements_reset_date**: Stores when the counter should reset (monthly)
- **ai_enhancement_quota**: Defines the monthly limit for each subscription plan

## Alternative: Use the SQL File
If you prefer, you can run the complete SQL script provided in `RAILWAY_AI_QUOTA_FIX.sql`.

---

## Need Help?
If you encounter any issues:
1. Check the Railway deployment logs for any errors
2. Verify your database connection is working
3. Make sure you're running the SQL on the correct database (production)
