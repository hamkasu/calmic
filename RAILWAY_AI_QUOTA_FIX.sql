-- Fix for Railway database: Add missing AI enhancement tracking columns
-- Run this SQL script in your Railway PostgreSQL database

-- Add AI enhancement tracking columns to user_subscription table
ALTER TABLE user_subscription 
ADD COLUMN IF NOT EXISTS ai_enhancements_used INTEGER NOT NULL DEFAULT 0;

ALTER TABLE user_subscription 
ADD COLUMN IF NOT EXISTS ai_enhancements_reset_date TIMESTAMP;

-- Add AI enhancement quota column to subscription_plan table
ALTER TABLE subscription_plan 
ADD COLUMN IF NOT EXISTS ai_enhancement_quota INTEGER NOT NULL DEFAULT 0;

-- Optionally: Change storage_gb to support decimal values (e.g., 0.5 GB)
-- Only run this if you haven't already done it
-- ALTER TABLE subscription_plan 
-- ALTER COLUMN storage_gb TYPE NUMERIC(10,2);

-- Verify the columns were added successfully
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'user_subscription' 
AND column_name IN ('ai_enhancements_used', 'ai_enhancements_reset_date')
ORDER BY column_name;

SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'subscription_plan' 
AND column_name = 'ai_enhancement_quota';
