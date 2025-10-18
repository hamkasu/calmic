# System Architecture Guide

## Overview

PhotoVault/StoryKeep is built using a modern three-tier architecture with clear separation between presentation, business logic, and data layers. The system supports both web and mobile clients through a unified backend API.

## Design Philosophy: Platform-Specific Feature Distribution

### Mobile-First Legacy Photo Restoration (StoryKeep)

The mobile app is laser-focused on **digitizing and restoring old physical photos**:

**Use Case**: Elderly users digitizing family photo albums
- Physical photos need to be captured with a camera
- Quick fixes needed: sharpen blurry photos, colorize B&W photos
- Simple, focused interface (3 buttons: Sharpen, Colorize DNN, Colorize AI)
- Offline support for capturing photos without internet

**Mobile-Only Features**:
- Smart camera with edge detection
- Photo detection and extraction
- Sharpen (fix degraded photos)
- Colorize DNN (fast colorization)
- Colorize AI (intelligent colorization)
- Offline upload queue

### Web-Based Advanced Editing (PhotoVault)

The web platform provides the **full photo editing suite**:

**Use Case**: Detailed editing at home on a larger screen
- All mobile features + advanced tools
- Complex adjustments (brightness, contrast, filters, effects)
- Face detection and person tagging
- Batch processing
- Social media integration
- Subscription management

**Why This Split?**
- **Mobile = Capture & Quick Fix**: Users are physically holding old photos, need immediate digitization
- **Web = Edit & Enhance**: Users have time for detailed editing on a desktop
- **Better UX**: Focused mobile interface vs. comprehensive web tools
- **Performance**: Heavy processing (face detection, batch operations) better on web

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                         │
│  ┌─────────────────┐         ┌─────────────────┐       │
│  │   Web Browser   │         │  StoryKeep iOS  │       │
│  │   (HTML/CSS/JS) │         │  (React Native) │       │
│  └─────────────────┘         └─────────────────┘       │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                 Application Layer                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Flask Application (Python)              │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │  │
│  │  │  Routes  │  │ Services │  │  Utilities   │   │  │
│  │  │          │  │          │  │              │   │  │
│  │  │ • Auth   │  │ • AI     │  │ • JWT Auth   │   │  │
│  │  │ • Photo  │  │ • Email  │  │ • File       │   │  │
│  │  │ • Gallery│  │ • Storage│  │   Handler    │   │  │
│  │  │ • API    │  │ • Social │  │ • Security   │   │  │
│  │  └──────────┘  └──────────┘  └──────────────┘   │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                    Data Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  PostgreSQL  │  │    Replit    │  │   External   │  │
│  │   Database   │  │    Object    │  │   Services   │  │
│  │              │  │   Storage    │  │              │  │
│  │ • Users      │  │ • Photos     │  │ • Google AI  │  │
│  │ • Photos     │  │ • Thumbnails │  │ • SendGrid   │  │
│  │ • Vaults     │  │ • Audio      │  │ • Stripe     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Web Application (Flask)

#### Blueprint Structure
The application is organized into modular blueprints for better maintainability:

- **auth_bp** (`/auth/*`) - User authentication and registration
- **main_bp** (`/`) - Main web pages and dashboard
- **gallery_bp** (`/gallery/*`) - Photo gallery and management
- **photo_bp** (`/photo/*`, `/upload`) - Photo upload and processing
- **camera_bp** (`/camera/*`) - Camera capture functionality
- **mobile_api_bp** (`/api/*`) - Mobile app API endpoints
- **admin_bp** (`/admin/*`) - Administrative functions
- **billing_bp** (`/billing/*`) - Subscription and payments
- **vault_bp** (`/vault/*`) - Family vault management

#### Service Layer
Business logic is separated into service modules:

```python
services/
├── ai_service.py           # Google Gemini integration
├── app_storage_service.py  # Object storage management
├── sendgrid_service.py     # Email notifications
└── social_media_service.py # Social media integration
```

#### Utility Layer
Common functionality abstracted into utilities:

