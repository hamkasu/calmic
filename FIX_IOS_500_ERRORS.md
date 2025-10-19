# Fix iOS App 500 Errors - Railway Database Migration

## Problem
Your iOS app connects to Railway successfully but gets **500 errors** when loading:
- Dashboard statistics
- User profile

## Root Cause Found ✅
Railway's PostgreSQL database is **missing columns** that exist in your local Replit database. The mobile API code tries to query these columns, causing database errors.

**Missing columns:**
- `user.profile_picture` - User avatar
- `photo.file_size` - Photo file size
- `photo.edited_filename` - Edited photo filename
- `photo.enhancement_metadata` - Enhancement data
- Plus 10+ other metadata columns

## Solution: Run Database Migration on Railway

### Option 1: Using Railway Dashboard (Recommended - Easiest)

1. **Go to Railway Dashboard**
   - Visit https://railway.app/
   - Open your project
   - Click on your **PostgreSQL database**

2. **Open the Data Tab**
   - Click the "Data" tab
   - Click "Query" button

3. **Copy and Paste the Migration SQL**
   - Open the file `railway_add_missing_columns.sql` from this Replit
   - Copy ALL the SQL content
   - Paste it into the Railway query editor

4. **Run the Migration**
   - Click "Run Query" or press Ctrl+Enter
   - Wait for completion messages
   - You should see: "✅ Migration complete!"

5. **Restart Your Railway App**
   - Go back to your Railway project
   - Click on your **web service** (not the database)
   - Click "Restart" from the menu

6. **Test Your iOS App**
   - Close and reopen the StoryKeep app
   - Try logging in
   - Dashboard should load without errors!

---

### Option 2: Using Railway CLI

```bash
# Install Railway CLI (if not already installed)
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Connect to database and run migration
railway run psql < railway_add_missing_columns.sql
```

---

### Option 3: Using psql Directly

If you have PostgreSQL client installed:

```bash
# Get your Railway database URL from Railway dashboard
# It looks like: postgresql://user:password@host:port/database

# Run migration
psql "YOUR_RAILWAY_DATABASE_URL" < railway_add_missing_columns.sql
```

---

## Verification

After running the migration, test these endpoints:

```bash
# Test login (replace with your credentials)
curl -X POST https://extraordinary-contentment-production.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpassword"}'

# Should return: {"success":true,"token":"...","user":{...}}

# Test dashboard (replace TOKEN with the token from login)
curl https://extraordinary-contentment-production.up.railway.app/api/dashboard \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Should return: {"total_photos":...,"enhanced_photos":...} with status 200
```

---

## What This Migration Does

The SQL file safely adds all missing columns to your Railway database:
- ✅ Checks if each column exists before adding
- ✅ Won't break if columns already exist
- ✅ Adds proper data types and defaults
- ✅ Provides status messages for each operation

---

## Expected Result

After the migration:
- ✅ iOS app dashboard loads successfully
- ✅ User profile displays correctly
- ✅ No more 500 errors
- ✅ All mobile app features work

---

## Troubleshooting

**If you still get 500 errors after migration:**

1. Check Railway logs for specific errors:
   - Go to Railway dashboard
   - Click your web service
   - View the "Deployments" or "Logs" tab

2. Verify columns were added:
   ```sql
   SELECT column_name FROM information_schema.columns 
   WHERE table_name='user' ORDER BY column_name;
   ```

3. Make sure you restarted the Railway app after migration

**Need help?** Share the error message from Railway logs and I can assist further.
