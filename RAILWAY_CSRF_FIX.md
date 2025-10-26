# Railway Deployment Guide - CSRF Fix for iOS Upload

## Problem
iOS app shows CSRF error when uploading photos from camera roll to vaults:
```
ERROR: Upload failed: 400 <!doctype html>
The CSRF token is missing.
ERROR: Camera library upload error: [Error: Upload failed: 400]
```

## Root Cause Analysis
**Route Conflict:** Both `upload_bp` and `mobile_api_bp` defined `/api/upload` routes, causing Flask to route ALL requests to whichever blueprint was registered first. This created a conflict where mobile clients (using JWT) hit web routes (requiring CSRF tokens) or vice versa.

## Solution: Path Separation
Implement proper API path separation:

| Client Type | Endpoint | Blueprint | Authentication | CSRF |
|------------|----------|-----------|----------------|------|
| **Mobile App** | `/api/upload` | mobile_api_bp | JWT Token | Exempt |
| **Web Browser** | `/api/web/upload` | photo_bp | Session Cookie | Required |

### Changes Made:

1. **Web Frontend** (`templates/upload.html`):
   - Changed upload endpoint from `/api/upload` → `/api/web/upload`
   
2. **Web Backend** (`photovault/routes/photo.py`):
   - Removed `@csrf.exempt` from `/api/web/upload` route
   - Now properly requires CSRF tokens for web uploads

3. **Blueprint Registration** (`photovault/__init__.py`):
   - Added comment clarifying path separation

## Why This Is Secure
- ✅ **Mobile API:** JWT authentication (immune to CSRF) + CSRF exempt
- ✅ **Web upload:** Session authentication (vulnerable to CSRF) + CSRF protection enabled
- ✅ **No route conflicts:** Different paths prevent routing issues
- ✅ **No security regression:** All protections maintained correctly

## Files Changed
1. `templates/upload.html` - Updated fetch URL from `/api/upload` to `/api/web/upload`
2. `photovault/routes/photo.py` - Removed `@csrf.exempt` from `/api/web/upload` route
3. `photovault/__init__.py` - Added clarifying comment about path separation

## Deployment Steps

### Step 1: Commit Changes to Git
```bash
# Check what files changed
git status

# Review changes  
git diff templates/upload.html photovault/routes/photo.py photovault/__init__.py

# Stage changes
git add templates/upload.html photovault/routes/photo.py photovault/__init__.py

# Commit with clear message
git commit -m "Fix CSRF error with proper API path separation

- Web uploads now use /api/web/upload with CSRF protection
- Mobile uploads use /api/upload with JWT authentication  
- Removed @csrf.exempt from web upload route
- Prevents route conflicts and maintains security for both clients"
```

### Step 2: Push to GitHub
```bash
# Push to your main branch
git push origin main
```

### Step 3: Railway Auto-Deploy
Railway auto-deploys from GitHub. Monitor deployment:

1. **Open Railway Dashboard:** https://railway.app
2. **Monitor Deployment:**
   - Go to "Deployments" tab
   - Wait for "Building" → "Deploying" → "Success"
3. **Check Logs:** Look for "Starting PhotoVault development server"

### Step 4: Verify Fix
After deployment:

**Test iOS Upload** ✅
```
- Open StoryKeep app
- Go to Family Vault  
- Upload from Camera Roll
- Should succeed without CSRF error
```

**Test Web Upload** ✅  
```
- Open https://storykeep.calmic.com.my
- Login → Upload page
- Select photo and upload
- Should succeed with CSRF protection
```

## Expected Results

### iOS Mobile (After Fix)
```
POST /api/upload HTTP/1.1
Authorization: Bearer <JWT>

Response: {"success": true, "photo": {...}}
```

### Web Browser (After Fix)
```
POST /api/web/upload HTTP/1.1
Cookie: session=...
X-CSRFToken: abc123...

Response: {"success": true, "files": [...]}
```

## Technical Details

