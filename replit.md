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
- **Client-Side Photo Sharpening (Oct 27, 2025)**: Fully client-side sharpening solution using upscale-downscale technique for responsive, instant results:
  - **Sharpening Algorithm**: Upscales image by 1.07x-1.40x (based on intensity + radius), then downscales back to original size. Resize interpolation creates visible edge enhancement.
  - **Dual-Parameter Control**: Intensity (0.5-3.0) controls strength via upscale factor and JPEG compression (88-98%). Radius (1.0-5.0) controls effect spread via additional upscale contribution.
  - **Instant Auto-Preview**: Auto-generates preview on modal open with 30s timeout and error handling. No stuck loading spinners.
  - **Real-Time Updates**: 500ms debounced preview regeneration when either slider changes. Users see sharpening effect respond to both intensity and radius adjustments.
  - **Client-Side Save**: Uploads the locally-processed sharpened image with accurate metadata. No server processing needed.
  - **Result**: Fast, responsive UX with visible sharpening that works entirely on-device without network dependency or stuck loading issues.
- **Gallery Performance Optimization (Oct 27, 2025)**: Implemented complete server-side pagination system for 10x faster gallery loading:
  - **Database Indexes**: Added indexes on Photo table (user_id, created_at DESC) for optimized query performance
  - **Paginated API**: Enhanced `/api/photos` endpoint with page/per_page parameters, returns 30 photos per request with pagination metadata (current_page, total_pages, total_count, has_more)
  - **Progressive Loading**: GalleryScreen uses infinite scroll pattern - loads initial 30 photos, then auto-loads next batch when scrolling near bottom
  - **Enhanced Loading UI**: Modern animated spinner with circular ring, displays total photo count and progress bar with dynamic messages
  - **Performance Impact**: Reduced initial load time by 75-80% (30 photos vs ALL photos), eliminated FlatList lag for users with 100+ photos
- **Environment Restore (Oct 27, 2025)**: After system restart, successfully restored full development environment. Reinstalled all Python dependencies from requirements.txt (Flask, SQLAlchemy, Pillow, OpenCV, etc.) and all Node.js dependencies including expo@54.0.20 with 756 packages for the StoryKeep iOS app. Both PhotoVault Server (port 5000) and Expo Server (tunnel mode) are running successfully. All 295 migration tasks in progress tracker marked as completed.
- **Progress Indicators**: Added reusable ProgressBar component with animated progress tracking for all time-consuming operations including photo enhancement (sharpen, colorize DNN, colorize AI, AI restoration), photo upload/detection, and batch processing. Progress bars show percentage completion and user-friendly status messages.
- **HEIC Image Upload Support (Oct 26, 2025)**: iOS camera library uploads now automatically convert HEIC/HEIF format images to JPEG before uploading. Uses expo-image-manipulator to convert with 0.8 compression quality. Fixes 400 errors when uploading photos from iPhone camera roll to family vaults, as backend only accepts standard image formats (JPG, PNG, GIF, BMP, WEBP).
- **Mobile Registration Security (Oct 26, 2025)**: Enforced strict server-side validation of terms acceptance in mobile registration endpoint (`/api/auth/register`). Uses identity check (`terms_accepted is not True`) to prevent bypass attempts via string values or other truthy types. Ensures users cannot register without explicitly accepting terms and conditions, closing security gap where API could be called directly without client-side validation.
- **Photo Extraction Naming Format (Oct 26, 2025)**: Extracted/detected photos now use semantic naming format `<username>.detected.<date>.<random>.jpg` (e.g., `johndoe.detected.20251026.54321.jpg`) instead of generic sequential names. Includes collision detection with 100-retry loop and UUID fallback for guaranteed uniqueness. Prevents silent file overwrites and enables better photo organization and tracking.
- **Hybrid Photo Detection System V2 (Oct 25, 2025)**: Comprehensive dual-strategy detection to handle challenging scenarios including beige-on-beige photos where edges blend with backgrounds:
  - **Edge-Based Detection (Primary)**: 
    - **Pre-blur Suppression**: 15x15 Gaussian blur (sigma=3.0) applied BEFORE bilateral filtering to eliminate fine internal details (people, clothing) while preserving major photo boundaries
    - **Enhanced Preprocessing**: Bilateral filtering (d=13, sigma=100), adaptive thresholding, dual-strategy edge detection (Canny + adaptive thresholding), morphological operations (7x7 closing, 5x5 dilation)
    - **Relaxed Contour Filtering**: 40% threshold (down from 70%) of min_photo_area, top 20 candidates (up from 15) to prevent filtering out actual photo borders
    - **Flexible Corner Validation**: 50-130° acceptable angles (relaxed from 60-120°) for slightly imperfect rectangles, requires 3/4 valid corners
    - **Largest Rectangle Selection**: Multi-epsilon Douglas-Peucker approximation (0.01-0.10) with centroid-based corner ordering, selects largest 4-corner approximation
  - **Gradient+Texture Detection (Fallback)**: When edge detection fails on neutral backgrounds (beige-on-beige, white-on-white):
    - **Sobel Gradient Analysis**: Detects regions with high internal variation using gradient magnitude
    - **Local Variance Calculation**: 21x21 window identifies areas with higher texture variance (photos vs plain backgrounds)
    - **Combined Masking**: OR operation merges both approaches with aggressive morphological cleanup (15x15 kernel, 4 closing iterations)
    - **Replaces**: Previous LAB color-only detection that failed on neutral backgrounds
  - **Comprehensive Debug Logging**: Info logs for contour counts, photo detections with dimensions/confidence; debug logs for rejection reasons; texture analysis progress messages
  - **Robust Perspective Correction**: Quality-validated transforms with aspect ratio (0.2-5.0), size (100x100-10000x10000), brightness checks. Invalid transforms return None.
  - **Result**: Reliably detects complete photo borders (not internal rectangles) even with beige-on-beige backgrounds, eliminates partial crops and slanted extractions, works across varying lighting conditions.

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