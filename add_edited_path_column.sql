-- Add missing edited_path column to Railway database
-- Run this SQL in your Railway PostgreSQL database

ALTER TABLE photo ADD COLUMN IF NOT EXISTS edited_path VARCHAR(500);

-- Verify the column was added
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'photo' 
  AND column_name IN ('edited_path', 'edited_filename', 'enhancement_metadata')
ORDER BY column_name;