### Endpoint Mapping
```python
# Mobile API (mobile_api_bp with url_prefix='/api')
@mobile_api_bp.route('/upload', methods=['POST'])  # → /api/upload
@csrf.exempt
@token_required
def upload_photo(current_user):
    # JWT authentication, CSRF exempt
    
# Web Upload (photo_bp, no url_prefix)  
@photo_bp.route('/api/web/upload', methods=['POST'])  # → /api/web/upload
@login_required  # Session auth + CSRF required
def upload_photo():
    # Session authentication, CSRF protected
```

### Security Comparison

| Aspect | Mobile Route | Web Route |
|--------|-------------|-----------|
| **Path** | `/api/upload` | `/api/web/upload` |
| **Auth Method** | JWT (Authorization header) | Session (Cookie) |
| **CSRF Protection** | Exempt (JWT immune) | Required (Cookie vulnerable) |
| **Security Level** | ✅ Secure | ✅ Secure |

## Why Previous Attempts Failed

### ❌ Attempt 1: Blueprint-Level Exemption Only
```python
csrf.exempt(mobile_api_bp)
app.register_blueprint(mobile_api_bp)
```
**Problem:** Route conflict still existed - both blueprints had `/api/upload`

### ❌ Attempt 2: Blueprint Registration Reordering
```python
app.register_blueprint(mobile_api_bp)  # First
app.register_blueprint(upload_bp)       # Second
```
**Problem:** Flask doesn't fall through - ALL `/api/upload` requests hit mobile route, breaking web uploads

### ❌ Attempt 3: Hybrid Auth with CSRF Exempt
```python
@upload_bp.route('/api/upload')
@csrf.exempt  # ❌ SECURITY VULNERABILITY!
@hybrid_auth
```
**Problem:** Removed CSRF protection from session-based uploads, enabling CSRF attacks

### ✅ Final Solution: Path Separation
```python
# Mobile: /api/upload (JWT + CSRF exempt)
# Web: /api/web/upload (Session + CSRF required)
```
**Success:** No route conflict, both auth methods properly protected

## Troubleshooting

### If CSRF error persists:
1. **Verify deployment succeeded** - Check Railway status
2. **Clear browser cache** - Hard refresh (Ctrl+Shift+R)
3. **Check frontend code** - Verify `/api/web/upload` path
4. **Inspect network tab** - Confirm X-CSRFToken header sent

### If web uploads return 400:
1. **Missing CSRF token** - Check frontend sends `X-CSRFToken` header
2. **Invalid session** - User may need to re-login
3. **Check logs** - Look for CSRF validation errors

### If mobile uploads still fail:
1. **Check JWT token** - Ensure Authorization header present
2. **Token expired** - User may need to re-login
3. **Wrong endpoint** - Mobile should use `/api/upload` NOT `/api/web/upload`

## Verification Commands

### Test Web Upload (Browser Console)
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/api/web/upload', {
  method: 'POST',
  headers: {
    'X-CSRFToken': document.querySelector('[name=csrf_token]').value
  },
  body: formData
}).then(r => r.json()).then(console.log);
```

### Test Mobile Upload (curl)
```bash
curl -X POST https://storykeep.calmic.com.my/api/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@photo.jpg"
```

## Related Documentation
- Flask Blueprints: https://flask.palletsprojects.com/en/3.0.x/blueprints/
- Flask-WTF CSRF: https://flask-wtf.readthedocs.io/en/stable/csrf.html
- JWT Best Practices: https://tools.ietf.org/html/rfc8725

## Files and Line Numbers
- `templates/upload.html:231` - Web upload endpoint
- `photovault/routes/photo.py:224-226` - Web upload route (CSRF protected)
- `photovault/routes/mobile_api.py:625-628` - Mobile upload route (CSRF exempt)
- `photovault/__init__.py:268` - mobile_api_bp registration

## Next Steps After Deployment
1. ✅ Test iOS photo uploads to vaults
2. ✅ Test web browser photo uploads (regression test)
3. ✅ Monitor Railway logs for errors
4. ✅ Update mobile app if needed

---

**Created:** October 26, 2025  
**Issue:** CSRF error on iOS vault uploads  
**Root Cause:** Route conflict - both blueprints defined `/api/upload`  
**Solution:** Path separation - mobile uses `/api/upload`, web uses `/api/web/upload`  
**Security:** No regression - proper auth and CSRF for each client type  
**Deployment:** Automatic via Railway GitHub integration
