# API Documentation

## Base URLs

- **Development**: `http://localhost:5000/api`
- **Production**: `https://web-production-535bd.up.railway.app/api`

## Authentication

### Session-Based (Web)
Web requests use Flask session cookies managed by Flask-Login.

### JWT-Based (Mobile)
Mobile requests require a Bearer token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

JWT tokens are obtained through login and are valid for 30 days.

## Authentication Endpoints

### POST /api/auth/login
Mobile app login endpoint.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "user@example.com"
  }
}
```

**Errors:**
- `400 Bad Request` - Missing credentials
- `401 Unauthorized` - Invalid credentials

---

### POST /api/auth/register
Mobile app registration endpoint.

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "User registered successfully",
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "user@example.com"
  }
}
```

**Errors:**
- `400 Bad Request` - Validation errors
- `409 Conflict` - Username/email already exists

---

## Photo Endpoints

### GET /api/photos
Get paginated list of user's photos.

**Authentication:** JWT required

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20, max: 100)
- `filter` (optional): Filter type - `all`, `dnn_colorized`, `ai_colorized`, `not_colorized`

**Response (200 OK):**
```json
{
  "success": true,
  "photos": [
    {
      "id": 1,
      "original_url": "/uploads/1/photo.jpg",
      "edited_url": "/uploads/1/photo_edited.jpg",
      "thumbnail_url": "/uploads/1/photo_thumb.jpg",
      "created_at": "2025-10-12T10:30:00Z",
      "width": 1920,
      "height": 1080,
      "file_size": 2048576,
      "colorization_method": "dnn"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5
  }
}
```

---

### POST /api/upload
Upload a photo (supports multipart/form-data).

**Authentication:** JWT required

**Request (multipart/form-data):**
```
file: <image file>
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Photo uploaded successfully",
  "photo": {
    "id": 1,
    "filename": "johndoe.20251012.123456.jpg",
    "url": "/uploads/1/johndoe.20251012.123456.jpg",
    "thumbnail_url": "/uploads/1/johndoe.20251012.123456_thumb.jpg"
  }
}
```

**Errors:**
- `400 Bad Request` - No file provided
- `413 Payload Too Large` - File exceeds 50MB
- `415 Unsupported Media Type` - Invalid file type

---

### POST /api/detect-and-extract
Detect and extract photos from a larger image.

**Authentication:** JWT required

**Request (multipart/form-data):**
```
file: <image file>
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Detected and extracted 3 photos",
  "photos": [
    {
      "id": 1,
      "filename": "extracted_1.jpg",
      "url": "/uploads/1/extracted_1.jpg"
    }
  ]
}
```

---

### POST /api/photos/{photo_id}/enhance
Apply auto-enhancement to a photo.

**Authentication:** JWT required

**Request Body:**
```json
{
  "brightness": 1.1,
  "contrast": 1.2,
  "sharpness": 1.3
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Photo enhanced successfully",
  "edited_url": "/uploads/1/photo_enhanced.jpg"
}
```

---

### POST /api/photos/{photo_id}/colorize
Apply DNN-based colorization.

**Authentication:** JWT required

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Photo colorized successfully",
  "edited_url": "/uploads/1/photo_colorized.jpg",
  "method": "dnn"
}
```

---

### POST /api/photos/{photo_id}/colorize-ai
Apply AI-guided colorization using Google Gemini.

**Authentication:** JWT required

**Response (200 OK):**
```json
{
  "success": true,
  "message": "AI colorization completed",
  "edited_url": "/uploads/1/photo_ai_colorized.jpg",
  "method": "ai",
  "analysis": "Vintage family photo from the 1960s..."
}
```

---

### POST /api/photos/{photo_id}/sharpen
Apply sharpening to a photo.

**Authentication:** JWT required

**Request Body:**
```json
{
  "intensity": 1.5
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Photo sharpened successfully",
  "edited_url": "/uploads/1/photo_sharpened.jpg"
}
```

---

### DELETE /api/photos/{photo_id}
Delete a photo.

**Authentication:** JWT required

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Photo deleted successfully"
}
```

---

## Dashboard Endpoints

### GET /api/dashboard
Get user dashboard statistics and photos.

**Authentication:** JWT required

**Response (200 OK):**
```json
{
  "total_photos": 46,
  "enhanced_photos": 12,
  "storage_used": 245.5,
  "subscription_plan": "Basic",
  "recent_photo": {
    "id": 1,
    "original_url": "/uploads/1/photo.jpg",
    "thumbnail_url": "/uploads/1/photo_thumb.jpg"
  },
  "all_photos": [
    {
      "id": 1,
      "original_url": "/uploads/1/photo.jpg",
      "edited_url": "/uploads/1/photo_edited.jpg"
    }
  ]
}
```

---

### GET /api/auth/profile
Get current user profile information.

