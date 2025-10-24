# Railway Update: 4 Subscription Plans

## What This Update Does

Reduces your subscription plans from 5 to 4 tiers by:
- ✅ Keeping: Free, Personal, Family, Pro
- ❌ Removing: Business Plan (deactivated, not deleted)
- ⬆️ Upgrading: Pro Plan now has 500GB storage and enhanced features

---

## New 4-Tier Structure

| Plan | Price (MYR/mo) | Storage | AI Enhancements | Family Vaults |
|------|----------------|---------|-----------------|---------------|
| **Free** | RM 0.00 | 500MB | 5/month | 1 |
| **Personal** | RM 12.90 | 5GB | 25/month | 2 |
| **Family** ⭐ | RM 24.90 | 25GB | 75/month | 5 |
| **Pro** | RM 49.90 | **500GB** | 500/month | 20 |

⭐ = Featured Plan

---

## Apply to Railway (3 Minutes)

### Step 1: Open Railway Database
1. Go to https://railway.app
2. Open your StoryKeep project
3. Click **PostgreSQL** service
4. Click **Data** tab → **Query**

### Step 2: Run the Update SQL

Copy and paste this into the query editor:

```sql
-- Deactivate old plans
UPDATE subscription_plan 
SET is_active = false 
WHERE LOWER(name) IN ('basic', 'standard', 'premium', 'business');

-- Update Pro Plan (now top tier with 500GB)
UPDATE subscription_plan 
SET 
    storage_gb = 500,
    max_family_vaults = 20,
    ai_enhancement_quota = 500,
    social_media_integration = true,
    description = 'Unlimited storage and all premium features'
WHERE LOWER(name) = 'pro';

-- Set Family Plan as featured
UPDATE subscription_plan 
SET is_featured = true
WHERE LOWER(name) = 'family';

-- Ensure other featured flags are off
UPDATE subscription_plan 
SET is_featured = false
WHERE LOWER(name) IN ('free', 'personal', 'pro');
```

### Step 3: Verify the Changes

Run this to confirm you have exactly 4 active plans:

```sql
SELECT name, display_name, price_myr, storage_gb, is_active, is_featured
FROM subscription_plan 
WHERE is_active = true
ORDER BY sort_order;
```

**Expected Output**: 4 rows (Free, Personal, Family, Pro)

### Step 4: Restart Railway Service

1. Go to Railway dashboard
2. Click your **web service**
3. Click **⟳ Restart** or redeploy

### Step 5: Test

Visit https://storykeep.calmic.com.my/billing/plans

You should see exactly **4 subscription plans**:
- Free Plan (RM 0.00)
- Personal Plan (RM 12.90)  
- Family Plan (RM 24.90) ⭐
- Pro Plan (RM 49.90)

---

## What Happens to Existing Business Plan Subscribers?

Don't worry! The Business Plan is **deactivated, not deleted**:
- ✅ Existing subscribers keep their Business Plan subscription
- ✅ They can continue using all features
- ❌ New users cannot subscribe to Business Plan
- 💡 You can manually migrate them to Pro Plan later if needed

---

## Local Environment (Replit)

Your local Replit environment has already been updated! ✅
- PhotoVault Server restarted with new 4-plan structure
- Changes applied automatically on startup

---

## Complete SQL File

For your reference, I've created `RAILWAY_UPDATE_4_PLANS.sql` with:
- Full update script
- Verification queries
- Safety checks

Run this file for a complete update with all verification steps included.

---

## Need to Revert?

If you want to bring back the Business Plan:

```sql
UPDATE subscription_plan 
SET is_active = true 
WHERE LOWER(name) = 'business';
```

---

**Questions?** Check the Railway logs or verify plans in the database!
