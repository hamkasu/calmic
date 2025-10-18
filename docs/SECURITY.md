# Security Documentation

## Overview

PhotoVault implements multiple layers of security to protect user data, prevent unauthorized access, and ensure compliance with security best practices.

## Authentication & Authorization

### 1. Password Security

#### Password Hashing
All passwords are hashed using Werkzeug's security functions with bcrypt:

```python
from werkzeug.security import generate_password_hash, check_password_hash

# Hashing password
password_hash = generate_password_hash(password, method='pbkdf2:sha256')

# Verifying password
is_valid = check_password_hash(password_hash, password)
```

**Security Features:**
- PBKDF2 with SHA-256
- Salt automatically generated
- 260,000 iterations (recommended for 2025)
- Passwords never stored in plaintext

#### Password Requirements

```python
def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Must contain uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Must contain lowercase letter"
    if not re.search(r'\d', password):
        return False, "Must contain number"
    return True, "Valid"
```

### 2. Session Management

#### Web Sessions (Flask-Login)

```python
from flask_login import LoginManager, login_user, logout_user

login_manager = LoginManager()
login_manager.session_protection = 'strong'

# Session configuration
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
```

**Security Features:**
- Secure flag (HTTPS only)
- HttpOnly flag (XSS protection)
- SameSite flag (CSRF protection)
- Session timeout (1 hour)
- Session fixation protection

### 3. JWT Authentication (Mobile)

#### Token Generation

```python
import jwt
from datetime import datetime, timedelta

def generate_token(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token
```

#### Token Verification

```python
from functools import wraps
from flask import request, jsonify

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid header format'}), 401
        
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated
```

**Security Features:**
- HS256 algorithm
- 30-day expiration
- User validation on each request
- Proper error handling

### 4. Hybrid Authentication

For file serving (supports both web and mobile):

```python
from flask_login import current_user

def hybrid_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = None
        
        # Try JWT first (mobile)
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]
                data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
                user = User.query.get(data['user_id'])
            except:
                pass
        
        # Fallback to session auth (web)
        if not user and current_user.is_authenticated:
            user = current_user
        
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        return f(user, *args, **kwargs)
    
    return decorated
```

## Input Validation & Sanitization

### 1. File Upload Security

#### Extension Validation

```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
```

#### MIME Type Validation

```python
import mimetypes

def validate_mime_type(file):
    mime_type = mimetypes.guess_type(file.filename)[0]
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    return mime_type in allowed_types
```

#### Content Validation

```python
from PIL import Image

def validate_image_content(file_stream):
    try:
        with Image.open(file_stream) as img:
            img.verify()  # Verify it's actually an image
            return True
    except Exception as e:
        logger.warning(f"Image validation failed: {str(e)}")
        return False
```

#### Size Limits

```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_IMAGE_DIMENSION = 4096  # 4096px

def validate_file_size(file):
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset
    return size <= MAX_FILE_SIZE

def validate_dimensions(file_path):
    with Image.open(file_path) as img:
        return img.width <= MAX_IMAGE_DIMENSION and \
               img.height <= MAX_IMAGE_DIMENSION
```

### 2. Filename Sanitization

```python
from werkzeug.utils import secure_filename
import re

def sanitize_filename(filename):
    # Remove path traversal attempts
    filename = secure_filename(filename)
    
    # Remove any remaining dangerous characters
    filename = re.sub(r'[^\w\-.]', '_', filename)
    
    # Ensure unique filename
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    name, ext = os.path.splitext(filename)
    return f"{name}_{unique_id}{ext}"
```

### 3. Path Traversal Prevention

```python
import os

def safe_join(directory, filename):
    """Safely join path components preventing traversal"""
    # Normalize and resolve
    filepath = os.path.normpath(os.path.join(directory, filename))
    
    # Ensure the path is within the directory
    if not filepath.startswith(os.path.abspath(directory)):
        raise ValueError("Path traversal attempt detected")
    
    return filepath
```

### 4. Input Sanitization

```python
import html
import re

def sanitize_input(text):
    """Sanitize user input"""
    # HTML escape
    text = html.escape(text)
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Limit length
    text = text[:1000]
    
    return text.strip()

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
```

## CSRF Protection

### 1. Web Forms

```python
from flask_wtf import CSRFProtect

csrf = CSRFProtect(app)

# In forms
from flask_wtf import FlaskForm
class PhotoUploadForm(FlaskForm):
    photo = FileField('Photo', validators=[DataRequired()])
    # CSRF token automatically added
```

### 2. API Endpoints

```python
from photovault.extensions import csrf

# Exempt mobile API endpoints
@mobile_api_bp.route('/auth/login', methods=['POST'])
@csrf.exempt
def mobile_login():
    # JWT provides protection for mobile
    pass
```

## SQL Injection Prevention

### 1. Parameterized Queries

```python
# GOOD - Using SQLAlchemy ORM
user = User.query.filter_by(username=username).first()

# GOOD - Parameterized raw SQL
result = db.session.execute(
    "SELECT * FROM users WHERE username = :username",
    {'username': username}
)

# BAD - String concatenation (vulnerable)
# query = f"SELECT * FROM users WHERE username = '{username}'"
```

### 2. Input Validation

```python
def validate_user_input(input_value):
    # Whitelist validation
    if not re.match(r'^[a-zA-Z0-9_]+$', input_value):
        raise ValueError("Invalid input")
    return input_value
```

## XSS Prevention

### 1. Template Auto-Escaping

Jinja2 auto-escapes by default:

```html
<!-- Safe - automatically escaped -->
<p>{{ user.username }}</p>

<!-- Unsafe - manual escaping needed -->
<p>{{ user.bio|safe }}</p>
```

