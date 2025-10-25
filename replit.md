# StoryKeep - Save Your Family Stories

## Overview
StoryKeep is a comprehensive, subscription-based photo management and enhancement platform. It offers a professional camera interface, automatic photo upload and organization, secure storage, face detection and recognition, advanced AI-powered photo enhancement and restoration, smart tagging, family vault sharing, and social media integration. The platform aims to provide advanced photo management solutions to a broad market.

## User Preferences
None configured yet (will be added as needed)

## System Architecture

### UI/UX Decisions
The frontend uses HTML5, CSS3, JavaScript (vanilla + jQuery patterns) with Jinja2 templating, and Bootstrap patterns for responsive design. A unified photo card component system ensures consistent display with a responsive CSS Grid layout. Action buttons, filename/timestamp overlays, and display elements are standardized. The mobile app utilizes React Native/Expo for a cross-platform experience, with platform-specific UI adaptations for iOS (Face ID/Touch ID, iOS UI patterns) and Android (Fingerprint/Face Unlock, Material Design).

### Technical Implementations
The backend is built with Flask 3.0.3, PostgreSQL (via Neon on Replit), and SQLAlchemy 2.0.25. Alembic via Flask-Migrate handles database migrations. Flask-Login manages authentication, and Flask-WTF + WTForms are used for forms. Gunicorn 21.2.0 serves the application in production. Image processing uses Pillow 11.3.0, pillow-heif 1.1.1, and OpenCV 4.12.0.88 (headless), with NumPy and scikit-image. AI integration leverages Google Gemini API for intelligent photo colorization and analysis, and Replicate API for professional-grade AI photo restoration (GFPGAN, CodeFormer). Replit Object Storage is used for persistent image storage with local storage fallback.

The `AdvancedPhotoDetector` implements production-grade edge detection with multi-scale pyramid processing, adaptive preprocessing (shadow removal, glare mitigation, illumination normalization), multi-strategy edge detection (Canny, Sobel), hierarchical contour analysis, watershed segmentation, special detection modes (Polaroid, faded photos), geometric validation, Non-Maximum Suppression (NMS), and a confidence scoring system.

The Mobile Digitizer App (React Native/Expo) features a smart camera with real-time edge detection, batch capture, client-side photo enhancement, server-side AI photo detection and extraction, an offline queue, upload service with progress tracking, JWT authentication, React Navigation, family vault management with multi-select deletion and permission-based access, and device photo library uploads. It supports voice memo recording and playback using expo-av. Profile picture uploads support HEIC/HEIF with automatic conversion to JPEG.

**Recent Enhancements (Oct 2025):**
- **Progress Indicators**: Added reusable ProgressBar component with animated progress tracking for all time-consuming operations including photo enhancement (sharpen, colorize DNN, colorize AI, AI restoration), photo upload/detection, and batch processing. Progress bars show percentage completion and user-friendly status messages.
- **Gallery Optimization**: Implemented pagination (30 photos per page) with lazy loading, optimized FlatList rendering with `initialNumToRender`, `windowSize`, and `removeClippedSubviews` for better performance. Added initial loading screen with progress indicator.
- **Photo Detection Sensitivity**: Optimized detection parameters to better detect smaller photos while maintaining quality (min_confidence=0.60, min_photo_area=80k pixels, min_dimension=250 pixels). The detector now successfully captures photos as small as 250x320 pixels, making it ideal for detecting multiple photos in a single camera frame.

### Feature Specifications
- **Authentication & Authorization**: User registration, login, password reset, session management, admin/superuser roles, subscription-based access.
- **Photo Management**: Upload with metadata extraction, automatic face detection and tagging, enhancement, restoration, colorization, AI smart tagging, gallery organization, search, filtering, bulk deletion, and "Download All" as ZIP backup.
- **Family Vaults**: Shared collections, member invitations, stories, and collaborative management.
- **Subscription System**: Multiple pricing tiers with feature-based access, Stripe payment integration, and Malaysian pricing (MYR) with SST.
- **AI Enhancement Quota System**: Monthly quotas for AI enhancements (colorization, restoration) to prevent excessive API costs. Atomic quota enforcement with SELECT FOR UPDATE locking prevents concurrent request bypass. Quotas: Free (5), Personal (25), Family (75), Pro (250), Business (1000). Auto-resets on 1st of each month via cron job.
- **Admin Features**: CSV/Excel export of user data, batch user operations.
- **Photo Annotations**: Text comments and voice memos for photos.

### System Design Choices
- **Database**: PostgreSQL for all environments, SQLAlchemy ORM, connection pooling, SSL for production.
- **Security**: CSRF protection, password hashing, secure session cookies, file upload validation, SQL injection prevention.
- **Quota Management**: Atomic quota consumption using database-level row locking (SELECT FOR UPDATE) to prevent race conditions. Monthly reset via cron job handles both active subscriptions and legacy NULL reset dates.
- **Image Processing**: Utilizes OpenCV, Pillow, and NumPy for robust image manipulation and analysis, including EXIF metadata extraction.
- **Persistence**: Replit Object Storage for persistent image storage, organized by user.
- **Deployment**: Configured for Replit Autoscale with Gunicorn.

## External Dependencies
- **Database**: PostgreSQL (Neon on Replit)
- **AI**: Google Gemini API, Replicate API
- **Object Storage**: Replit Object Storage
- **Email**: SendGrid
- **Payments**: Stripe
- **Frontend Libraries**: jQuery patterns, Bootstrap patterns