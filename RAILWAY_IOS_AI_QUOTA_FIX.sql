-- =================================================================
-- RAILWAY AI QUOTA FIX
-- Adds missing AI enhancement quota columns and configures plans
-- Fixes iOS error: "You've reached your monthly AI enhancement limit (0 enhancements)"
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
