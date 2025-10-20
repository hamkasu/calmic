# Railway Deployment Guide: People Page Flashing Fix

## Issue
The People page was flashing/flickering on Railway due to deprecated SQLAlchemy 2.0 pagination method causing continuous page reloads.

## Root Cause
- The `/people` route used `Query.paginate()` which was removed in SQLAlchemy 2.0
- This caused `AttributeError` exceptions on every page load
- The exception handler re-rendered the page with `people=None`, creating a flash/flicker loop
- Railway production uses SQLAlchemy 2.0, triggering the issue

## Fix Applied
Updated `photovault/routes/main.py` line 324-348 to use SQLAlchemy 2.0 compatible pagination:

**Before (Deprecated):**
```python
people = Person.query.filter_by(user_id=current_user.id).order_by(Person.name.asc()).paginate(
    page=page, per_page=12, error_out=False
)
```

**After (SQLAlchemy 2.0):**
```python
from sqlalchemy import select

# Use select() with where() clause for SQLAlchemy 2.0
stmt = select(Person).where(Person.user_id == current_user.id).order_by(Person.name.asc())
people = db.paginate(stmt, page=page, per_page=per_page, error_out=False)
```

**Important:** Note the use of `.where()` instead of `.filter_by()`. SQLAlchemy 2.0 Select objects do not support `.filter_by()` method.

## Deployment Steps

### 1. Commit and Push Changes
```bash
git add photovault/routes/main.py
git commit -m "Fix People page flashing - upgrade to SQLAlchemy 2.0 pagination"
git push origin main
```

### 2. Railway Auto-Deploy
Railway will automatically detect the push and redeploy your application.

### 3. Verify the Fix
1. Visit your Railway app: `https://web-production-535bd.up.railway.app/people`
2. Log in and navigate to the People page
3. Verify the page loads without flashing or flickering
4. Test adding a new person
5. Test editing an existing person
6. Test pagination if you have more than 12 people

### 4. Monitor Logs
Check Railway logs for any errors:
```bash
railway logs
```

Look for:
- ✅ No `AttributeError` exceptions
- ✅ Successful page loads: `"GET /people HTTP/1.1" 200`
- ✅ Database queries executing without errors

## Expected Behavior After Fix
- People page loads instantly without flashing
- Pagination works smoothly (12 people per page)
- Add/Edit/Delete person operations work correctly
- No console errors in browser developer tools
- No server-side AttributeError exceptions in Railway logs

## Related Fixes
This is the same pagination issue previously fixed in:
- Gallery page (`/api/photos` endpoint)
- Dashboard statistics

All SQLAlchemy 2.0 pagination is now consistent across the application.

## Testing Checklist
- [x] Local testing: People page loads without errors
- [x] Server restart: No exceptions in logs
- [ ] Railway deployment: Push changes to production
- [ ] Production testing: Verify no flashing on Railway
- [ ] Browser testing: Check developer console for errors
- [ ] Pagination testing: Navigate through multiple pages

## Support
If issues persist after deployment:
1. Check Railway logs for specific error messages
2. Verify SQLAlchemy version: `pip show SQLAlchemy` (should be 2.0.25)
3. Clear browser cache and hard refresh
4. Check network tab in browser developer tools for failed requests