```python
utils/
├── jwt_auth.py            # JWT authentication decorators
├── enhanced_file_handler.py # File upload/download management
├── file_handler.py        # Basic file operations
├── metadata_extractor.py  # EXIF data extraction
├── face_detection.py      # Face detection algorithms
├── face_recognition.py    # Face recognition
├── photo_detection.py     # Photo extraction from images
└── security.py           # Security utilities
```

### 2. Mobile Application (React Native/Expo)

#### Screen Architecture
```
screens/
├── AuthScreens/
│   ├── LoginScreen.js     # Authentication
│   └── RegisterScreen.js
├── CameraScreen.js        # Photo capture
├── GalleryScreen.js       # Photo gallery
├── PhotoDetailScreen.js   # Photo viewer/editor
├── DashboardScreen.js     # User dashboard
├── FamilyVaultScreen.js   # Family vault management
├── VaultDetailScreen.js   # Vault details
├── ProfileScreen.js       # User profile
└── SettingsScreen.js      # App settings
```

#### Service Layer
```javascript
services/
├── api.js                 # API client with Axios
├── authService.js         # Authentication logic
├── uploadQueue.js         # Offline upload queue
└── storageService.js      # Local storage management
```

## Data Flow Patterns

### 1. Photo Upload Flow (Web)

```
User Upload → Flask Route → Validation → Storage Service → Database
                ↓              ↓            ↓                ↓
          File Upload     Size/Type    Object Storage    Photo Record
                          Check        or Local FS       with Metadata
```

### 2. Photo Upload Flow (Mobile)

```
Camera Capture → Local Storage → Upload Queue → API Request → Backend Processing
      ↓              ↓               ↓             ↓              ↓
   Base64         AsyncStorage    Background     JWT Auth     Same as Web
   Encode                          Worker         Check
```

### 3. Authentication Flow

#### Web (Session-based)
```
Login Request → Validate Credentials → Create Session → Set Cookie → Redirect
                      ↓                      ↓              ↓
                User Query            Flask-Login      Session ID
```

#### Mobile (JWT-based)
```
Login Request → Validate Credentials → Generate JWT → Return Token → Store Securely
                      ↓                      ↓            ↓              ↓
                User Query            30-day expiry  JSON Response   SecureStore
```

### 4. Image Processing Pipeline

```
Original Image → Enhancement Request → Processing → Save Edited → Update DB
      ↓                 ↓                  ↓            ↓            ↓
   Validation      Settings JSON      OpenCV/PIL   New Filename   Photo Record
                                      Operations    with metadata   Updated
```

## Database Design Patterns

### 1. User-Owned Resources
All user-generated content is linked to the User model:

```python
Photo.user_id → User.id
Album.user_id → User.id
VoiceMemo.user_id → User.id
```

### 2. Association Tables
Many-to-many relationships use association tables:

```python
PhotoPerson: Photo ↔ Person (face tagging)
VaultPhoto: Photo ↔ FamilyVault (sharing)
StoryPhoto: Photo ↔ Story (narratives)
```

### 3. Soft Deletes
Critical data uses status fields instead of hard deletes:

```python
UserSubscription.status: 'active', 'cancelled', 'expired'
FamilyMember.status: 'active', 'pending', 'removed'
```

## Security Architecture

### 1. Authentication Layers

```
Web Requests:
  Browser → Flask Session → @login_required → Route Handler

Mobile Requests:
  iOS App → JWT Token → @token_required → Route Handler

File Serving:
  Request → @hybrid_auth → Validate User → Serve File
```

### 2. Input Validation Pipeline

```
User Input → Sanitization → Type Validation → Business Logic Validation → Storage
              ↓                 ↓                    ↓
         HTML Escape      Format Check        Database Constraints
         Path Traversal   Size Limits         Unique Constraints
         Prevention       Allowed Types
```

### 3. File Upload Security

```
File Upload → Extension Check → MIME Type Validation → Content Verification → Safe Storage
                ↓                     ↓                      ↓                    ↓
          Whitelist Only       Check Headers        PIL.Image.verify()    Secure Filename
                                                                           Isolated Directory
```

