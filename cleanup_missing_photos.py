#!/usr/bin/env python3
"""
Database Cleanup Script - Remove Photo Records for Missing Files
Safely removes database entries for photos that no longer exist in storage
"""
import os
import sys
from photovault import create_app, db
from photovault.models import Photo

def cleanup_missing_photos(dry_run=True):
    """
    Remove photo records where the actual file is missing
    
    Args:
        dry_run: If True, only show what would be deleted without actually deleting
    """
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("PhotoVault - Missing Photos Cleanup")
        print("=" * 70)
        print()
        
        if dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
            print("   Run with --execute to actually delete records")
        else:
            print("⚠️  EXECUTE MODE - Records will be permanently deleted")
        
        print()
        print("-" * 70)
        print()
        
        # Get all photos from database
        all_photos = Photo.query.all()
        total_photos = len(all_photos)
        
        print(f"📊 Total photos in database: {total_photos}")
        print()
        
        # Check which files are missing
        missing_photos = []
        existing_photos = []
        
        for photo in all_photos:
            file_path = photo.file_path
            
            # Check if file exists
            if os.path.exists(file_path):
                existing_photos.append(photo)
            else:
                missing_photos.append(photo)
        
        print(f"✅ Photos with existing files: {len(existing_photos)}")
        print(f"🔴 Photos with missing files: {len(missing_photos)}")
        print()
        
        if not missing_photos:
            print("✨ No cleanup needed! All photo records have corresponding files.")
            return 0
        
        # Show details of missing photos
        print("-" * 70)
        print("Missing Photos Details:")
        print("-" * 70)
        
        for photo in missing_photos:
            print(f"  ID: {photo.id}")
            print(f"  Filename: {photo.filename}")
            print(f"  Original: {photo.original_name}")
            print(f"  User ID: {photo.user_id}")
            print(f"  Path: {photo.file_path}")
            print(f"  Upload Date: {photo.created_at}")
            print()
        
        # Perform cleanup if not dry run
        if not dry_run:
            print("-" * 70)
            print("🗑️  Deleting records for missing photos...")
            print("-" * 70)
            print()
            
            deleted_count = 0
            for photo in missing_photos:
                try:
                    print(f"  Deleting: {photo.filename} (ID: {photo.id})")
                    db.session.delete(photo)
                    deleted_count += 1
                except Exception as e:
                    print(f"  ❌ Error deleting {photo.filename}: {e}")
            
            # Commit all deletions
            try:
                db.session.commit()
                print()
                print(f"✅ Successfully deleted {deleted_count} photo records")
                print()
            except Exception as e:
                db.session.rollback()
                print()
                print(f"❌ Error committing changes: {e}")
                print("   All changes have been rolled back")
                return 1
        else:
            print("-" * 70)
            print("💡 To delete these records, run:")
            print("   railway run python cleanup_missing_photos.py --execute")
            print("-" * 70)
            print()
        
        # Summary
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        
        if dry_run:
            print(f"📋 Found {len(missing_photos)} photo records with missing files")
            print(f"   Run with --execute to remove them from database")
        else:
            print(f"✅ Cleanup complete!")
            print(f"   Deleted: {deleted_count} records")
            print(f"   Remaining: {len(existing_photos)} photos")
        
        print()
        
        # Show storage recommendations
        if missing_photos:
            print("-" * 70)
            print("⚠️  IMPORTANT: Prevent future data loss")
            print("-" * 70)
            print()
            print("These photos were lost because Railway storage is ephemeral.")
            print("To prevent this from happening again:")
            print()
            print("1. Add Railway Volume:")
            print("   - Railway Dashboard → Service → Settings → Volumes")
            print("   - New Volume → Mount path: /data")
            print()
            print("2. Set environment variable:")
            print("   - UPLOAD_FOLDER=/data/uploads")
            print()
            print("3. Redeploy your app")
            print()
            print("4. Verify with: railway run python verify_railway_config.py")
            print()
        
        return 0

if __name__ == '__main__':
    # Check command line arguments
    execute_mode = '--execute' in sys.argv or '-e' in sys.argv
    
    # Run cleanup
    exit_code = cleanup_missing_photos(dry_run=not execute_mode)
    sys.exit(exit_code)
