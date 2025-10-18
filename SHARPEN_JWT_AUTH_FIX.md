# Fix: iOS Sharpen "Authorization token is missing" Error

## Problem
iOS app shows error: **"Authorization token is missing"** when sharpening images on Railway production.

## Root Cause
The `/api/photos/<id>/sharpen` endpoint in `photo.py` was using `@login_required` (session-based auth) instead of `@hybrid_auth`, which prevented JWT tokens from working.

## What Was Fixed
Changed the sharpen endpoint in `photovault/routes/photo.py` (line 1586-1589) from:
```python
@photo_bp.route('/api/photos/<int:photo_id>/sharpen', methods=['POST'])
@csrf.exempt
@login_required                    # ❌ Only accepts session cookies
def sharpen_photo_api(photo_id):
```

To:
```python
@photo_bp.route('/api/photos/<int:photo_id>/sharpen', methods=['POST'])
@csrf.exempt
@hybrid_auth                       # ✅ Accepts both session cookies AND JWT tokens
def sharpen_photo_api(current_user, photo_id):
```

## How to Deploy to Railway

### Step 1: Commit and Push to GitHub
```bash
git add photovault/routes/photo.py
git commit -m "Fix: Enable JWT authentication for sharpen endpoint"
git push origin main
```

### Step 2: Verify on Railway
1. Wait for Railway to automatically deploy (~2-3 minutes)
2. Check deployment logs on Railway dashboard
3. Test sharpen feature in iOS app

## Testing
After deployment:
1. Open StoryKeep iOS app
2. Navigate to any photo detail screen
3. Tap "Sharpen" button
4. Adjust sharpening strength
5. Tap "Apply"
6. ✅ Should succeed without "Authorization token is missing" error

## Technical Details
- **@hybrid_auth** supports both:
  - Session cookies (web users)
  - JWT Bearer tokens (mobile users)
- Mobile app sends: `Authorization: Bearer <jwt_token>`
- Hybrid auth checks both authentication methods
