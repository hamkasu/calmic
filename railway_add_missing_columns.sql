-- Railway Database Migration: Add Missing Columns for iOS Mobile App
-- Run this on your Railway PostgreSQL database to fix 500 errors

-- Add profile_picture column to user table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='user' AND column_name='profile_picture'
    ) THEN
        ALTER TABLE "user" ADD COLUMN profile_picture VARCHAR(500);
        RAISE NOTICE 'Added profile_picture column to user table';
    ELSE
        RAISE NOTICE 'profile_picture column already exists';
    END IF;
END $$;

-- Add file_size column to photo table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='photo' AND column_name='file_size'
    ) THEN
        ALTER TABLE photo ADD COLUMN file_size INTEGER;
        RAISE NOTICE 'Added file_size column to photo table';
    ELSE
        RAISE NOTICE 'file_size column already exists';
    END IF;
END $$;

-- Add edited_filename column to photo table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='photo' AND column_name='edited_filename'
    ) THEN
        ALTER TABLE photo ADD COLUMN edited_filename VARCHAR(255);
        RAISE NOTICE 'Added edited_filename column to photo table';
    ELSE
        RAISE NOTICE 'edited_filename column already exists';
    END IF;
END $$;

-- Add edited_path column to photo table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='photo' AND column_name='edited_path'
    ) THEN
        ALTER TABLE photo ADD COLUMN edited_path VARCHAR(500);
        RAISE NOTICE 'Added edited_path column to photo table';
    ELSE
        RAISE NOTICE 'edited_path column already exists';
    END IF;
END $$;

-- Add auto_enhanced column to photo table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='photo' AND column_name='auto_enhanced'
    ) THEN
        ALTER TABLE photo ADD COLUMN auto_enhanced BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added auto_enhanced column to photo table';
    ELSE
        RAISE NOTICE 'auto_enhanced column already exists';
    END IF;
END $$;

-- Add enhancement_metadata column to photo table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='photo' AND column_name='enhancement_metadata'
    ) THEN
        ALTER TABLE photo ADD COLUMN enhancement_metadata TEXT;
        RAISE NOTICE 'Added enhancement_metadata column to photo table';
    ELSE
        RAISE NOTICE 'enhancement_metadata column already exists';
    END IF;
END $$;

-- Add processing_notes column to photo table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='photo' AND column_name='processing_notes'
    ) THEN
        ALTER TABLE photo ADD COLUMN processing_notes TEXT;
        RAISE NOTICE 'Added processing_notes column to photo table';
    ELSE
        RAISE NOTICE 'processing_notes column already exists';
    END IF;
END $$;

-- Add back_text column to photo table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='photo' AND column_name='back_text'
    ) THEN
        ALTER TABLE photo ADD COLUMN back_text TEXT;
        RAISE NOTICE 'Added back_text column to photo table';
    ELSE
        RAISE NOTICE 'back_text column already exists';
    END IF;
END $$;

-- Add date_text column to photo table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='photo' AND column_name='date_text'
    ) THEN
        ALTER TABLE photo ADD COLUMN date_text VARCHAR(255);
        RAISE NOTICE 'Added date_text column to photo table';
    ELSE
        RAISE NOTICE 'date_text column already exists';
    END IF;
END $$;

-- Add location_text column to photo table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='photo' AND column_name='location_text'
    ) THEN
        ALTER TABLE photo ADD COLUMN location_text VARCHAR(255);
        RAISE NOTICE 'Added location_text column to photo table';
    ELSE
        RAISE NOTICE 'location_text column already exists';
    END IF;
END $$;

-- Add occasion column to photo table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='photo' AND column_name='occasion'
    ) THEN
        ALTER TABLE photo ADD COLUMN occasion VARCHAR(255);
        RAISE NOTICE 'Added occasion column to photo table';
    ELSE
        RAISE NOTICE 'occasion column already exists';
    END IF;
END $$;

-- Add photo_date column to photo table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='photo' AND column_name='photo_date'
    ) THEN
        ALTER TABLE photo ADD COLUMN photo_date TIMESTAMP;
        RAISE NOTICE 'Added photo_date column to photo table';
    ELSE
        RAISE NOTICE 'photo_date column already exists';
    END IF;
END $$;

-- Add condition column to photo table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='photo' AND column_name='condition'
    ) THEN
        ALTER TABLE photo ADD COLUMN condition VARCHAR(50);
        RAISE NOTICE 'Added condition column to photo table';
    ELSE
        RAISE NOTICE 'condition column already exists';
    END IF;
END $$;

-- Add photo_source column to photo table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='photo' AND column_name='photo_source'
    ) THEN
        ALTER TABLE photo ADD COLUMN photo_source VARCHAR(100);
        RAISE NOTICE 'Added photo_source column to photo table';
    ELSE
        RAISE NOTICE 'photo_source column already exists';
    END IF;
END $$;

-- Add needs_restoration column to photo table (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='photo' AND column_name='needs_restoration'
    ) THEN
        ALTER TABLE photo ADD COLUMN needs_restoration BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added needs_restoration column to photo table';
    ELSE
        RAISE NOTICE 'needs_restoration column already exists';
    END IF;
END $$;

-- Display success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration complete! All missing columns have been added.';
    RAISE NOTICE '✅ Your iOS app should now work without 500 errors.';
END $$;
