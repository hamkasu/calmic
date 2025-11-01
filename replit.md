# StoryKeep - Save Your Family Stories

## Overview
StoryKeep is a subscription-based platform for photo management and enhancement. It offers a professional camera interface, automatic upload and organization, secure storage, face detection and recognition, advanced AI-powered photo enhancement and restoration, smart tagging, family vault sharing, and social media integration. The platform aims to provide comprehensive photo management solutions to a broad market, enabling users to preserve and enhance their family memories.

## Recent Changes

### Subscription Enforcement Implementation (November 1, 2025)
Implemented comprehensive subscription plan enforcement across all platforms:
- [x] Created `subscription_enforcement.py` with decorators and utilities for plan limit enforcement
- [x] Added `AIEnhancementLog` model to track AI enhancement usage for quota management
- [x] Implemented storage limit checks on photo upload endpoints (mobile API)
- [x] Implemented AI enhancement quota checks on colorization endpoints with usage logging
- [x] Implemented family vault limit checks on vault creation endpoint
- [x] All decorators return detailed JSON responses with current usage, limits, and upgrade flags
- [x] Admin/superuser bypass implemented for all enforcement checks
- [x] Architect review completed and passed

Subscription limits enforced:
- **Storage**: Free (500MB), Personal (5GB), Family (25GB), Pro (500GB)
- **AI Enhancements**: Free (5/month), Personal (25/month), Family (75/month), Pro (500/month)
- **Family Vaults**: Free (1), Personal (2), Family (5), Pro (20)

### Project Import Migration Completed (November 1, 2025)
Successfully completed the migration of the StoryKeep project to the Replit environment:
- [x] Reinstalled all Python dependencies (Flask, SQLAlchemy, Pillow, OpenCV, PyJWT, bcrypt, werkzeug)
- [x] Installed Expo SDK 54 with 752 packages for the iOS mobile app
- [x] Restarted PhotoVault Server workflow - running successfully on port 5000
- [x] Restarted Expo Server workflow - Metro bundler running with tunnel ready
- [x] Verified database initialization and subscription plans setup
- [x] Confirmed both web and mobile development environments are fully operational

Current status:
- PhotoVault Server: Fully functional on port 5000, serving web requests
- Expo Server: Metro bundler running with tunnel connected for mobile testing
- Database: PostgreSQL initialized with all tables and subscription plans
- All systems ready for development and testing

### iOS Subscription Upgrade System (October 31, 2025)
Implemented complete subscription upgrade functionality for iOS mobile app:
- [x] Auto-create Free plan subscription on registration (both web and mobile)
- [x] Mobile API endpoints: GET /api/subscription/plans, GET /api/subscription/current, POST /api/subscription/upgrade
- [x] iOS SubscriptionPlansScreen with plan cards, pricing, features, and upgrade flow
- [x] Stripe Checkout integration for payment processing (production mode)
- [x] Development mode with instant upgrades for testing
- [x] Navigation integration from Settings screen
- [x] Deployment guide for Railway production (SUBSCRIPTION_UPGRADE_DEPLOYMENT.md)

Key features:
- 4-tier pricing: Free (auto-assigned), Personal (RM12.90), Family (RM24.90), Pro (RM49.90)
- Visual plan comparison with current plan indicator
- Graceful handling of dev vs production environments
- JWT authentication on all subscription endpoints
- Edge case handling (prevent upgrade to current/Free plan, payment errors)

### Copyright Notice Addition (October 2025)
Successfully added Calmic Sdn Bhd copyright notices to entire codebase:
- [x] Core Python files (main.py, dev.py, config.py)
- [x] All Python files in photovault/routes/ (15 files)
- [x] All Python files in photovault/utils/ (19 files)
- [x] All Python files in photovault/services/ (7 files)
- [x] All Python files in photovault/models/ (1 file)
- [x] All Python files in photovault/ root (billing.py, forms.py, config.py)
- [x] All database migration files (2 files)
- [x] All HTML template files (109 files in templates/ and photovault/templates/)
- [x] All iOS JavaScript files in StoryKeep-iOS/src/ (19 files)
- [x] StoryKeep-iOS/App.js

Total files updated: 180+ files across Python backend, HTML templates, and React Native mobile app.

Copyright format used:
- Python files: Multi-line docstring with "Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved."
- HTML files: HTML comment with copyright notice
- JavaScript files: JSDoc comment block with copyright notice

### AI Photo Restoration System (November 1, 2025)
Verified and documented the active AI photo restoration features powered by Replicate API:

**Active AI Services:**
- ✅ **Replicate API** - Professional photo restoration with GFPGAN and CodeFormer models
  - Configured with `REPLICATE_API_TOKEN` environment secret
  - Service implementation: `photovault/utils/ai_restoration.py`
  - Service wrapper: `photovault/services/ai_service.py`
  
**Available AI Restoration Models:**

1. **GFPGAN** (Generative Facial Prior GAN)
   - Purpose: Face restoration and enhancement for old/damaged photos
   - Models: v1.3 (fast), v1.4 (high quality)
   - Upscaling: 1x to 4x resolution enhancement
   - Best for: Portrait photos, group photos, family photographs

2. **CodeFormer** (Face Restoration)
   - Purpose: Advanced face restoration with fidelity control
   - Fidelity range: 0.0 (more restoration) to 1.0 (preserve original)
   - Upscaling: 1x to 4x with background enhancement
   - Face upsampling for detailed facial features
   - Best for: Severely damaged portraits, balance between restoration and authenticity

**Quality Presets:**
- `fast`: Quick processing, 1x upscale, basic restoration (GFPGAN v1.3)
- `balanced`: 2x upscale, good quality (GFPGAN v1.4, CodeFormer with face upsample)
- `quality`: 2x upscale, background enhancement enabled (CodeFormer full features)
- `maximum`: 4x upscale, all enhancements enabled (highest quality, slower)

