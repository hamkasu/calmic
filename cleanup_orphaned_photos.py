#!/usr/bin/env python3
"""
Clean up orphaned photo records (database entries with missing files)
Run this after mounting Railway Volume to remove old photo records whose files were deleted
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from photovault import create_app, db
from photovault.models import Photo

def cleanup_orphaned_photos():
    """Remove photo records from database where files don't exist"""
    app = create_app()
    
    with app.app_context():
        # Get all photos
        all_photos = Photo.query.all()
        total = len(all_photos)
        orphaned = []
        
        print(f"Checking {total} photo records for missing files...")
        print()
        
        for photo in all_photos:
            file_exists = False
            
            # Check if file exists on disk
            if os.path.exists(photo.file_path):
                file_exists = True
            
            # Check if file exists in App Storage (if available)
            try:
                from photovault.services.app_storage_service import app_storage
                app_storage_path = f"users/{photo.user_id}/{photo.filename}"
                if app_storage.file_exists(app_storage_path):
                    file_exists = True
            except:
                pass
            
            if not file_exists:
                orphaned.append(photo)
                print(f"❌ Orphaned: {photo.filename} (ID: {photo.id}, User: {photo.user_id})")
                print(f"   Path: {photo.file_path}")
                print()
        
        if not orphaned:
            print("✅ No orphaned photos found! All database records have matching files.")
            return
        
        print(f"\nFound {len(orphaned)} orphaned photo records (files missing)")
        print(f"These are likely photos uploaded before Railway Volume was mounted.")
        print()
        
        response = input(f"Delete these {len(orphaned)} orphaned records from database? (yes/no): ").lower().strip()
        
        if response == 'yes':
            for photo in orphaned:
                db.session.delete(photo)
            
            db.session.commit()
            print(f"\n✅ Successfully deleted {len(orphaned)} orphaned photo records")
            print("Your photo gallery will now only show photos with actual files.")
        else:
            print("\n❌ Cleanup cancelled. No changes made.")

if __name__ == '__main__':
    cleanup_orphaned_photos()
