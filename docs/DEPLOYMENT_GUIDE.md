# Production Deployment Guide

## Overview

This guide covers deploying PhotoVault to production on Railway (or similar platforms) with proper configuration for scaling, security, and reliability.

## Platform Requirements

### Minimum Requirements
- **Python**: 3.11 or higher
- **PostgreSQL**: 14 or higher
- **Node.js**: 20+ (for mobile app development)
- **Storage**: Object storage service (Replit Object Storage, AWS S3, etc.)
- **Memory**: 512MB minimum (1GB recommended)
- **Disk**: 2GB minimum

### Recommended Production Stack
- **Platform**: Railway, Heroku, or DigitalOcean App Platform
- **Database**: Neon, Supabase, or managed PostgreSQL
- **Storage**: Replit Object Storage, AWS S3, or CloudFlare R2
- **CDN**: CloudFlare (optional, for static assets)

---

## Railway Deployment (Primary)

### Step 1: Prepare Repository

1. **Ensure all changes are committed:**
```bash
git add .
git commit -m "Prepare for production deployment"
```

2. **Create production branch (optional):**
```bash
git checkout -b production
git push origin production
```

### Step 2: Railway Setup

1. **Connect GitHub Repository:**
   - Go to Railway dashboard
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Choose branch (main or production)

2. **Configure Build Settings:**
   ```
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn --bind=0.0.0.0:5000 --reuse-port main:app
   ```

3. **Set Python Version:**
   Create `runtime.txt`:
   ```
   python-3.11.0
   ```

### Step 3: Environment Variables

Configure these in Railway dashboard:

#### Core Settings
```bash
SECRET_KEY=<generate-strong-random-key>
FLASK_ENV=production
DEBUG=False
```

#### Database (Neon PostgreSQL)
```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

#### File Storage
```bash
UPLOAD_FOLDER=uploads
REPLIT_OBJECT_STORAGE_URL=<storage-endpoint>
REPLIT_OBJECT_STORAGE_KEY=<storage-key>
```

#### External Services
```bash
GOOGLE_GENAI_API_KEY=<gemini-api-key>
SENDGRID_API_KEY=<sendgrid-key>
STRIPE_SECRET_KEY=<stripe-secret>
STRIPE_PUBLISHABLE_KEY=<stripe-publishable>
```

#### Security
```bash
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

### Step 4: Database Migration

1. **Connect to Railway CLI:**
```bash
railway login
railway link
```

2. **Run migrations:**
```bash
railway run flask db upgrade
```

3. **Create subscription plans:**
```bash
railway run python -c "from photovault import create_app; app = create_app(); app.app_context().push(); from photovault.models import SubscriptionPlan, db; # Create plans here"
```

### Step 5: Deploy

```bash
git push origin production
```

Railway will automatically:
- Detect changes
- Build the application
- Run database migrations
- Deploy to production

### Step 6: Verify Deployment

1. **Check application logs:**
```bash
railway logs
```

2. **Test endpoints:**
```bash
curl https://your-app.railway.app/api
curl https://your-app.railway.app/auth/login
```

3. **Test mobile app connection:**
   - Update `BASE_URL` in `StoryKeep-iOS/src/services/api.js`
   - Test login and photo upload

---

## Configuration for Production

### 1. Gunicorn Configuration

Create `gunicorn.conf.py`:

```python
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "photovault"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Reloading
reload = False
reload_engine = "auto"
reload_extra_files = []
```

Update Railway start command:
```bash
gunicorn --config gunicorn.conf.py main:app
```

### 2. Production Flask Config

Update `config.py`:

```python
import os

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # Session configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # File upload
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = 'uploads'
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Logging
    LOG_LEVEL = 'INFO'
```

### 3. Database Connection Pooling

Update `photovault/extensions.py`:

```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(
    engine_options={
        'pool_size': 10,
        'max_overflow': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'pool_timeout': 30
    }
)
```

### 4. Error Handling

Add production error handlers in `main.py`:

```python
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f'Server Error: {error}', exc_info=True)
    return render_template('errors/500.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403
```

---

## Mobile App Production Configuration

### Update API Base URL

Edit `StoryKeep-iOS/src/services/api.js`:

```javascript
const BASE_URL = 'https://web-production-535bd.up.railway.app';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

### Build for Production

```bash
cd StoryKeep-iOS
npm run build
```

### iOS App Store Deployment

1. **Update app.json:**
```json
{
  "expo": {
    "name": "StoryKeep",
    "slug": "storykeep",
    "version": "1.0.0",
    "ios": {
      "bundleIdentifier": "com.calmic.storykeep",
      "buildNumber": "1"
    }
  }
}
```

2. **Build for iOS:**
```bash
eas build --platform ios
```

3. **Submit to App Store:**
```bash
eas submit --platform ios
```

---

## Security Hardening

### 1. HTTPS Configuration

Ensure Railway provides SSL certificate (automatic).

### 2. Content Security Policy

Add CSP headers in `main.py`:

```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

