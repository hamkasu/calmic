# Camera Upload Fix - October 15, 2025

## Problem
Camera was not saving photos on both web and iOS apps.

## Root Cause
**Field Name Mismatch between JavaScript and Backend:**

### Web Camera Issues:
1. **Single Photo Upload** (templates/camera.html line 1281):
   - ❌ JavaScript sent: `formData.append('file', blob, filename)`
   - ✅ Backend expected: `'image'` field at `/camera/upload`
   - ❌ Wrong endpoint: Used `/api/upload` instead of `/camera/upload`

2. **Quad Photo Upload** (templates/camera.html line 1532):
   - ❌ JavaScript sent: `formData.append('file', blob, filename)`
   - ✅ Backend expected: `'image'` field at `/camera/upload`

3. **Photo Model Initialization** (photovault/routes/camera_routes.py line 88):
   - ❌ Used constructor: `Photo(filename=..., user_id=...)`
   - ✅ Fixed to property assignment: `photo.filename = ...`

## Fixes Applied

### 1. Web Camera JavaScript (templates/camera.html)
```javascript
// BEFORE (Line 1281):
formData.append('file', blob, filename);
const uploadResponse = await fetch('/api/upload', {

// AFTER (Fixed):
formData.append('image', blob, filename);  // Changed 'file' to 'image'
const uploadResponse = await fetch('/camera/upload', {  // Changed endpoint
```

```javascript
// BEFORE (Line 1532):
formData.append('file', blob, filename);

// AFTER (Fixed):
formData.append('image', blob, filename);  // Changed 'file' to 'image'
```

### 2. Photo Model Initialization (photovault/routes/camera_routes.py)
```python
# BEFORE (Line 85-95):
photo = Photo(
    filename=filename,
    user_id=current_user.id,
    file_path=file_path,
    ...
)

# AFTER (Fixed):
photo = Photo()
photo.filename = filename
photo.user_id = current_user.id
photo.file_path = file_path
...
```

## Endpoint Summary

### Web Camera Endpoints:
- **Endpoint:** `/camera/upload` (POST)
- **Field Name:** `'image'`
- **Blueprint:** `camera_bp` with prefix `/camera`

### iOS Mobile API:
- **Endpoint:** `/api/upload` (POST)
- **Field Name:** `'photo'`
- **Authentication:** JWT token required

## Testing
✅ Server restarted successfully
✅ Camera upload endpoint available at `/camera/upload`
✅ Photo model initialization fixed

## Next Steps
1. Test web camera on local Replit (http://127.0.0.1:5000/camera)
2. Deploy fixes to Railway for iOS app
3. Test iOS camera upload with mobile API