## API Design Patterns

### 1. RESTful Endpoints
```
GET    /api/photos          # List photos
POST   /api/photos          # Create photo
GET    /api/photos/{id}     # Get photo details
PUT    /api/photos/{id}     # Update photo
DELETE /api/photos/{id}     # Delete photo
```

### 2. Response Format
All API responses follow a consistent structure:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "page": 1,
    "total": 100
  }
}
```

### 3. Error Handling
Standardized error responses:

```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": { ... }
}
```

## Storage Architecture

### 1. File Organization

```
uploads/
├── {user_id}/
│   ├── photos/
│   │   ├── original/
│   │   ├── edited/
│   │   └── thumbnails/
│   └── audio/
│       └── voice_memos/
```

### 2. Object Storage (Replit)

```
users/
├── {user_id}/
│   ├── {filename}              # Original photo
│   ├── {filename}_thumb.jpg    # Thumbnail
│   └── {filename}_edited.jpg   # Edited version
```

### 3. Hybrid Storage Strategy

```python
if replit_storage.is_available():
    # Use object storage (production)
    path = upload_to_object_storage(file)
else:
    # Fallback to local filesystem (development)
    path = save_to_local_filesystem(file)
```

## Scalability Considerations

### 1. Database Optimization
- Indexed foreign keys for fast joins
- Pagination for large result sets (20 items per page)
- Lazy loading for relationships
- Connection pooling via SQLAlchemy

### 2. Caching Strategy
- Static assets cached via browser headers
- Database query results cached in session
- Thumbnail generation cached on disk

### 3. Async Processing
- Background job queue for image processing
- Batch operations for bulk updates
- Deferred thumbnail generation

## Deployment Architecture

### Development
```
Local Machine → Flask Dev Server → SQLite/PostgreSQL → Local Storage
                 (port 5000)
```

### Production (Railway)
```
GitHub Push → Railway Deploy → Gunicorn Workers → PostgreSQL → Object Storage
                                  ↓                  ↓            ↓
                            Auto-scaling         Neon DB    Replit Storage
                            Load Balancer        (managed)   (managed)
```

## Integration Points

### 1. Google Gemini AI
- Endpoint: `https://generativelanguage.googleapis.com/`
- Purpose: Image analysis, colorization guidance
- Authentication: API key via headers

### 2. SendGrid Email
- Endpoint: `https://api.sendgrid.com/v3/`
- Purpose: Password resets, vault invitations
- Authentication: API key via headers

### 3. Stripe Payments
- Endpoint: `https://api.stripe.com/v1/`
- Purpose: Subscription billing (Malaysian market)
- Authentication: Secret key via headers

### 4. Replit Object Storage
- SDK: `replit-object-storage`
- Purpose: Production file storage
- Authentication: Environment credentials

## Performance Optimization

### 1. Image Processing
- Lazy thumbnail generation
- Progressive image loading
- Format conversion (WebP support)
- Dimension capping (4096px max)

### 2. API Optimization
- Response compression (gzip)
- Minimal payload sizes
- Selective field loading
- Batch endpoint support

### 3. Frontend Optimization
- Asset minification
- Lazy component loading
- Image lazy loading
- Service worker caching (mobile)

## Monitoring and Logging

### 1. Application Logging
```python
logger.info("User action")
logger.warning("Unusual behavior")
logger.error("Error occurred", exc_info=True)
```

### 2. Error Tracking
- Database errors logged with traceback
- API errors returned with error codes
- File operation failures logged

### 3. Metrics (Production)
- Request latency
- Error rates
- Storage usage
- Active user count

## Future Architecture Considerations

### 1. Microservices Migration
- Separate image processing service
- Dedicated AI service
- Independent storage service

### 2. Message Queue
- RabbitMQ/Redis for async jobs
- Background task processing
- Email queue management

### 3. CDN Integration
- CloudFlare for static assets
- Thumbnail delivery optimization
- Global content distribution

### 4. Database Sharding
- User-based sharding strategy
- Read replicas for scaling
- Time-based partitioning for photos
