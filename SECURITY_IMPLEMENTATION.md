# PhotoVault Enterprise Security Implementation Guide

## Overview
This document describes the enterprise-grade security features implemented for PhotoVault/StoryKeep, including rate limiting, multi-factor authentication (MFA/2FA), OAuth social login, token refresh, and enhanced password policies.

## Completed Infrastructure

### 1. Database Schema
All security tables have been created via migration (`migrations/add_security_tables.sql`):

- **login_attempt**: Tracks all login attempts for audit and rate limiting
- **account_lockout**: Manages temporary account lockouts after failed attempts
- **refresh_token**: Stores hashed JWT refresh tokens for secure token rotation (uses scrypt hashing)
- **mfa_secret**: Stores TOTP secrets and hashed backup codes for 2FA (uses scrypt hashing)
- **oauth_provider**: Links users to OAuth providers (Google, Apple) with unique constraints
- **security_log**: Comprehensive security event logging

**Security Features:**
- Refresh tokens are hashed before storage using scrypt and verified with constant-time comparison
- MFA backup codes are hashed before storage using scrypt and verified with constant-time comparison
- OAuth provider has unique constraint on (provider, provider_user_id) to prevent duplicate bindings
- All sensitive credentials use constant-time comparison to prevent timing attacks

### 2. Security Utilities Created

#### Password Security (`photovault/utils/security.py`)
- `validate_password_strength()`: Enforces enterprise password policy:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character
- `track_login_attempt()`: Records all login attempts with IP and user agent
- `check_account_lockout()`: Prevents login if account is locked
- `lockout_account()`: Implements progressive lockout (5 minutes to 24 hours)
- `unlock_account()`: Manual or automatic unlock
- `log_security_event()`: Centralized security logging with severity levels

#### MFA/2FA (`photovault/utils/mfa.py`)
- `generate_mfa_secret()`: Creates TOTP secret with QR code and backup codes
- `verify_mfa_code()`: Validates TOTP codes with time drift tolerance
- `enable_mfa()`: Enables MFA after successful verification
- `disable_mfa()`: Disables MFA (keeps audit trail)
- `verify_backup_code()`: One-time use backup codes for account recovery
- `regenerate_backup_codes()`: Creates new backup codes

#### OAuth 2.0 Social Login (`photovault/utils/oauth.py`)
- `init_oauth()`: Configures Google and Apple OAuth providers
- `get_or_create_oauth_user()`: Links OAuth accounts to users
- `disconnect_oauth_provider()`: Safely removes OAuth connections

#### Rate Limiting
- Flask-Limiter initialized with configurable storage backend:
  - Development: In-memory storage (automatic)
  - Production: Redis storage (set RATELIMIT_STORAGE_URL environment variable)
  - Default limits: 200 requests per day, 50 requests per hour (global)
  - Per-route custom limits can be applied
- **Important**: For production deployments with multiple processes, configure Redis storage

### 3. Dependencies Installed
```
Flask-Limiter==3.9.0
pyotp==2.9.0
qrcode[pil]==8.0
Authlib==1.4.0
```

## Environment Variables Required

### OAuth Configuration (Optional)
Add these to your environment or Replit Secrets:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Apple OAuth (Sign in with Apple)
APPLE_CLIENT_ID=com.your.bundle.id
APPLE_CLIENT_SECRET=your_apple_client_secret

# App Configuration
SECRET_KEY=your_secret_key_here

# Rate Limiting (Production - Required for multi-process deployments)
RATELIMIT_STORAGE_URL=redis://localhost:6379
# For development, memory:// is used automatically if not set
```

### Obtaining OAuth Credentials

#### Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select existing
3. Enable "Google+ API"
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Add authorized redirect URIs:
   - Development: `http://localhost:5000/auth/google/callback`
   - Production: `https://yourdomain.com/auth/google/callback`