**Authentication:** JWT required

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "user@example.com",
  "is_admin": false,
  "subscription": {
    "plan": "Basic",
    "status": "active",
    "expires_at": "2025-11-12T00:00:00Z"
  }
}
```

---

## Family Vault Endpoints

### GET /api/family/vaults
List user's family vaults.

**Authentication:** JWT required

**Response (200 OK):**
```json
{
  "success": true,
  "vaults": [
    {
      "id": 1,
      "name": "Family Memories",
      "description": "Our family photo collection",
      "vault_code": "ABC123",
      "is_public": false,
      "creator_id": 1,
      "photo_count": 50,
      "member_count": 4,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

---

### GET /api/family/vault/{vault_id}
Get vault details with photos and members.

**Authentication:** JWT required

**Response (200 OK):**
```json
{
  "success": true,
  "vault": {
    "id": 1,
    "name": "Family Memories",
    "description": "Our family photo collection",
    "photos": [
      {
        "id": 1,
        "url": "/uploads/1/photo.jpg",
        "caption": "Summer vacation 2024",
        "uploaded_by": "johndoe"
      }
    ],
    "members": [
      {
        "user_id": 1,
        "username": "johndoe",
        "role": "owner",
        "status": "active"
      }
    ]
  }
}
```

---

### POST /api/family/vaults
Create a new family vault.

**Authentication:** JWT required

**Request Body:**
```json
{
  "name": "Holiday Photos",
  "description": "Photos from our holiday trip",
  "is_public": false
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Vault created successfully",
  "vault": {
    "id": 2,
    "name": "Holiday Photos",
    "vault_code": "XYZ789"
  }
}
```

---

### POST /api/family/vault/{vault_id}/add-photo
Add a photo to a vault.

**Authentication:** JWT required

**Request Body:**
```json
{
  "photo_id": 5,
  "caption": "Beach sunset"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Photo added to vault successfully"
}
```

---

### POST /api/family/vault/{vault_id}/invite
Invite a member to a vault.

**Authentication:** JWT required

**Request Body:**
```json
{
  "email": "friend@example.com",
  "role": "member"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Invitation sent successfully"
}
```

---

## Voice Memo Endpoints

### POST /api/photos/{photo_id}/voice-memos
Upload a voice memo for a photo.

**Authentication:** JWT required

**Request (multipart/form-data):**
```
audio: <audio file>
title: "My voice note"
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Voice memo uploaded successfully",
  "memo": {
    "id": 1,
    "title": "My voice note",
    "duration": 45.5,
    "url": "/api/voice-memos/1/audio"
  }
}
```

---

### GET /api/photos/{photo_id}/voice-memos
List voice memos for a photo.

**Authentication:** JWT required

**Response (200 OK):**
```json
{
  "success": true,
  "memos": [
    {
      "id": 1,
      "title": "My voice note",
      "duration": 45.5,
      "created_at": "2025-10-12T10:30:00Z",
      "url": "/api/voice-memos/1/audio"
    }
  ]
}
```

---

### GET /api/voice-memos/{memo_id}/audio
Stream voice memo audio file.

**Authentication:** JWT or Session required

**Response:** Audio file stream (audio/mpeg, audio/wav, etc.)

---

### DELETE /api/voice-memos/{memo_id}
Delete a voice memo.

**Authentication:** JWT required

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Voice memo deleted successfully"
}
```

---

## Error Response Format

All errors follow this format:

```json
{
  "success": false,
  "error": "Error message describing what went wrong",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

- `400 BAD_REQUEST` - Invalid request data
- `401 UNAUTHORIZED` - Missing or invalid authentication
- `403 FORBIDDEN` - Insufficient permissions
- `404 NOT_FOUND` - Resource not found
- `409 CONFLICT` - Resource conflict (e.g., duplicate)
- `413 PAYLOAD_TOO_LARGE` - File too large
- `415 UNSUPPORTED_MEDIA_TYPE` - Invalid file type
- `500 INTERNAL_SERVER_ERROR` - Server error

## Rate Limiting

- Upload endpoints: 10 requests per minute
- API endpoints: 100 requests per minute
- Authentication endpoints: 5 requests per minute

## File Upload Limits

- **Maximum file size**: 50MB (mobile), 16MB (web)
- **Allowed formats**: PNG, JPG, JPEG, GIF, BMP, WEBP
- **Maximum dimensions**: 4096 x 4096 pixels
- **Thumbnail size**: 300 x 300 pixels

## Pagination

List endpoints support pagination with these query parameters:

- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

Response includes pagination metadata:

```json
{
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5
  }
}
```

## Image URL Format

All image URLs are relative to the base URL:

```
/uploads/{user_id}/{filename}
```

To access images from mobile app, prepend the base URL and include JWT token in Authorization header:

```
GET https://web-production-535bd.up.railway.app/uploads/1/photo.jpg
Authorization: Bearer <jwt_token>
```
