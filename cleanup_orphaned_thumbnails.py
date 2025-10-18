#!/usr/bin/env python3
"""
Clean up orphaned thumbnail files (files without database records)
Removes thumbnail files that don't have corresponding photo records
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from photovault import create_app, db
from photovault.models import Photo

def cleanup_orphaned_thumbnails(dry_run=True):
    """Remove thumbnail files that don't have corresponding database records"""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("PhotoVault - Orphaned Thumbnails Cleanup")
        print("=" * 70)
        print()
        
        if dry_run:
            print("🔍 DRY RUN MODE - No files will be deleted")
            print("   Run with --execute to actually delete files")
        else:
            print("⚠️  EXECUTE MODE - Files will be permanently deleted")
        
        print()
        print("-" * 70)
        print()
        
        # Get upload folder from config
        upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
        
        if not os.path.exists(upload_folder):
            print(f"❌ Upload folder not found: {upload_folder}")
            return 1
        
        print(f"📁 Scanning upload folder: {upload_folder}")
        print()
        
        # Find all thumbnail files
        orphaned_thumbnails = []
        total_thumbnails = 0
        
        for root, dirs, files in os.walk(upload_folder):
            for filename in files:
                if '_thumb.' in filename:
                    total_thumbnails += 1
                    filepath = os.path.join(root, filename)
                    
                    # Extract original filename from thumbnail
                    # Format: original_name_thumb.ext or enhanced.date.id_thumb.ext
                    original_filename = filename.replace('_thumb.', '.')
                    
                    # Also check for the pattern without _thumb
                    base_filename = filename.split('_thumb.')[0]
                    
                    # Check if photo record exists in database
                    photo = Photo.query.filter(
                        (Photo.filename == original_filename) |
                        (Photo.filename.like(f"{base_filename}%"))
                    ).first()
                    
                    if not photo:
                        orphaned_thumbnails.append(filepath)
                        print(f"❌ Orphaned thumbnail: {filename}")
                        print(f"   Path: {filepath}")
                        print()
        
        print(f"📊 Total thumbnails found: {total_thumbnails}")
        print(f"🔴 Orphaned thumbnails: {len(orphaned_thumbnails)}")
        print()
        
        if not orphaned_thumbnails:
            print("✨ No orphaned thumbnails found! All thumbnails have corresponding records.")
            return 0
        
        # Perform cleanup if not dry run
        if not dry_run:
            print("-" * 70)
            print("🗑️  Deleting orphaned thumbnails...")
            print("-" * 70)
            print()
            
            deleted_count = 0
            for filepath in orphaned_thumbnails:
                try:
                    os.remove(filepath)
                    print(f"  ✓ Deleted: {os.path.basename(filepath)}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  ❌ Error deleting {filepath}: {e}")
            
            print()
            print(f"✅ Successfully deleted {deleted_count} orphaned thumbnails")
            print()
        else:
            print("-" * 70)
            print("💡 To delete these thumbnails, run:")
            print("   python cleanup_orphaned_thumbnails.py --execute")
            print("-" * 70)
            print()
        
        # Summary
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        
        if dry_run:
            print(f"📋 Found {len(orphaned_thumbnails)} orphaned thumbnail files")
            print(f"   Run with --execute to remove them from storage")
        else:
            print(f"✅ Cleanup complete!")
            print(f"   Deleted: {deleted_count} thumbnails")
            print(f"   Remaining: {total_thumbnails - deleted_count} thumbnails")
        
        print()
        
        return 0

if __name__ == '__main__':
    # Check command line arguments
    execute_mode = '--execute' in sys.argv or '-e' in sys.argv
    
    # Run cleanup
    exit_code = cleanup_orphaned_thumbnails(dry_run=not execute_mode)
    sys.exit(exit_code)
