# Railway Subscription Endpoints Fix Guide

## Issue
iOS app getting 500 error when trying to load subscription plans from Railway production server.

**Error:** `Failed to load subscription data: AxiosError: Request failed with status code 500`

## Root Cause
The subscription endpoints (`/api/subscription/plans` and `/api/subscription/current`) were trying to access database columns that don't match the actual schema:
- Code was looking for: `ai_enhancements_per_month`, `family_vaults_limit`
- Actual columns are: `ai_enhancement_quota`, `max_family_vaults`

## Fix Applied
Updated `photovault/routes/mobile_api.py` to use the correct column names with proper fallbacks.

## Deployment Steps

### 1. Verify Railway Database Has Subscription Tables

Check if Railway has the required tables:

```sql
-- Check if subscription_plan table exists
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('subscription_plan', 'user_subscription');
```

If tables are missing, run migrations (see step 2).

### 2. Run Database Migrations on Railway

**Option A: Via Railway CLI**
```bash
# Connect to Railway project
railway link

# Run Flask migrations
railway run flask db upgrade
```

**Option B: Via Railway Shell**
1. Go to Railway Dashboard → Your Project → Settings → Shell
2. Run:
```bash
flask db upgrade
```

### 3. Verify Subscription Plans Are Seeded

Check if plans exist:
```sql
SELECT id, name, display_name, price_myr, storage_gb, ai_enhancement_quota, max_family_vaults
FROM subscription_plan
ORDER BY sort_order;
```

**Expected output:** 4 rows (free, personal, family, pro)

If empty, the plans should auto-seed when the server restarts. If not, manually seed:

```sql
-- Insert Free Plan
INSERT INTO subscription_plan (
    name, display_name, description, price_myr, sst_rate, storage_gb,
    max_family_vaults, ai_enhancement_quota, is_active, is_featured, sort_order,
    face_detection, photo_enhancement, smart_tagging, billing_period
) VALUES (
    'free', 'Free Plan', 'Get started with basic photo storage',
    0.00, 0.00, 0.50, 1, 5, true, false, 1,
    true, true, false, 'monthly'
);

-- Insert Personal Plan
INSERT INTO subscription_plan (
    name, display_name, description, price_myr, sst_rate, storage_gb,
    max_family_vaults, ai_enhancement_quota, is_active, is_featured, sort_order,
    face_detection, photo_enhancement, smart_tagging, billing_period
) VALUES (
    'personal', 'Personal Plan', 'Perfect for personal photo management',
    12.90, 6.00, 5.00, 2, 25, true, false, 2,
    true, true, true, 'monthly'
);

-- Insert Family Plan (Featured)
INSERT INTO subscription_plan (
    name, display_name, description, price_myr, sst_rate, storage_gb,
    max_family_vaults, ai_enhancement_quota, is_active, is_featured, sort_order,
    face_detection, photo_enhancement, smart_tagging, priority_support, billing_period
) VALUES (
    'family', 'Family Plan', 'Affordable storage for everyday photos',
    24.90, 6.00, 25.00, 5, 75, true, true, 3,
    true, true, true, true, 'monthly'
);

-- Insert Pro Plan
INSERT INTO subscription_plan (
    name, display_name, description, price_myr, sst_rate, storage_gb,
    max_family_vaults, ai_enhancement_quota, is_active, is_featured, sort_order,
    face_detection, photo_enhancement, smart_tagging, social_media_integration,
    api_access, priority_support, billing_period
) VALUES (
    'pro', 'Pro Plan', 'Unlimited storage and all premium features',
    49.90, 6.00, 500.00, 20, 500, true, false, 4,
    true, true, true, true, true, true, 'monthly'
);
```

### 4. Deploy Code Changes to Railway

**Option A: Via GitHub (Recommended)**
```bash
# Commit the changes
git add photovault/routes/mobile_api.py
git commit -m "Fix subscription endpoints - use correct database column names"
git push origin main
```

Railway will automatically deploy the new code.

**Option B: Via Railway CLI**
```bash
railway up
```

### 5. Test the Endpoints

After deployment, test with curl:

```bash
# Replace YOUR_AUTH_TOKEN with a valid JWT token
curl -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
     https://storykeep.calmic.com.my/api/subscription/plans

curl -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
     https://storykeep.calmic.com.my/api/subscription/current
```

Expected responses:

**Plans endpoint:**
```json
{
  "success": true,
  "plans": [
    {
      "id": 1,
      "name": "free",
      "display_name": "Free Plan",
      "price_myr": 0.0,
      "storage_gb": 0.5,
      "ai_enhancements_per_month": 5,
      "family_vaults_limit": 1,
      "is_current": true,
      "features": ["500MB Storage", "5 AI Enhancements/month", "1 Family Vault"]
    }
  ]
}
```

**Current subscription endpoint:**
```json
{
  "success": true,
  "subscription": {
    "plan_name": "Free",
    "plan_display_name": "Free Plan",
    "status": "active",
    "is_free": true,
    "storage_gb": 0.5,
    "ai_enhancements_per_month": 5,
    "family_vaults_limit": 1
  }
}
```

### 6. Test in iOS App

1. Open the iOS app
2. Navigate to Subscription Plans screen
3. Verify plans load without errors
4. Check that current subscription displays correctly

## Changes Made

### File: `photovault/routes/mobile_api.py`

**Changes in `/subscription/plans` endpoint:**
- Added `hasattr()` checks to safely access columns
- Uses `ai_enhancement_quota` instead of `ai_enhancements_per_month`
- Uses `max_family_vaults` instead of `family_vaults_limit`
- Added proper type casting with `float()` for numeric values
- Improved feature list formatting

**Changes in `/subscription/current` endpoint:**
- Fixed Free plan name lookup (changed from 'Free' to 'free')
- Added safe column access with fallback values
- Uses correct database column names
- Handles missing free plan gracefully

## Verification Checklist

- [ ] Database migrations applied successfully
- [ ] Subscription plans table has 4 rows
- [ ] Code changes deployed to Railway
- [ ] `/api/subscription/plans` returns 200 with plan data
- [ ] `/api/subscription/current` returns 200 with subscription data
- [ ] iOS app loads subscription plans without errors
- [ ] Current subscription displays correctly in app

## Troubleshooting

**Error: relation "subscription_plan" does not exist**
- Run: `flask db upgrade` on Railway

**Error: No subscription plans returned**
- Check if plans are seeded: `SELECT COUNT(*) FROM subscription_plan;`
- If zero, manually seed using SQL above or restart server

**Error: Still getting 500 error**
- Check Railway logs: `railway logs`
- Look for Python traceback showing exact error
- Verify column names match database schema

## Notes

- Local Replit server already has the fix applied and working
- Changes must be deployed to Railway for iOS app to benefit
- The fix is backward compatible and won't break existing functionality