### 3. Rate Limiting

Install Flask-Limiter:
```bash
pip install Flask-Limiter
```

Configure in `photovault/__init__.py`:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Apply to routes
@limiter.limit("5 per minute")
@mobile_api_bp.route('/auth/login', methods=['POST'])
def mobile_login():
    # ...
```

### 4. Environment Variable Validation

Add startup validation in `main.py`:

```python
import sys

REQUIRED_ENV_VARS = [
    'SECRET_KEY',
    'DATABASE_URL',
    'GOOGLE_GENAI_API_KEY',
    'SENDGRID_API_KEY',
    'STRIPE_SECRET_KEY'
]

def validate_environment():
    missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

if __name__ == '__main__':
    validate_environment()
    app.run()
```

---

## Performance Optimization

### 1. Database Indexing

Create indexes for common queries:

```sql
CREATE INDEX idx_photo_user_created ON photo(user_id, created_at DESC);
CREATE INDEX idx_photo_favorite ON photo(user_id, is_favorite) WHERE is_favorite = TRUE;
CREATE INDEX idx_vault_photo_vault ON vault_photo(vault_id);
```

### 2. Caching Strategy

Install Flask-Caching:
```bash
pip install Flask-Caching
```

Configure caching:
```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL')
})

@cache.cached(timeout=300, key_prefix='user_photos')
def get_user_photos(user_id):
    return Photo.query.filter_by(user_id=user_id).all()
```

### 3. Image Optimization

Compress images on upload:

```python
from PIL import Image

def optimize_image(file_path, quality=85):
    with Image.open(file_path) as img:
        # Convert to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Optimize and save
        img.save(file_path, 'JPEG', quality=quality, optimize=True)
```

---

## Monitoring and Logging

### 1. Application Logging

Configure structured logging:

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler(
        'logs/photovault.log',
        maxBytes=10240000,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('PhotoVault startup')
```

### 2. Error Tracking

Integrate Sentry:

```bash
pip install sentry-sdk[flask]
```

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

### 3. Health Check Endpoint

Add health check for monitoring:

```python
@app.route('/health')
def health_check():
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
```

---

## Backup Strategy

### 1. Database Backups

Set up automated backups on Railway:
- Enable automatic daily backups
- Retention: 7 days minimum

Manual backup:
```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### 2. File Storage Backups

For Replit Object Storage:
```python
from photovault.services.app_storage_service import app_storage

def backup_user_files(user_id):
    files = app_storage.list_files(f'users/{user_id}/')
    for file in files:
        content = app_storage.get_file_content(file)
        # Upload to backup storage
```

---

## Rollback Procedure

### Quick Rollback

1. **Revert to previous deployment:**
```bash
railway rollback
```

2. **Verify application:**
```bash
railway logs
curl https://your-app.railway.app/health
```

### Database Rollback

1. **Downgrade migration:**
```bash
railway run flask db downgrade
```

2. **Restore from backup:**
```bash
psql $DATABASE_URL < backup_20251012.sql
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations created and tested
- [ ] SSL certificate configured
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] Error tracking enabled
- [ ] Backup strategy in place

### Post-Deployment
- [ ] Health check endpoint responding
- [ ] Database connectivity verified
- [ ] File uploads working
- [ ] Mobile app connecting successfully
- [ ] Email notifications working
- [ ] Payment processing functional
- [ ] Monitoring dashboards configured
- [ ] Backup jobs scheduled

### Performance Verification
- [ ] Page load times < 2 seconds
- [ ] API response times < 500ms
- [ ] Image optimization working
- [ ] Database queries optimized
- [ ] No N+1 query issues
- [ ] Caching effective

---

## Troubleshooting

### Common Issues

**Database Connection Errors:**
```bash
# Check connection
railway run python -c "from photovault import db; print(db.engine.url)"

# Test query
railway run python -c "from photovault import db; db.session.execute('SELECT 1')"
```

**File Upload Failures:**
```bash
# Check storage configuration
railway run python -c "from photovault.services.app_storage_service import app_storage; print(app_storage.is_available())"
```

**Mobile App Connection Issues:**
- Verify BASE_URL in mobile app
- Check CORS headers in Flask app
- Verify JWT token generation
- Test with curl:
  ```bash
  curl -X POST https://your-app.railway.app/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"password"}'
  ```

---

## Support Resources

- **Railway Docs**: https://docs.railway.app
- **Flask Docs**: https://flask.palletsprojects.com
- **PostgreSQL Docs**: https://www.postgresql.org/docs
- **Expo Docs**: https://docs.expo.dev
