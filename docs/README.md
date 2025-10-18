# PhotoVault / StoryKeep - Technical Documentation

## Overview

PhotoVault (web) and StoryKeep (mobile) is a comprehensive photo management and digitization platform designed to preserve and enhance family memories. The system combines advanced image processing, AI-powered enhancements, and cloud storage to create a complete digital photo archive solution.

## Project Structure

```
photovault/
├── photovault/              # Main Flask application
│   ├── routes/             # API and web route blueprints
│   ├── services/           # Business logic and integrations
│   ├── utils/              # Helper functions and utilities
│   ├── templates/          # Jinja2 HTML templates
│   ├── static/             # CSS, JavaScript, images
│   └── models.py           # Database models
├── StoryKeep-iOS/          # React Native/Expo mobile app
│   ├── src/
│   │   ├── screens/        # Mobile app screens
│   │   ├── components/     # Reusable UI components
│   │   ├── services/       # API client and services
│   │   └── utils/          # Helper functions
├── migrations/             # Database migration scripts
├── docs/                   # Technical documentation
└── tests/                  # Test suites
```

## Design Philosophy: Mobile-First Legacy Photo Restoration

PhotoVault/StoryKeep is designed with a clear platform split optimized for different use cases:

### 📱 Mobile App (StoryKeep) - Legacy Photo Digitization
**Purpose**: Quick digitization and restoration of old physical photos

**Core Features**:
- **Smart Camera**: Edge detection and auto-capture for physical photos
- **Photo Extraction**: Automatic detection and cropping
- **Sharpen**: Fix blurry or degraded old photos
- **Colorize (DNN)**: Fast colorization for B&W photos
- **Colorize (AI)**: Intelligent AI-powered colorization
- **Offline Queue**: Capture without internet, upload later
- **Family Vaults**: Share restored photos instantly

**Why Mobile-First?**
- Old photos are physical - users need a camera-first solution
- Quick restoration tools (sharpen, colorize) for immediate results
- Simple, focused UI for elderly users digitizing family memories

### 💻 Web Platform (PhotoVault) - Advanced Photo Editing
**Purpose**: Comprehensive photo management and advanced editing

**All Mobile Features Plus**:
- **Advanced Editing**: Full suite of adjustment tools (brightness, contrast, filters)
- **Face Detection**: Automatic person tagging and recognition
- **Batch Processing**: Edit multiple photos simultaneously
- **Social Sharing**: Direct integration with social media platforms
- **Voice Memos**: Attach audio recordings to photos
- **Subscription Management**: Malaysian market-focused billing with SST compliance
- **Detailed Analytics**: Photo metadata and insights

**Why Web for Advanced Features?**
- Larger screen for precise editing
- More complex workflows benefit from desktop UI
- Non-time-sensitive tasks done at home

## Key Features

### Web Platform (PhotoVault)
- **Photo Management**: Upload, organize, and manage photo collections
- **Advanced Editing**: Full editing suite with filters, adjustments, and effects
- **AI Integration**: Google Gemini-powered photo analysis and colorization
- **Family Vaults**: Shared photo collections with role-based access
- **Voice Memos**: Attach audio recordings to photos
- **Face Recognition**: Detect and tag people in photos
- **Social Sharing**: Direct integration with social media platforms
- **Subscription Billing**: Malaysian market-focused pricing with SST compliance

### Mobile App (StoryKeep) - Legacy Photo Focus
- **Smart Camera**: Edge detection, auto-capture, batch mode for physical photos
- **Photo Digitization**: Automatic photo detection and extraction
- **Sharpen**: Fix blurry or degraded old photos
- **Colorize (DNN & AI)**: Two colorization options for B&W photos
- **Offline Support**: Local storage and background upload queue
- **Gallery Management**: Filter, sort, and manage photo collections
- **Family Vaults**: Access and manage shared family photos
- **Secure Authentication**: JWT-based auth with biometric login support

## Technology Stack

### Backend
- **Framework**: Flask 3.0.3 (Python)
- **Database**: PostgreSQL with SQLAlchemy 2.0 ORM
- **Authentication**: Flask-Login (web), JWT (mobile)
- **Image Processing**: Pillow, OpenCV (headless)
- **AI Services**: Google Gemini API
- **Storage**: Replit Object Storage with local fallback
- **Email**: SendGrid integration
- **Payments**: Stripe (Malaysian market)

### Frontend (Web)
- **Templates**: Jinja2 with Bootstrap 5
- **JavaScript**: Vanilla JS with modern ES6+
- **Styling**: Custom CSS with responsive design

### Mobile App
- **Framework**: React Native with Expo SDK 54
- **Navigation**: React Navigation
- **State Management**: React Hooks + AsyncStorage
- **HTTP Client**: Axios
- **Camera**: expo-camera
- **Image Processing**: expo-image-manipulator
- **Secure Storage**: expo-secure-store

## Documentation Index

1. [**Architecture Guide**](./ARCHITECTURE.md) - System design and patterns
2. [**API Documentation**](./API_DOCUMENTATION.md) - Complete API reference
3. [**Database Schema**](./DATABASE_SCHEMA.md) - Data models and relationships
4. [**Deployment Guide**](./DEPLOYMENT_GUIDE.md) - Production deployment instructions
5. [**Mobile App Guide**](./MOBILE_APP_GUIDE.md) - iOS app architecture
6. [**Security Guide**](./SECURITY.md) - Security implementation details
7. [**Developer Setup**](./DEVELOPER_SETUP.md) - Getting started for new developers

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Node.js 20+ (for mobile app)
- Expo CLI (for mobile development)

### Local Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd photovault
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Initialize database**
```bash
flask db upgrade
```

5. **Run development server**
```bash
python dev.py
```

6. **Install mobile app dependencies** (optional)
```bash
cd StoryKeep-iOS
npm install
npx expo start --tunnel
```

## Environment Variables

### Core Configuration
- `SECRET_KEY` - Flask secret key for session management
- `DATABASE_URL` - PostgreSQL connection string
- `UPLOAD_FOLDER` - Local file upload directory

### External Services
- `GOOGLE_GENAI_API_KEY` - Google Gemini API key for AI features
- `SENDGRID_API_KEY` - SendGrid API key for email
- `STRIPE_SECRET_KEY` - Stripe secret key for payments
- `STRIPE_PUBLISHABLE_KEY` - Stripe publishable key

### Storage Configuration
- `REPLIT_OBJECT_STORAGE_URL` - Object storage endpoint
- `REPLIT_OBJECT_STORAGE_KEY` - Storage access key

## API Base URLs

### Development
- Web App: `http://localhost:5000`
- Mobile API: `http://localhost:5000/api`

### Production
- Web App: `https://web-production-535bd.up.railway.app`
- Mobile API: `https://web-production-535bd.up.railway.app/api`

## Support and Contact

For technical support or questions:
- Review the [Developer Setup Guide](./DEVELOPER_SETUP.md)
- Check the [API Documentation](./API_DOCUMENTATION.md)
- Review the [Architecture Guide](./ARCHITECTURE.md)

## License

Copyright © 2025 Calmic. All rights reserved.
