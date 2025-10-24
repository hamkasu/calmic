-- COMPLETE FIX for Railway Database
-- This includes both the missing columns AND deactivating old plans
-- Run this entire script in Railway's PostgreSQL Query editor

-- =================================================================
-- PART 1: Add Missing Columns (fixes the website crash)
-- =================================================================

-- Add AI enhancement tracking to user_subscription table
ALTER TABLE user_subscription 
ADD COLUMN IF NOT EXISTS ai_enhancements_used INTEGER NOT NULL DEFAULT 0;

ALTER TABLE user_subscription 
ADD COLUMN IF NOT EXISTS ai_enhancements_reset_date TIMESTAMP;

-- Add AI enhancement quota to subscription_plan table
ALTER TABLE subscription_plan 
ADD COLUMN IF NOT EXISTS ai_enhancement_quota INTEGER NOT NULL DEFAULT 0;

-- =================================================================
-- PART 2: Deactivate Old Plans (fixes the billing page)
-- =================================================================

-- Deactivate the old subscription plans (Basic, Standard, Premium)
-- The lowercase names match what's in your database
UPDATE subscription_plan 
SET is_active = false 
WHERE LOWER(name) IN ('basic', 'standard', 'premium');

-- Alternative: Also try with exact case matching
UPDATE subscription_plan 
SET is_active = false 
WHERE name IN ('Basic Plan', 'Standard Plan', 'Premium Plan', 'basic', 'standard', 'premium');

-- =================================================================
-- PART 3: Verification Queries
-- =================================================================

-- Verify columns were added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'user_subscription' 
AND column_name IN ('ai_enhancements_used', 'ai_enhancements_reset_date')
ORDER BY column_name;

-- Verify old plans are deactivated
SELECT id, name, display_name, is_active, price_myr 
FROM subscription_plan 
ORDER BY sort_order;

-- Show only active plans (these should be the new ones)
SELECT id, name, display_name, is_active, price_myr, ai_enhancement_quota 
FROM subscription_plan 
WHERE is_active = true
ORDER BY sort_order;
