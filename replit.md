# StoryKeep - Save Your Family Stories

## Overview
StoryKeep is a comprehensive photo management and enhancement platform offering a professional-grade experience. It includes a professional camera interface, automatic photo upload and organization, secure storage, face detection and recognition, advanced photo enhancement and restoration, AI-powered smart tagging, family vault sharing, and social media integration. The platform uses a subscription-based model and aims to provide advanced photo management solutions to a broad market.

## Recent Changes
**October 20, 2025** - Codebase Optimization & Bug Fixes:
- Removed duplicate imports and blueprint declarations in photovault/routes/photo.py
- Eliminated shadow directories (/routes, /utils, /StoryBox-iOS, /photovault/static) to prevent code drift
- Fixed critical NameError bug in upload flow where unique_id was undefined
- Corrected thumbnail naming to use `thumb_{photo.id}_{filename}` format for API endpoint compatibility
- Implemented transactional integrity in photo upload using db.session.flush() to prevent orphaned database records on upload failures
- Upload flow now maintains atomicity: all processing (thumbnail, face detection) completes before commit, ensuring rollback properly cleans up on failures

## User Preferences
None configured yet (will be added as needed)

## System Architecture

### UI/UX Decisions
The frontend uses HTML5, CSS3, JavaScript (vanilla + jQuery patterns) with Jinja2 templating, and Bootstrap patterns for responsive design. A unified photo card component system ensures consistent display with a responsive CSS Grid layout (4-column desktop, 3-column tablet, 2-column mobile). Action buttons (View, Download, Edit, Delete) and filename/timestamp overlays are standardized.

### Technical Implementations
The backend is built with Flask 3.0.3, PostgreSQL (via Neon on Replit), and SQLAlchemy 2.0.25 for ORM. Alembic via Flask-Migrate handles database migrations. Flask-Login manages authentication, and Flask-WTF + WTForms are used for forms. Gunicorn 21.2.0 serves the application in production. Image processing uses Pillow 11.3.0 with pillow-heif 1.1.1 for HEIC/HEIF support, and OpenCV 4.12.0.88 (headless), with NumPy and scikit-image. AI integration leverages Google Gemini API (gemini-2.0-flash-exp) for intelligent photo colorization and analysis. Replit Object Storage is used for persistent image storage with local storage fallback.

The Mobile Digitizer App (iOS & Android) is a professional photo digitalization tool built with React Native/Expo, featuring:
- Smart camera with real-time edge detection, visual guides, and auto-capture.
- Batch capture mode.
- Flash control.
- Client-side photo enhancement (brightness, contrast, sharpness, denoise).
- Server-side AI photo detection and extraction via `/api/detect-and-extract`.
- Offline queue using AsyncStorage for capturing without internet.
- Upload service with progress tracking and batch processing.
- JWT authentication with secure token storage and automatic logout detection (500ms polling).
- React Navigation for seamless user experience.
- Family vault photo management with multi-select deletion and permission-based access control.
- Device photo library upload via Expo ImagePicker for direct vault uploads.
- Gallery bulk share to family vaults with efficient bulk API endpoint, loading overlay, and intelligent retry logic for failed photos.
- Enhanced dashboard with 30% larger stat icons (42px), Vaults stat display with green highlight, and accurate vault counting using set-based deduplication to prevent double-counting of creators who are also members.

Voice memo recording and playback are supported using expo-av (.m4a format), with secure playback and automatic temp file cleanup.

Profile picture uploads support HEIC/HEIF formats (iOS default) with automatic conversion to JPEG for universal compatibility. The upload endpoint uses a temp file pattern with robust error handling to prevent corrupted files.

### Cross-Platform Mobile Support
The mobile app is fully cross-platform, supporting both iOS and Android with platform-specific adaptations:
- **iOS**: Face ID/Touch ID biometric authentication, iOS-specific UI patterns
- **Android**: Fingerprint/Face Unlock biometric authentication, Material Design patterns, hardware back button support
- **StatusBar**: Platform-optimized status bar configuration
- **KeyboardAvoidingView**: Platform-specific keyboard handling (iOS: padding, Android: height)
- **Permissions**: Platform-appropriate permission requests for camera, storage, and biometric access

### Feature Specifications
- **Authentication & Authorization**: User registration, login, password reset, session management, admin/superuser roles, subscription-based access.
- **Photo Management**: Upload with metadata extraction, automatic face detection and tagging, enhancement, restoration, colorization, AI smart tagging, gallery organization, search, and filtering. Includes bulk deletion.
- **Family Vaults**: Shared collections, member invitations, stories, and collaborative management.
- **Subscription System**: Multiple pricing tiers (Free, Basic, Standard, Pro, Premium) with feature-based access, Stripe payment integration, and Malaysian pricing (MYR) with SST.
- **Admin Features**: CSV/Excel export of user data, batch user operations.
- **Photo Annotations**: Text comments and voice memos for photos.

### System Design Choices
- **Database**: PostgreSQL for all environments, SQLAlchemy ORM with relationship mappings, connection pooling, SSL for production.
- **Security**: CSRF protection, password hashing, secure session cookies, file upload validation, SQL injection prevention.
- **Image Processing**: Utilizes OpenCV, Pillow, and NumPy for robust image manipulation and analysis, including EXIF metadata extraction.
- **Persistence**: Replit Object Storage for persistent image storage, organized by user.
- **Deployment**: Configured for Replit Autoscale with Gunicorn.

## External Dependencies
- **Database**: PostgreSQL (Neon on Replit)
- **AI**: Google Gemini API
- **Object Storage**: Replit Object Storage
- **Email**: SendGrid
- **Payments**: Stripe
- **Frontend Libraries**: jQuery patterns, Bootstrap patterns