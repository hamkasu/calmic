# Railway iOS AI Quota Error Fix

## Problem
Users on the iOS app are getting this error when trying to use AI enhancements:
```
Error: You've reached your monthly AI enhancement limit (0 enhancements).
AxiosError: Request failed with status code 429
```

## Root Cause
The Railway database is missing AI quota columns or the subscription plans don't have AI quotas configured properly.

## The Fix

### Step 1: Connect to Railway Database
1. Go to your Railway project
2. Click on your PostgreSQL database
3. Click the **"Data"** tab
4. Click **"Query"** button

### Step 2: Run This SQL Script

Copy and paste this entire SQL script into the Railway query editor:

```sql
-- =================================================================
-- RAILWAY AI QUOTA FIX
-- Adds missing AI enhancement quota columns and configures plans
-- =================================================================

-- Add AI enhancement quota column to subscription_plan table (if missing)
ALTER TABLE subscription_plan 
ADD COLUMN IF NOT EXISTS ai_enhancement_quota INTEGER NOT NULL DEFAULT 0;

-- Add AI enhancement tracking columns to user_subscription table (if missing)
ALTER TABLE user_subscription 
ADD COLUMN IF NOT EXISTS ai_enhancements_used INTEGER NOT NULL DEFAULT 0;

ALTER TABLE user_subscription 
ADD COLUMN IF NOT EXISTS ai_enhancements_reset_date TIMESTAMP;

-- =================================================================
-- UPDATE SUBSCRIPTION PLANS WITH AI QUOTAS
-- =================================================================

-- Update Free plan (5 AI enhancements/month)
UPDATE subscription_plan 
SET ai_enhancement_quota = 5 
WHERE name = 'free' AND is_active = true;

-- Update Basic plan (25 AI enhancements/month)
UPDATE subscription_plan 
SET ai_enhancement_quota = 25 
WHERE name = 'basic' AND is_active = true;

-- Update Premium plan (75 AI enhancements/month)
UPDATE subscription_plan 
SET ai_enhancement_quota = 75 
WHERE name = 'premium' AND is_active = true;

-- Update Unlimited plan (500 AI enhancements/month)
UPDATE subscription_plan 
SET ai_enhancement_quota = 500 
WHERE name = 'unlimited' AND is_active = true;

-- =================================================================
-- RESET ALL USER AI QUOTAS
-- This gives everyone a fresh start with their AI quota
-- =================================================================

UPDATE user_subscription 
SET 
    ai_enhancements_used = 0,
    ai_enhancements_reset_date = DATE_TRUNC('month', NOW() + INTERVAL '1 month')
WHERE status = 'active';

-- =================================================================
-- VERIFICATION QUERIES
-- =================================================================

-- Check that columns were added
SELECT 
    column_name, 
    data_type, 
    column_default,
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('subscription_plan', 'user_subscription')
AND column_name IN ('ai_enhancement_quota', 'ai_enhancements_used', 'ai_enhancements_reset_date')
ORDER BY table_name, column_name;

-- Check subscription plan quotas
SELECT 
    name, 
    display_name, 
    ai_enhancement_quota,
    is_active,
    price_myr
FROM subscription_plan 
WHERE is_active = true
ORDER BY price_myr;

-- Check active user subscriptions
SELECT 
    us.id,
    u.username,
    sp.name as plan_name,
    sp.ai_enhancement_quota as quota_limit,
    us.ai_enhancements_used as quota_used,
    us.ai_enhancements_reset_date as resets_on,
    us.status
FROM user_subscription us
JOIN "user" u ON us.user_id = u.id
JOIN subscription_plan sp ON us.plan_id = sp.id
WHERE us.status = 'active'
ORDER BY u.username
LIMIT 20;
```

### Step 3: Click "Run Query"
The script will:
1. ✅ Add missing AI quota columns
2. ✅ Configure all subscription plans with proper AI quotas
3. ✅ Reset all users to 0 AI usage for a fresh start
4. ✅ Show verification results

### Step 4: Restart Railway Service
After running the SQL:
1. Go to your Railway service (the one running the Flask app)
2. Click **"Settings"**
3. Scroll down and click **"Restart"**
4. Wait for the service to come back online

### Step 5: Test on iOS
1. Close and reopen the StoryKeep app on your iPhone
2. Try using an AI enhancement feature (colorization, AI restore, or sharpen)
3. The error should be gone! ✅

## What This Fix Does

### AI Quota System
- **Free Plan**: 5 AI enhancements per month
- **Basic Plan**: 25 AI enhancements per month
- **Premium Plan**: 75 AI enhancements per month
- **Unlimited Plan**: 500 AI enhancements per month

### How It Works
1. Each time a user uses an AI feature (colorization, AI restoration, sharpen), the counter increments
2. The quota resets automatically on the 1st of each month
3. Users can see their remaining quota in the app

## If You Still See Errors

### Error: "relation does not exist"
- This means the table names are different on Railway
- Check your Railway database table names and adjust the SQL accordingly

### Error: "column already exists"
- This is safe to ignore - it means the columns were already added
- The script uses `IF NOT EXISTS` to prevent errors

### Still Getting 429 Errors
1. Check the verification queries at the end of the SQL output
2. Make sure your plan has `ai_enhancement_quota > 0`
3. Make sure your user has an active subscription
4. Check Railway logs for any other errors

## Need to Give Someone More AI Quota?

Run this SQL to increase a specific user's quota:

```sql
-- Find user ID first
SELECT id, username, email FROM "user" WHERE username = 'hamka';

-- Then update their subscription (replace USER_ID)
UPDATE user_subscription 
SET 
    ai_enhancements_used = 0,
    ai_enhancements_reset_date = DATE_TRUNC('month', NOW() + INTERVAL '1 month')
WHERE user_id = USER_ID AND status = 'active';
```

Or upgrade them to a higher plan with more quota!
