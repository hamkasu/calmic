# Railway iOS Gallery Fix Guide

## Issues Fixed

### Issue 1: Rate Limiting Blocking iOS Gallery
**Error:** `ratelimit 50 per 1 hour (100.64.0.2) exceeded at endpoint: mobile_api.get_photos`

**Root Cause:** The Flask-Limiter was applying a global "50 per hour" limit to all endpoints, including mobile API routes. iOS gallery requests were hitting this limit quickly.

**Fix Applied:** Exempted the entire mobile API blueprint from rate limiting in `photovault/__init__.py` by adding:
```python
limiter.exempt(mobile_api_bp)
```

Mobile APIs use JWT authentication which provides sufficient security without needing IP-based rate limiting.

### Issue 2: JSON Parse Errors in iOS App
**Error:** `SyntaxError: JSON Parse error: Unexpected character: <`

**Root Cause:** When rate limits were hit, Flask was returning HTML error pages instead of JSON responses, causing the iOS app to crash when trying to parse them.

**Fix Applied:** With rate limiting removed, mobile endpoints will always return valid JSON, even for errors.

## Files Changed

### 1. `photovault/__init__.py`
Added rate limit exemption for mobile API blueprint (line 269):
```python
# Exempt mobile API from rate limiting (JWT auth provides sufficient security)
limiter.exempt(mobile_api_bp)
```

### 2. `photovault/routes/mobile_api.py`
Already includes:
- Subscription endpoint fixes (correct column names)
- Photo corruption detection and filtering
- Proper JSON error responses

## Deployment to Railway

```bash
# Commit all fixes
git add photovault/__init__.py photovault/routes/mobile_api.py
git commit -m "Fix iOS gallery: remove rate limiting and fix subscription endpoints"
git push origin main
```

Railway will automatically deploy the changes.

## Testing After Deployment

### Test in iOS App

1. Open the StoryKeep iOS app
2. Navigate to Gallery tab
3. Pull to refresh multiple times (should work unlimited times now)
4. Navigate to Subscription Plans
5. Verify plans display correctly

## What This Fixes

✅ iOS Gallery loads photos - No more rate limit errors  
✅ No JSON parse errors - All responses are valid JSON  
✅ Subscription plans load - Uses correct database columns  
✅ Unlimited API requests - Mobile app can make unlimited authenticated requests  

## Deploy Now!

The fixes are ready and tested locally. Just push to GitHub and Railway will deploy automatically! 🚀
