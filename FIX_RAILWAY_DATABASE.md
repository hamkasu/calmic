# Fix Railway Database Issues

This guide fixes two critical issues in your Railway production database:
1. Missing `mfa_secret` table
2. Corrupted photo filenames showing as error messages

## Issue 1: Missing MFA Table

### Problem
The `mfa_secret` table doesn't exist in Railway, causing errors:
```
relation "mfa_secret" does not exist
```

### Solution: Run Database Migration

**Step 1: Push the migration to GitHub**
```bash
git add migrations/versions/e4254a8d276f_add_mfa_secret_table.py
git commit -m "Add MFA secret table migration for Railway"
git push origin main
```

**Step 2: Run migration on Railway**

Option A - Using Railway CLI (Recommended):
```bash
# Install Railway CLI if not already installed
npm i -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Run the migration
railway run flask db upgrade
```

Option B - Using Railway's Shell:
1. Go to Railway dashboard
2. Open your PhotoVault service
3. Click on "Shell" tab
4. Run: `flask db upgrade`

**Step 3: Verify migration**
```bash
railway run flask db current
```

You should see: `e4254a8d276f (head)` indicating the migration was successful.

---

## Issue 2: Corrupted Photo Filenames

### Problem
Some photos have error messages stored as filenames:
```
filename: "(f,"'int' object is not iterable")"
URL: /uploads/2/(f,"'int' object is not iterable")
```

This causes images to display as placeholders.

### Solution: Clean Up Corrupted Data

**Step 1: Create cleanup script**

Save this as `fix_corrupted_photos.py`:

```python
"""
Fix corrupted photo filenames in Railway database
Run this script on Railway to clean up malformed data
"""
from photovault import create_app
from photovault.models import Photo
from photovault.extensions import db
import re

app = create_app()

with app.app_context():
    # Find photos with corrupted filenames
    all_photos = Photo.query.all()
    corrupted_count = 0
    fixed_count = 0
    deleted_count = 0
    
    for photo in all_photos:
        # Check if filename looks like an error message
        if photo.filename and (
            '(' in photo.filename or 
            ')' in photo.filename or
            'error' in photo.filename.lower() or
            'object' in photo.filename.lower() or
            'iterable' in photo.filename.lower() or
            not re.match(r'^[\w\-\.]+$', photo.filename)
        ):
            corrupted_count += 1
            print(f"Found corrupted photo ID {photo.id}: {photo.filename}")
            
            # Option 1: Try to recover from original_name
            if photo.original_name and re.match(r'^[\w\-\.]+$', photo.original_name):
                print(f"  → Recovering from original_name: {photo.original_name}")
                photo.filename = photo.original_name
                fixed_count += 1
            
            # Option 2: Delete the corrupted record if unrecoverable
            else:
                print(f"  → Cannot recover, deleting photo record ID {photo.id}")
                db.session.delete(photo)
                deleted_count += 1
    
    # Commit changes
    if corrupted_count > 0:
        print(f"\nSummary:")
        print(f"  Found: {corrupted_count} corrupted photos")
        print(f"  Fixed: {fixed_count} photos")
        print(f"  Deleted: {deleted_count} unrecoverable records")
        
        confirm = input("\nCommit these changes? (yes/no): ")
        if confirm.lower() == 'yes':
            db.session.commit()
            print("✓ Changes committed successfully")
        else:
            db.session.rollback()
            print("✗ Changes rolled back")
    else:
        print("✓ No corrupted photos found!")
```

**Step 2: Upload and run the script on Railway**

```bash
# Add the script to your repo
git add fix_corrupted_photos.py
git commit -m "Add database cleanup script for corrupted photos"
git push origin main

# Wait for Railway to deploy, then run it
railway run python fix_corrupted_photos.py
```

**Step 3: Verify the fix**

Check your Railway app - the photos should now load properly instead of showing placeholders.

---

## Prevention: Add Error Handling

To prevent future filename corruption, the codebase should validate filenames before saving to database. This has been added to local development code.

---

## Quick Deployment Checklist

- [ ] Push migration file to GitHub
- [ ] Run `flask db upgrade` on Railway
- [ ] Verify migration with `flask db current`
- [ ] Push cleanup script to GitHub  
- [ ] Run cleanup script on Railway
- [ ] Test the app - photos should load correctly
- [ ] MFA functionality should work without errors

---

## Testing

After applying both fixes:

1. **Test MFA**: Try setting up 2FA on a test account
2. **Test Photos**: Browse your photo gallery - all images should load
3. **Check Logs**: No more "mfa_secret does not exist" errors
4. **Upload New Photos**: Verify new uploads work correctly

---

## Need Help?

If you encounter issues:
1. Check Railway logs for error messages
2. Verify database connection is working
3. Ensure all migrations ran successfully
4. Contact support with specific error messages
