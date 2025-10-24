## 🔧 Complete Railway Database Fix Guide

Your website has **TWO issues** that need fixing:

### Issue 1: Website Crash ❌
**Error**: `column user_subscription.ai_enhancements_used does not exist`
**Fix**: Add missing database columns

### Issue 2: Old Plans Showing 📋
**Error**: Billing page shows old Basic/Standard/Premium plans
**Fix**: Deactivate old plans in database

---

## ✅ Quick Fix (3 Minutes)

### Step 1: Open Railway Database
1. Go to https://railway.app
2. Open your StoryKeep project
3. Click on **PostgreSQL** (your database service)
4. Click **Data** tab
5. Click **Query** button

### Step 2: Run This Complete Fix SQL

Copy and paste **ALL** of this into the query editor and click **Run**:

```sql
-- Fix 1: Add missing columns
ALTER TABLE user_subscription 
ADD COLUMN IF NOT EXISTS ai_enhancements_used INTEGER NOT NULL DEFAULT 0;

ALTER TABLE user_subscription 
ADD COLUMN IF NOT EXISTS ai_enhancements_reset_date TIMESTAMP;

ALTER TABLE subscription_plan 
ADD COLUMN IF NOT EXISTS ai_enhancement_quota INTEGER NOT NULL DEFAULT 0;

-- Fix 2: Deactivate old plans
UPDATE subscription_plan 
SET is_active = false 
WHERE LOWER(name) IN ('basic', 'standard', 'premium');

UPDATE subscription_plan 
SET is_active = false 
WHERE name IN ('Basic Plan', 'Standard Plan', 'Premium Plan');
```

### Step 3: Verify the Fix

Run this verification query to confirm:

```sql
-- Should show all plans with their active status
SELECT id, name, display_name, is_active, price_myr 
FROM subscription_plan 
ORDER BY is_active DESC, sort_order;
```

**Expected Result:**
- Old plans (Basic, Standard, Premium): `is_active = false`
- New plans: `is_active = true`

### Step 4: Restart Railway Service

1. Go back to Railway project dashboard
2. Click on your **web service** (StoryKeep app)
3. Click **⟳ Restart** or redeploy

### Step 5: Test Your Website

1. Visit https://storykeep.calmic.com.my
2. Homepage should load without "Internal Server Error"
3. Go to `/billing/plans` page
4. You should see only the NEW active subscription plans

---

## What This Fix Does

### Columns Added:
- `ai_enhancements_used`: Tracks monthly AI usage (colorization, sharpening, etc.)
- `ai_enhancements_reset_date`: When to reset the monthly counter
- `ai_enhancement_quota`: Monthly AI enhancement limit per plan

### Plans Deactivated:
- ✅ **Before**: Basic (RM 9.54), Standard (RM 21.09), Premium (RM 84.69) showing
- ✅ **After**: Only new active plans will display

---

## Troubleshooting

### If old plans still show:
1. Check the plan names in your database:
   ```sql
   SELECT name, display_name, is_active FROM subscription_plan;
   ```
2. Update the deactivation query to match the exact names
3. Clear your browser cache (Ctrl+Shift+R or Cmd+Shift+R)

### If website still crashes:
1. Check Railway deployment logs for errors
2. Verify the columns were actually added (use verification query)
3. Make sure you restarted the Railway service

---

## Alternative: Complete SQL File

I've also created `RAILWAY_COMPLETE_FIX.sql` which includes:
- All column additions
- Plan deactivation updates  
- Verification queries

You can run the entire file at once!

---

**Need Help?**
If you encounter issues:
1. Check Railway logs for specific error messages
2. Verify database connection is working
3. Ensure you're connected to the correct (production) database