#### Apple Sign In
1. Go to [Apple Developer Portal](https://developer.apple.com/)
2. Certificates, Identifiers & Profiles → Identifiers
3. Register a new App ID with "Sign in with Apple" capability
4. Create a Service ID
5. Configure redirect URIs

## Implementation Status

### ✅ Completed
- [x] Database schema and migrations
- [x] Security utility modules
- [x] MFA/TOTP implementation
- [x] OAuth framework setup
- [x] Flask-Limiter integration
- [x] Password strength validation
- [x] Login attempt tracking
- [x] Account lockout logic
- [x] Security event logging

### ⏳ Pending Integration
- [ ] Update authentication routes to use new security utilities
- [ ] Implement MFA endpoints (setup, verify, enable/disable)
- [ ] Implement OAuth endpoints (login, callback, disconnect)
- [ ] Implement token refresh endpoints
- [ ] Add rate limiting decorators to sensitive routes
- [ ] Update iOS app to support MFA and OAuth

## Integration Examples

### Example 1: Adding Rate Limiting to Login Route
```python
from photovault.extensions import limiter

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # Max 5 login attempts per minute
def login():
    # Your login logic here
    pass
```

### Example 2: Using Password Validation
```python
from photovault.utils.security import validate_password_strength

@auth_bp.route('/register', methods=['POST'])
def register():
    password = request.form.get('password')
    
    is_valid, errors = validate_password_strength(password)
    if not is_valid:
        return jsonify({'error': 'Password requirements not met', 'details': errors}), 400
    
    # Continue with registration
```

### Example 3: Tracking Login Attempts
```python
from photovault.utils.security import track_login_attempt, check_account_lockout

@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    
    # Check if account is locked
    is_locked, unlock_time = check_account_lockout(username)
    if is_locked:
        return jsonify({'error': f'Account locked until {unlock_time}'}), 403
    
    # Authenticate user
    user = authenticate(username, password)
    
    # Track the attempt
    track_login_attempt(
        username_or_email=username,
        success=(user is not None),
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        failure_reason=None if user else "Invalid credentials"
    )
    
    # Continue with login
```

### Example 4: Enabling MFA
```python
from photovault.utils.mfa import generate_mfa_secret, verify_mfa_code, enable_mfa

@auth_bp.route('/mfa/setup', methods=['POST'])
@login_required
def setup_mfa():
    user_id = current_user.id
    username = current_user.username
    
    # Generate MFA secret and QR code
    secret, qr_code, backup_codes = generate_mfa_secret(user_id, username)
    
    return jsonify({
        'qr_code': qr_code,  # Data URI for QR code image
        'backup_codes': backup_codes,
        'message': 'Scan QR code with your authenticator app'
    })

@auth_bp.route('/mfa/enable', methods=['POST'])
@login_required
def enable_mfa_route():
    code = request.json.get('code')
    
    # Verify code before enabling
    success, message = enable_mfa(current_user.id, code)
    
    return jsonify({
        'success': success,
        'message': message
    }), 200 if success else 400
```

### Example 5: OAuth Login Flow
```python
from photovault.utils.oauth import oauth, get_or_create_oauth_user

@auth_bp.route('/login/google')
def google_login():
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/auth/google/callback')
def google_callback():
    # Get OAuth token
    token = oauth.google.authorize_access_token()
    
    # Get user info
    user_info = token.get('userinfo')
    
    # Create or link user
    user, is_new, oauth_conn = get_or_create_oauth_user(
        provider='google',
        provider_user_id=user_info['sub'],
        email=user_info['email'],
        display_name=user_info.get('name'),
        profile_picture=user_info.get('picture')
    )
    
    # Log in the user
    login_user(user)
    
    return redirect(url_for('main.dashboard'))
```

## Security Best Practices

### 1. Password Requirements
- Minimum 8 characters
- Mixed case (upper and lower)
- Numbers and special characters
- No common patterns

### 2. Account Lockout Policy
- 3 failed attempts: 5 minutes lockout
- 5 failed attempts: 15 minutes lockout
- 10+ failed attempts: 24 hours lockout
- Admin can manually unlock accounts

### 3. MFA Recommendations
- Encourage all users to enable MFA
- Provide 10 backup codes per user
- Allow regenerating backup codes
- Support authenticator apps (Google Authenticator, Authy, etc.)

### 4. Rate Limiting Strategy
- Login: 5 attempts per minute per IP
- Registration: 3 per hour per IP
- Password reset: 3 per hour per user
- API endpoints: 100 per hour per user

### 5. Security Logging
- Log all authentication events
- Log MFA changes
- Log OAuth connections/disconnections
- Log account lockouts and unlocks
- Include IP address and user agent

## Production Deployment

### Running the Migration
On production (Railway), run:
```bash
python -c "from photovault.extensions import db; from photovault import create_app; app = create_app('production'); app.app_context().push(); from sqlalchemy import text; db.session.execute(text(open('migrations/add_security_tables.sql').read())); db.session.commit(); print('Migration completed')"
```

### Environment Setup
1. Add OAuth credentials to Railway environment variables
2. Ensure `SECRET_KEY` is set to a strong random value
3. Configure redirect URIs for production domain
4. Test OAuth flows in production environment

## Testing

### Test MFA Flow
1. Create a test user
2. Call `/mfa/setup` to get QR code
3. Scan with authenticator app
4. Call `/mfa/enable` with TOTP code
5. Test login with MFA required

### Test OAuth Flow
1. Configure test OAuth apps
2. Test Google login flow
3. Test Apple login flow
4. Test account linking (existing user)
5. Test account creation (new user)

### Test Account Lockout
1. Attempt login with wrong password 3 times
2. Verify account is locked
3. Wait for lockout period
4. Verify automatic unlock

## Next Steps

### Phase 1: Core Security (Priority)
1. Update web authentication routes with security utilities
2. Add rate limiting to login, registration, password reset
3. Implement enhanced password validation on registration

### Phase 2: MFA Implementation
1. Create MFA setup endpoints
2. Create MFA verification endpoints
3. Update login flow to check MFA status
4. Create UI for MFA setup

### Phase 3: OAuth Integration
1. Create OAuth login routes
2. Create OAuth callback handlers
3. Create OAuth disconnect endpoints
4. Update UI with social login buttons

### Phase 4: Mobile API
1. Update mobile API authentication
2. Add token refresh endpoints
3. Support MFA in mobile app
4. Support OAuth in mobile app

## Support & Troubleshooting

### Common Issues

**MFA not working:**
- Verify server time is synchronized (TOTP is time-sensitive)
- Check that secret was properly saved to database
- Verify authenticator app is using correct secret

**OAuth callback errors:**
- Verify redirect URIs match exactly in OAuth provider settings
- Check that OAuth credentials are correct
- Ensure HTTPS is used in production

**Account lockout issues:**
- Check `account_lockout` table for active lockouts
- Verify unlock times are in correct timezone
- Use `unlock_account()` utility for manual unlock

### Database Queries for Debugging

```sql
-- Check active lockouts
SELECT * FROM account_lockout WHERE is_active = true;

-- View recent login attempts
SELECT * FROM login_attempt ORDER BY attempted_at DESC LIMIT 50;

-- Check MFA status for user
SELECT * FROM mfa_secret WHERE user_id = YOUR_USER_ID;

-- View OAuth connections
SELECT * FROM oauth_provider WHERE user_id = YOUR_USER_ID;

-- Recent security events
SELECT * FROM security_log ORDER BY created_at DESC LIMIT 100;
```

## Conclusion

The security infrastructure is now in place. The next phase is integrating these features into the authentication routes and user interface. All utilities are production-ready and follow enterprise security best practices.

For questions or issues, refer to the utility module source code which includes comprehensive docstrings and error handling.
