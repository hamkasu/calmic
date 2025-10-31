# Subscription Upgrade Feature - Railway Deployment Guide

## Overview
This guide covers deploying the new subscription management feature that allows iOS users to upgrade from Free to paid plans.

## Changes Made

### Backend (Python/Flask)

1. **Auto-create Free Plan on Registration** (`photovault/routes/auth.py` & `photovault/routes/mobile_api.py`)
   - Both web and mobile registration now automatically create a Free plan subscription
   - New users get a 1-year Free plan subscription upon account creation

2. **New Mobile API Endpoints** (`photovault/routes/mobile_api.py`)
   - `GET /api/subscription/plans` - Returns all active subscription plans with features
   - `GET /api/subscription/current` - Returns user's current subscription details
   - `POST /api/subscription/upgrade` - Initiates subscription upgrade via Stripe checkout

### Frontend (React Native/Expo)

1. **New Subscription Plans Screen** (`StoryKeep-iOS/src/screens/SubscriptionPlansScreen.js`)
   - Displays all available plans with features and pricing
   - Shows current plan with visual indicator
   - Handles upgrade flow with confirmation dialog
   - Opens Stripe checkout URL in browser for payment

2. **API Service Methods** (`StoryKeep-iOS/src/services/api.js`)
   - Added `subscriptionAPI` with methods for plans, current subscription, and upgrades

3. **Navigation Updates** (`StoryKeep-iOS/App.js` & `StoryKeep-iOS/src/screens/SettingsScreen.js`)
   - Added "Subscription" menu item in Settings
   - Integrated SubscriptionPlansScreen into navigation

## Deployment Steps

### 1. Prepare for Deployment

```bash
# Ensure all changes are committed
git status
git add -A
git commit -m "Add subscription upgrade feature for iOS app"
```

### 2. Deploy to Railway

```bash
# Push to GitHub (Railway will auto-deploy)
git push origin main
```

### 3. Verify Stripe Configuration on Railway

Ensure these environment variables are set in Railway:

```
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

**Important**: Make sure each SubscriptionPlan in your database has a valid `stripe_price_id`:
- Free Plan: No Stripe price ID needed
- Personal Plan: `price_xxxxxxxxxxxxx`
- Family Plan: `price_xxxxxxxxxxxxx`
- Pro Plan: `price_xxxxxxxxxxxxx`

### 4. Update Stripe Price IDs (if needed)

If your Stripe price IDs need to be updated:

```sql
-- Connect to Railway production database
UPDATE subscription_plans SET stripe_price_id = 'price_xxxxxxxxxxxxx' WHERE name = 'Personal';
UPDATE subscription_plans SET stripe_price_id = 'price_xxxxxxxxxxxxx' WHERE name = 'Family';
UPDATE subscription_plans SET stripe_price_id = 'price_xxxxxxxxxxxxx' WHERE name = 'Pro';
```

### 5. Test the Complete Flow

1. **Register a new account** on Railway production:
   - User should automatically get a Free plan subscription

2. **Check subscription in database**:
   ```sql
   SELECT u.username, p.name as plan_name, s.status, s.current_period_end
   FROM users u
   LEFT JOIN user_subscriptions s ON u.id = s.user_id
   LEFT JOIN subscription_plans p ON s.plan_id = p.id
   WHERE u.username = 'test_user';
   ```

3. **Test iOS upgrade flow**:
   - Open the app and login
   - Go to Settings → Subscription
   - View available plans
   - Attempt to upgrade to a paid plan
   - Verify Stripe checkout opens in browser
   - Complete test payment
   - Verify subscription updated in database

## Development Mode vs Production

### Development Mode (Local Replit)
- No Stripe required
- Upgrades happen instantly without payment
- Good for testing the UI and flow

### Production Mode (Railway)
- Requires valid Stripe API keys
- Opens actual Stripe Checkout for payment
- Webhooks handle subscription updates

## Stripe Webhook Configuration

Make sure your Stripe webhook is configured to send events to:
```
https://storykeep.calmic.com.my/billing/webhook
```

Required webhook events:
- `checkout.session.completed`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

## Troubleshooting

### User doesn't have a subscription after registration
Check the logs for errors during Free plan creation. The user account is created even if subscription creation fails (graceful degradation).

### Upgrade fails with "Invalid plan" error
Verify that the plan exists in the database and has the correct `stripe_price_id`.

### Stripe checkout doesn't open
Check that:
1. `STRIPE_SECRET_KEY` is set in Railway
2. The plan has a valid `stripe_price_id`
3. The user's Stripe customer ID is created properly

### Can't downgrade plan
This is by design. Users must contact support for downgrades to prevent accidental data loss.

## Key Features

### Automatic Free Plan Assignment
- Every new user (web or mobile) gets a Free plan automatically
- No manual intervention required
- 1-year duration for Free plan

### Smart Upgrade Flow
- Displays current plan with visual indicator
- Shows featured plan (Family) with star badge
- Prevents upgrading to current plan
- Immediate upgrades with prorated billing
- Opens Stripe checkout in browser for payment

### Development-Friendly
- Works without Stripe in development mode
- Auto-detects Stripe configuration
- Graceful fallbacks for missing data

## Next Steps After Deployment

1. Test complete registration → Free plan → upgrade → payment flow
2. Monitor Stripe dashboard for successful payments
3. Check Railway logs for any errors
4. Verify user subscriptions are being created properly
5. Test edge cases (already subscribed, invalid plan, etc.)

## Support Contacts

If you encounter issues:
1. Check Railway logs first
2. Verify Stripe webhook events are being received
3. Check database for subscription records
4. Contact Calmic support team
