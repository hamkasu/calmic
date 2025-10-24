-- Update Railway Database to Show Only 4 Subscription Plans
-- This deactivates all old plans and ensures only the new 4-tier structure is active

-- =================================================================
-- STEP 1: Deactivate ALL old plans first
-- =================================================================

-- Deactivate old plan names (case-insensitive)
UPDATE subscription_plan 
SET is_active = false 
WHERE LOWER(name) IN ('basic', 'standard', 'premium', 'business');

-- Also deactivate by display name in case they're named differently
UPDATE subscription_plan 
SET is_active = false 
WHERE display_name IN ('Basic Plan', 'Standard Plan', 'Premium Plan', 'Business Plan');

-- =================================================================
-- STEP 2: Ensure the new 4 plans are properly configured
-- =================================================================

-- Update Pro Plan with enhanced features (now the top tier)
UPDATE subscription_plan 
SET 
    display_name = 'Pro Plan',
    description = 'Unlimited storage and all premium features',
    storage_gb = 500,
    max_family_vaults = 20,
    ai_enhancement_quota = 500,
    social_media_integration = true,
    is_active = true,
    sort_order = 4
WHERE LOWER(name) = 'pro';

-- Ensure Family Plan is featured
UPDATE subscription_plan 
SET 
    is_featured = true,
    is_active = true,
    sort_order = 3
WHERE LOWER(name) = 'family';

-- Ensure Personal Plan is active
UPDATE subscription_plan 
SET 
    is_active = true,
    is_featured = false,
    sort_order = 2
WHERE LOWER(name) = 'personal';

-- Ensure Free Plan is active
UPDATE subscription_plan 
SET 
    is_active = true,
    is_featured = false,
    sort_order = 1
WHERE LOWER(name) = 'free';

-- =================================================================
-- STEP 3: Verification Queries
-- =================================================================

-- Show all plans with their active status
SELECT 
    id, 
    name, 
    display_name, 
    price_myr, 
    storage_gb,
    ai_enhancement_quota,
    is_active, 
    is_featured,
    sort_order
FROM subscription_plan 
ORDER BY is_active DESC, sort_order;

-- Show only active plans (should be exactly 4)
SELECT 
    COUNT(*) as active_plan_count,
    string_agg(display_name, ', ' ORDER BY sort_order) as active_plans
FROM subscription_plan 
WHERE is_active = true;

-- Expected output: 
-- active_plan_count: 4
-- active_plans: Free Plan, Personal Plan, Family Plan, Pro Plan
