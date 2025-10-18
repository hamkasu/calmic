# Railway Billing Plans Error - Quick Fix Guide

## Problem
Getting "Internal Server Error" on `/billing/plans` page on Railway deployment.

## Most Common Causes & Fixes

### 1. PostgreSQL Database Not Configured ⭐ MOST LIKELY

**Symptoms:** 
- Internal Server Error on /billing/plans
- Database connection errors in logs
- "relation does not exist" errors

**Fix:**
1. Go to your Railway dashboard
2. Navigate to your PhotoVault project
3. Click **"+ New"** → **Database** → **PostgreSQL**
4. Railway will automatically set `DATABASE_URL`
5. **Redeploy** your app
6. Run migrations: `railway run flask db upgrade`

### 2. Database Migrations Not Run

**Symptoms:**
- Error: "relation 'subscription_plan' does not exist"
- Tables missing from database

**Fix:**
```bash
# Connect to your Railway project
railway link

# Run database migrations
railway run flask db upgrade

# Verify tables exist
railway run python railway_diagnose.py
```

### 3. Environment Variables Missing

**Required Variables:**
- `DATABASE_URL` - Auto-set when you add PostgreSQL
- `FLASK_CONFIG=production` - Set manually
- `SECRET_KEY` - Set manually (for session persistence)

**Fix:**
```bash
# Set Flask config to production
railway variables set FLASK_CONFIG=production

# Set secret key
railway variables set SECRET_KEY=$(openssl rand -base64 32)

# Verify all variables
railway variables
```

### 4. Subscription Plans Not Seeded

**Symptoms:**
- Empty pricing page (no plans shown)
- No errors but page is blank

**Fix:**
The app now auto-seeds plans on first access to /billing/plans. If this fails:

```bash
# Run Python shell on Railway
railway run flask shell

# Manually seed plans
>>> from photovault import create_app, _seed_subscription_plans
>>> app = create_app()
>>> with app.app_context():
...     _seed_subscription_plans(app)
>>> exit()
```

## Diagnostic Commands

### Check Configuration
```bash
# Run diagnostic script
railway run python railway_diagnose.py
```

### Check Logs
```bash
# View recent logs
railway logs

# Follow logs in real-time
railway logs -f
```

### Check Database
```bash
# Connect to database
railway run flask shell

# Check if subscription_plan table exists
>>> from photovault.models import SubscriptionPlan
>>> SubscriptionPlan.query.count()
>>> SubscriptionPlan.query.all()
```

## Complete Setup Checklist

- [ ] PostgreSQL database added to Railway project
- [ ] `DATABASE_URL` environment variable auto-set
- [ ] `FLASK_CONFIG=production` environment variable set
- [ ] `SECRET_KEY` environment variable set
- [ ] Database migrations run: `railway run flask db upgrade`
- [ ] App redeployed after all changes
- [ ] Diagnostic script shows all green: `railway run python railway_diagnose.py`
- [ ] /billing/plans page loads successfully

## Still Having Issues?

1. **Run the diagnostic:**
   ```bash
   railway run python railway_diagnose.py
   ```

2. **Check the logs:**
   ```bash
   railway logs | grep -i error
   ```

3. **Verify database connectivity:**
   ```bash
   railway run flask shell
   >>> from photovault.extensions import db
   >>> db.session.execute(db.text('SELECT 1')).scalar()
   ```

4. **Check subscription plans:**
   ```bash
   railway run flask shell
   >>> from photovault.models import SubscriptionPlan
   >>> plans = SubscriptionPlan.query.all()
   >>> print(f"Found {len(plans)} plans")
   >>> for p in plans:
   ...     print(f"- {p.name}: {p.display_name}")
   ```

## Quick One-Line Fix (Most Cases)

If PostgreSQL is not configured:
```bash
# Add PostgreSQL via Railway dashboard, then:
railway run flask db upgrade && railway up
```

This should fix 90% of Railway billing plan errors.
