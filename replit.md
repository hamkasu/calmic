# StoryKeep - Save Your Family Stories

## Overview
StoryKeep is a comprehensive photo management and enhancement platform offering a professional-grade experience. It includes a professional camera interface, automatic photo upload and organization, secure storage, face detection and recognition, advanced photo enhancement and restoration, AI-powered smart tagging, family vault sharing, and social media integration. The platform uses a subscription-based model and aims to provide advanced photo management solutions to a broad market.

## Recent Changes
**October 23, 2025** - Added Download All Images Feature:
- Added "Download All" button to dashboard header button group for quick photo backup
- Created `/download-all` route that generates ZIP file containing all user photos
- ZIP file organizes photos into "original/" and "edited/" folders for easy navigation
- Implemented loading state with spinner while preparing download
- Timestamped filename format: `StoryKeep_Photos_username_YYYYMMDD_HHMMSS.zip`
- Fixed empty ZIP issue: Updated route to properly download files from Replit Object Storage
- Route now intelligently handles both object storage (`users/` prefix) and local filesystem photos
- Uses `app_storage.download_file()` for object storage and `zipf.writestr()` to add bytes to ZIP
- Proper error handling for empty photo libraries and file access issues
- Architect-reviewed and approved with PASS rating
- Server restarted successfully with new download feature enabled

**October 22, 2025** - Professional Photo Restoration Enhancement Pipeline:
- Added comprehensive post-processing enhancement pipeline to dramatically improve repaired photo quality
- Implemented sharpen_image() using unsharp masking (strength 1.5) to restore detail lost during damage repair
- Implemented enhance_contrast_clahe() with adaptive histogram equalization (clip_limit 3.0, 8x8 tiles) for superior tonal range
- Implemented denoise_preserve_edges() using bilateral filtering (7px, 50/50) to reduce blur artifacts while preserving edges
- Implemented normalize_brightness_contrast() with LAB color space normalization (5-250 range) for optimal brightness/contrast
- Created post_process_repair() orchestration function that chains all enhancements in optimal sequence: denoise → CLAHE → sharpen → normalize
- Updated comprehensive_repair() to apply full enhancement pipeline as final step, producing professional-quality results
- Added optional apply_enhancement parameter to individual repair methods (scratches, cracks) with lighter enhancement settings
- Comprehensive repair now prevents double-processing by disabling intermediate enhancements
- All enhancements architect-reviewed and approved with PASS rating; noted to monitor LAB normalization on very dark/bright photos
- Enhancement parameters professionally tuned for balanced restoration without over-processing artifacts
- Server restarted successfully with OpenCV damage repair features fully enabled

**October 22, 2025** - Comprehensive Edge Detection Upgrades:
- Implemented advanced multi-scale pyramid detection (3 scales: 1.0x, 0.75x, 0.5x) to catch photos of all sizes including small photos
- Added adaptive preprocessing pipeline with shadow removal, glare mitigation, and illumination normalization for challenging lighting conditions
- Implemented hierarchical contour detection (RETR_TREE) for detecting overlapping and touching photos
- Added watershed segmentation to separate touching photos with shared edges
- Implemented special photo type detection: Polaroid recognition (white border detection), faded photo enhancement (aggressive CLAHE)
- Added geometric validation with texture analysis and relaxed angle checks (60-120° instead of 70-110°) to reduce false positives while improving recall
- Implemented Non-Maximum Suppression (NMS) to merge overlapping detections and prevent duplicates
- Enhanced frontend JavaScript real-time detection with matching preprocessing stack (illumination normalization, CLAHE 3.0, bilateral blur, Canny+Sobel fusion)
- Expanded aspect ratio support for Polaroids (0.8-1.0), panoramic (0.3-0.5), and tall photos (2.0-3.3)
- Lowered minimum area threshold from 5% to 2% for small photo detection
- Added backward compatibility alias `PhotoDetector = AdvancedPhotoDetector` to prevent breaking changes
- All improvements architect-reviewed and approved with PASS rating for coherent integration and comprehensive edge-case coverage

**October 20, 2025** - Fixed People Page Flashing Issue on Railway:
- Fixed SQLAlchemy 2.0 pagination bug causing People page to flash/flicker on Railway
- Replaced deprecated `Query.paginate()` with `db.paginate(select(Person).where()...)` 
- Updated People route to use proper SQLAlchemy 2.0 syntax with `.where()` instead of `.filter_by()`
- Created comprehensive deployment guide (RAILWAY_PEOPLE_PAGE_FIX.md) with step-by-step instructions
- Verified fix locally - server running without errors
- Ready for Railway deployment to resolve production flashing issue

**Earlier Today** - Environment Restored After System Restart:
- Reinstalled all Python dependencies from requirements.txt (Flask, SQLAlchemy, Pillow, OpenCV, etc.)
- Reinstalled Expo and 744 npm packages in StoryKeep-iOS directory
- Restarted both workflows: PhotoVault Server (port 5000) and Expo Server (Metro Bundler with tunnel)
- Both servers verified and running successfully with no critical errors
- Database initialized successfully with subscription plans configured

**Previous Session** - Codebase Optimization & Bug Fixes:
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

**Advanced Photo Detection System** (`AdvancedPhotoDetector`) implements production-grade edge detection with:
- Multi-scale pyramid processing (1.0x, 0.75x, 0.5x) for size-invariant detection
- Adaptive preprocessing: shadow removal, glare mitigation, illumination normalization, CLAHE enhancement
- Multi-strategy edge detection combining adaptive Canny with Sobel edges
- Hierarchical contour analysis (RETR_TREE) for overlapping photo detection
- Watershed segmentation for separating touching photos
- Special detection modes: Polaroid white-border recognition, faded photo aggressive enhancement
- Geometric validation: quadrilateral approximation, corner angle checking (60-120°), texture analysis, edge strength validation
- Non-Maximum Suppression (NMS) for merging overlapping detections
- Confidence scoring system with area-based, aspect-ratio-based, and geometry-based metrics
- Corner refinement with sub-pixel accuracy for precise extraction

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
- **Photo Management**: Upload with metadata extraction, automatic face detection and tagging, enhancement, restoration, colorization, AI smart tagging, gallery organization, search, and filtering. Includes bulk deletion and download all photos as ZIP backup.
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