### 2. Content Security Policy

```python
@app.after_request
def set_csp(response):
    response.headers['Content-Security-Policy'] = \
        "default-src 'self'; " \
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; " \
        "style-src 'self' 'unsafe-inline'; " \
        "img-src 'self' data: https:; " \
        "font-src 'self' data:;"
    return response
```

### 3. Security Headers

```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

## Rate Limiting

### 1. Upload Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@limiter.limit("10 per minute")
@photo_bp.route('/upload', methods=['POST'])
def upload_photo():
    pass
```

### 2. Authentication Rate Limiting

```python
@limiter.limit("5 per minute")
@auth_bp.route('/login', methods=['POST'])
def login():
    pass

@limiter.limit("3 per minute")
@auth_bp.route('/register', methods=['POST'])
def register():
    pass
```

## Secure File Storage

### 1. Access Control

```python
@gallery_bp.route('/uploads/<int:user_id>/<filename>')
@hybrid_auth
def uploaded_file(current_user, user_id, filename):
    # Verify user owns the file
    if current_user.id != user_id:
        abort(403)
    
    # Safe path construction
    file_path = safe_join(
        app.config['UPLOAD_FOLDER'],
        str(user_id),
        filename
    )
    
    if not os.path.exists(file_path):
        abort(404)
    
    return send_file(file_path)
```

### 2. Secure File Serving

```python
from flask import send_file

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    # Validate filename
    safe_filename = secure_filename(filename)
    
    # Verify ownership
    photo = Photo.query.filter_by(
        filename=safe_filename,
        user_id=current_user.id
    ).first_or_404()
    
    # Serve with proper headers
    return send_file(
        photo.file_path,
        as_attachment=True,
        download_name=photo.original_name
    )
```

## API Security

### 1. CORS Configuration

```python
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": ["exp://localhost:8081", "https://app.example.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
})
```

### 2. Request Size Limits

```python
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'error': 'File too large. Maximum size: 50MB'
    }), 413
```

## Data Protection

### 1. Encryption at Rest

```python
# Use Replit Object Storage with encryption
from photovault.services.app_storage_service import app_storage

# Files encrypted automatically by storage service
app_storage.upload_file(file_content, file_path)
```

### 2. Encryption in Transit

- HTTPS enforced in production
- TLS 1.2+ required
- Certificate pinning (mobile app)

### 3. Sensitive Data Handling

```python
# Never log sensitive data
logger.info(f"User {user.id} uploaded photo")  # Good
# logger.info(f"Password: {password}")  # BAD

# Never return sensitive data in API
def user_to_dict(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email
        # password_hash excluded
    }
```

## Mobile App Security

### 1. Secure Storage

```javascript
// Use SecureStore for sensitive data
import * as SecureStore from 'expo-secure-store';

await SecureStore.setItemAsync('authToken', token);
const token = await SecureStore.getItemAsync('authToken');
```

### 2. Certificate Pinning

```javascript
// app.json
{
  "expo": {
    "ios": {
      "infoPlist": {
        "NSAppTransportSecurity": {
          "NSExceptionDomains": {
            "api.example.com": {
              "NSIncludesSubdomains": true,
              "NSExceptionMinimumTLSVersion": "TLSv1.2",
              "NSExceptionRequiresForwardSecrecy": true
            }
          }
        }
      }
    }
  }
}
```

### 3. Biometric Security

```javascript
import * as LocalAuthentication from 'expo-local-authentication';

const authenticate = async () => {
  const result = await LocalAuthentication.authenticateAsync({
    promptMessage: 'Authenticate to continue',
    fallbackLabel: 'Use passcode',
  });
  
  return result.success;
};
```

## Security Monitoring

### 1. Logging

```python
import logging

# Log security events
logger.warning(f"Failed login attempt for user: {username}")
logger.error(f"Unauthorized access attempt to file: {filename}")
logger.info(f"Password reset requested for: {email}")
```

### 2. Audit Trail

```python
class SecurityEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    event_type = db.Column(db.String(50))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def log_security_event(user_id, event_type):
    event = SecurityEvent(
        user_id=user_id,
        event_type=event_type,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(event)
    db.session.commit()
```

## Security Checklist

### Deployment Security
- [ ] HTTPS enabled with valid certificate
- [ ] Security headers configured
- [ ] CSRF protection enabled
- [ ] Rate limiting configured
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified
- [ ] File upload security implemented
- [ ] Session security configured
- [ ] JWT security implemented
- [ ] Environment variables secured
- [ ] Debug mode disabled in production

### Data Security
- [ ] Passwords properly hashed
- [ ] Sensitive data encrypted
- [ ] Database backups encrypted
- [ ] Access control implemented
- [ ] Audit logging enabled

### API Security
- [ ] Authentication required
- [ ] Authorization checked
- [ ] Request validation
- [ ] Response sanitization
- [ ] CORS properly configured
- [ ] Rate limiting enabled

### Mobile Security
- [ ] Secure storage used
- [ ] Certificate pinning enabled
- [ ] Biometric auth implemented
- [ ] Token expiration handled
- [ ] Offline data encrypted

## Incident Response

### 1. Security Breach Procedure

1. **Immediate Actions:**
   - Rotate all API keys and secrets
   - Force logout all users
   - Disable affected endpoints
   - Enable maintenance mode

2. **Investigation:**
   - Review security logs
   - Identify breach scope
   - Document findings

3. **Remediation:**
   - Patch vulnerabilities
   - Update affected users
   - Implement additional security measures

4. **Post-Incident:**
   - Conduct security audit
   - Update security policies
   - Train development team

### 2. Vulnerability Disclosure

Contact: security@example.com

Response time: 24-48 hours
