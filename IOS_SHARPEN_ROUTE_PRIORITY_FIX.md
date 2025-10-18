# iOS Sharpen Route Priority Fix - Railway Deployment Guide

## 🐛 Problem
The iOS app's sharpen feature was failing on Railway production with:
- **Error**: "The CSRF token is missing"  
- **Status Code**: 400 Bad Request
- **Logs**: `INFO:flask_wtf.csrf:The CSRF token is missing.`

## 🔍 Root Cause Analysis

### Duplicate Route Issue
Both `photo_bp` and `mobile_api_bp` blueprints defined the same route path:

**photo_bp** (session authentication):
```python
@photo_bp.route('/api/photos/<int:photo_id>/sharpen', methods=['POST'])
@login_required  # Requires Flask-Login session + CSRF token
def sharpen_photo_api(photo_id):
```

**mobile_api_bp** (JWT authentication):
```python
mobile_api_bp = Blueprint('mobile_api', __name__, url_prefix='/api')

@mobile_api_bp.route('/photos/<int:photo_id>/sharpen', methods=['POST'])
@csrf.exempt  # CSRF exempt for mobile
@token_required  # Requires JWT Bearer token
def sharpen_photo_mobile(photo_id):
```

Both resolve to: `/api/photos/<int:photo_id>/sharpen`

### Blueprint Registration Order Problem
In `photovault/__init__.py`, blueprints were registered in this order:
1. **photo_bp** (line 269) ← Registered first, matches first!
2. **mobile_api_bp** (line 276) ← Never reached

Flask's routing matches the **first registered route**, so all requests to `/api/photos/<id>/sharpen` hit the session-authenticated `photo_bp` endpoint, which requires CSRF tokens that mobile apps don't have.

## ✅ Secure Solution

### Fixed Blueprint Registration Order
Moved `mobile_api_bp` registration **before** `photo_bp` in `photovault/__init__.py`:

```python
# Register mobile_api_bp BEFORE photo_bp to ensure JWT-authenticated routes match first
app.register_blueprint(mobile_api_bp)  # ← Now matches first for /api/photos/<id>/sharpen
app.register_blueprint(photo_bp)       # ← Falls back for web requests
```

**File Changed**: `photovault/__init__.py` (lines 272-274)

## 🔒 Security Benefits

### Why This Solution is Secure
1. **No CSRF Protection Removed**: Both endpoints maintain their security:
   - `mobile_api_bp`: JWT authentication with `@csrf.exempt` (correct for mobile)
   - `photo_bp`: Session authentication with CSRF protection (correct for web)

2. **Proper Route Precedence**: Mobile requests hit the JWT endpoint first
   - Mobile app with `Authorization: Bearer <token>` → `mobile_api_bp` (✓ Authenticated via JWT)
   - Web browser with session cookies → `photo_bp` (✓ Authenticated via session + CSRF)

3. **Defense in Depth**: Each endpoint validates authentication appropriate for its client type

## 📦 Deploy to Railway

### Step 1: Push Changes to GitHub
```bash
# Stage the fix
git add photovault/__init__.py

# Commit with descriptive message
git commit -m "Fix: Reorder blueprints to prioritize mobile JWT routes over session routes"

# Push to main branch (Railway auto-deploys from main)
git push origin main
```

### Step 2: Verify Railway Deployment
1. Go to your Railway dashboard: https://railway.app/
2. Select your PhotoVault project
3. Click on the **"Deployments"** tab
4. Wait for the new deployment to show "✓ Success" (usually 2-3 minutes)

### Step 3: Test iOS App
1. Open StoryKeep app on your iPhone
2. Navigate to a photo
3. Tap **"Enhance Photo"** → **"Sharpen"**
4. Adjust intensity slider
5. Tap **"Sharpen"**
6. ✅ Should see "Photo sharpened successfully!" without CSRF errors

## 📊 Expected Behavior After Fix

### Railway Logs (Before Fix)
```
INFO:flask_wtf.csrf:The CSRF token is missing.
AxiosError: Request failed with status code 400
```

### Railway Logs (After Fix)
```
INFO:photovault.routes.mobile_api: Sharpen photo 244 for user hamka
INFO:photovault.routes.mobile_api: Photo sharpened successfully
```

### Route Matching Order
1. Request: `POST /api/photos/123/sharpen` with `Authorization: Bearer <JWT>`
2. Flask checks blueprints in registration order:
   - ✓ **mobile_api_bp** matches → Uses JWT auth, no CSRF required
   - Photo successfully sharpened

## 🚨 What NOT to Do

### ❌ DANGEROUS: Adding @csrf.exempt to Session-Authenticated Routes
```python
# DON'T DO THIS - Creates CSRF vulnerability!
@photo_bp.route('/api/photos/<int:photo_id>/sharpen', methods=['POST'])
@csrf.exempt  # ← UNSAFE: Removes CSRF protection from session auth
@login_required
def sharpen_photo_api(photo_id):
```

This creates a **high-risk CSRF vulnerability** where malicious sites can forge requests for logged-in users.

### ✅ CORRECT: Use Blueprint Registration Order
```python
# Register JWT-authenticated blueprints first
app.register_blueprint(mobile_api_bp)  # JWT auth, CSRF exempt
app.register_blueprint(photo_bp)        # Session auth, CSRF protected
```

## 📝 Related Files
- **Fixed File**: `photovault/__init__.py` (blueprint registration order)
- **Mobile Endpoint**: `photovault/routes/mobile_api.py` (JWT auth with @csrf.exempt)  
- **Web Endpoint**: `photovault/routes/photo.py` (session auth with CSRF protection)
- **iOS App Code**: `StoryKeep-iOS/src/services/api.js` (calls `/api/photos/${photoId}/sharpen`)

## 🎯 Key Takeaway
When multiple blueprints define the same route, Flask matches them in **registration order**. Always register API endpoints that handle mobile authentication (JWT) before web endpoints that use session authentication to ensure proper routing precedence.