**API Endpoints:**

Web API (Session Auth):
```
POST /api/photos/<photo_id>/repair/ai
Body: {
  "model": "gfpgan" | "codeformer",
  "quality": "fast" | "balanced" | "quality" | "maximum",
  "fidelity": 0.0-1.0  // CodeFormer only, default 0.5
}
```

Mobile API (JWT Auth):
```
POST /photos/<photo_id>/repair
Body: {
  "type": "ai",
  "model": "gfpgan" | "codeformer",
  "quality": "fast" | "balanced" | "quality" | "maximum",
  "fidelity": 0.0-1.0  // CodeFormer only, default 0.5
}
```

**iOS App Integration:**
- Ready to use via `photoAPI.repairDamage(photoId, options)`
- Implemented in `StoryKeep-iOS/src/services/api.js`
- UI screens: `EnhancePhotoScreen.js`
- Supports all quality presets and model selection

**Quota Management:**
- AI restorations count against monthly AI enhancement quota
- Tracked via `AIEnhancementLog` model
- Quota limits: Free (5), Personal (25), Family (75), Pro (500) per month

**Additional AI Services (Inactive - Require Configuration):**
- ⚠️ Google Gemini API - Colorization and photo analysis (needs `GEMINI_API_KEY`)
- ⚠️ OpenAI API - AI inpainting for damage repair (needs `OPENAI_API_KEY`)

## User Preferences
None configured yet (will be added as needed)

## System Architecture

### UI/UX Decisions
The web frontend uses HTML5, CSS3, JavaScript (vanilla + jQuery patterns) with Jinja2 templating, and Bootstrap for responsive design. A unified photo card component system ensures consistent display with a responsive CSS Grid layout. The mobile app (React Native/Expo) provides a cross-platform experience with platform-specific UI adaptations (iOS Face ID/Touch ID, Android Material Design).

### Technical Implementations
The backend uses Flask 3.0.3, PostgreSQL (via Neon on Replit), and SQLAlchemy 2.0.25, with Alembic for database migrations. Flask-Login manages authentication, and Flask-WTF handles forms. Gunicorn serves the application in production. Image processing relies on Pillow 11.3.0, pillow-heif 1.1.1, and OpenCV 4.12.0.88. AI integration uses Google Gemini API for colorization and analysis, and Replicate API for professional photo restoration (GFPGAN, CodeFormer). Replit Object Storage is used for persistent image storage.

The `AdvancedPhotoDetector` implements production-grade edge detection with multi-scale pyramid processing, adaptive preprocessing, multi-strategy edge detection (Canny, Sobel), hierarchical contour analysis, watershed segmentation, special detection modes (Polaroid, faded photos), geometric validation, Non-Maximum Suppression (NMS), and a confidence scoring system. This system includes a hybrid photo detection approach for challenging scenarios like beige-on-beige backgrounds, combining edge-based and gradient+texture detection strategies for robust extraction.

The Mobile Digitizer App (React Native/Expo) features a smart camera with real-time edge detection, batch capture, client-side photo enhancement, server-side AI photo detection/extraction, an offline queue, upload service with progress tracking, JWT authentication, and family vault management. It supports voice memos and HEIC/HEIF profile picture uploads with automatic conversion.

Recent enhancements include an expanded suite of 8 artistic transformation effects (Sketch, Cartoon, Oil Painting, Watercolor, Vintage/Sepia, Pop Art, HDR Enhancement, Professional B&W) using OpenCV, processed server-side. A dedicated Enhanced Versions Gallery allows users to view and manage all enhanced versions of a photo. Client-side photo sharpening provides instant, responsive results using an upscale-downscale technique. Gallery performance is optimized with server-side pagination for faster loading and infinite scroll. HEIC image upload support with automatic conversion to JPEG has been added, alongside robust mobile registration security and semantic naming for extracted photos.

### Feature Specifications
- **Authentication & Authorization**: User registration, login, password reset, session management, admin/superuser roles, subscription-based access.
- **Photo Management**: Upload with metadata, automatic face detection/tagging, enhancement (colorization, restoration, artistic effects, sharpening), AI smart tagging, gallery organization, search, filtering, bulk actions, and ZIP backup.
- **Family Vaults**: Shared collections, member invitations, stories, and collaborative management.
- **Subscription System**: Multiple pricing tiers, Stripe integration, and Malaysian pricing (MYR) with SST.
- **AI Enhancement Quota System**: Monthly quotas for AI enhancements (colorization, restoration) with atomic consumption and monthly resets.
- **Admin Features**: CSV/Excel export, batch user operations.
- **Photo Annotations**: Text comments and voice memos.

### System Design Choices
- **Database**: PostgreSQL across all environments with SQLAlchemy ORM, connection pooling, and SSL.
- **Security**: CSRF protection, password hashing, secure session cookies, file upload validation, SQL injection prevention.
- **Quota Management**: Atomic consumption using database-level row locking (`SELECT FOR UPDATE`) and monthly cron job resets.
- **Image Processing**: OpenCV, Pillow, and NumPy for manipulation, analysis, and EXIF metadata extraction.
- **Persistence**: Replit Object Storage for user-organized image storage.
- **Deployment**: Configured for Replit Autoscale with Gunicorn.

## External Dependencies
- **Database**: PostgreSQL (Neon on Replit)
- **AI**: Google Gemini API, Replicate API
- **Object Storage**: Replit Object Storage
- **Email**: SendGrid
- **Payments**: Stripe
- **Frontend Libraries**: jQuery patterns, Bootstrap patterns