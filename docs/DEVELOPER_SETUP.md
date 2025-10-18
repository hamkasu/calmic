# Developer Setup Guide

## Overview

This guide will help you set up a complete development environment for PhotoVault/StoryKeep on your local machine or Replit environment.

## Prerequisites

### Required Software
- **Python 3.11+** - Backend runtime
- **PostgreSQL 14+** - Database
- **Node.js 20+** - Mobile app development
- **Git** - Version control
- **Expo CLI** - Mobile app tooling (optional)

### Recommended Tools
- **VS Code** or **PyCharm** - Code editor
- **Postman** or **Insomnia** - API testing
- **pgAdmin** or **DBeaver** - Database management
- **Xcode** (macOS only) - iOS development
- **Expo Go app** - Mobile testing

## Initial Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd photovault
```

### 2. Environment Configuration

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_APP=main.py
FLASK_ENV=development
DEBUG=True

# Database (PostgreSQL)
DATABASE_URL=postgresql://username:password@localhost:5432/photovault

# File Upload
UPLOAD_FOLDER=uploads
MAX_UPLOAD_SIZE=52428800  # 50MB

# External Services (Optional for local dev)
GOOGLE_GENAI_API_KEY=your-gemini-api-key
SENDGRID_API_KEY=your-sendgrid-key
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key

# Object Storage (Optional)
REPLIT_OBJECT_STORAGE_URL=
REPLIT_OBJECT_STORAGE_KEY=
```

### 3. Generate Secret Key

```python
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output to `SECRET_KEY` in `.env`.

## Backend Setup

### 1. Install Python Dependencies

#### Using pip (Recommended for Replit)

```bash
pip install -r requirements.txt
```

#### Using virtual environment (Local development)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

#### Install PostgreSQL

**macOS (Homebrew):**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download from https://www.postgresql.org/download/windows/

#### Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE photovault;

# Create user (optional)
CREATE USER photovault_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE photovault TO photovault_user;

# Exit
\q
```

#### Run Migrations

```bash
# Initialize migrations (first time only)
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

### 3. Create Admin User

```bash
python -c "
from photovault import create_app, db
from photovault.models import User

app = create_app()
with app.app_context():
    admin = User(
        username='admin',
        email='admin@example.com',
        is_admin=True,
        is_superuser=True
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print('Admin user created: admin / admin123')
"
```

### 4. Create Subscription Plans

```bash
python -c "
from photovault import create_app, db
from photovault.models import SubscriptionPlan

app = create_app()
with app.app_context():
    plans = [
        {
            'name': 'Free',
            'price_myr': 0,
            'storage_gb': 0.1,
            'max_photos': 100,
            'max_vaults': 1,
            'ai_features': False
        },
        {
            'name': 'Basic',
            'price_myr': 9.90,
            'storage_gb': 5,
            'max_photos': 1000,
            'max_vaults': 5,
            'ai_features': True
        },
        {
            'name': 'Pro',
            'price_myr': 29.90,
            'storage_gb': 50,
            'max_photos': None,
            'max_vaults': 20,
            'ai_features': True
        }
    ]
    
    for plan_data in plans:
        plan = SubscriptionPlan(**plan_data)
        db.session.add(plan)
    
    db.session.commit()
    print('Subscription plans created')
"
```

### 5. Run Development Server

```bash
# Standard Flask development server
python dev.py

# Or using Flask CLI
flask run --host=0.0.0.0 --port=5000

# With auto-reload
flask run --reload
```

The web application will be available at `http://localhost:5000`.

## Mobile App Setup

### 1. Install Node.js Dependencies

```bash
cd StoryKeep-iOS
npm install
```

### 2. Install Expo CLI (Global)

```bash
npm install -g expo-cli
# or
npm install -g @expo/cli
```

### 3. Update API Configuration

Edit `src/services/api.js`:

```javascript
// For local development
const BASE_URL = 'http://localhost:5000';

// For Replit development
// const BASE_URL = 'https://your-repl-name.username.repl.co';

// For production
// const BASE_URL = 'https://web-production-535bd.up.railway.app';

export default BASE_URL;
```

### 4. Start Expo Development Server

```bash
# Start with tunnel (recommended for testing on real device)
npx expo start --tunnel

# Or start normally
npx expo start

# Or with cleared cache
npx expo start --clear
```

### 5. Test on Device

#### iOS (Physical Device)
1. Install "Expo Go" from App Store
2. Scan QR code from terminal
3. App will load on your device

#### iOS (Simulator - macOS only)
1. Install Xcode from App Store
2. Press `i` in Expo terminal
3. App will open in iOS Simulator

#### Android (Physical Device)
1. Install "Expo Go" from Play Store
2. Scan QR code from terminal
3. App will load on your device

## Development Workflows

### Workflow 1: Backend Development

**Configure workflow (Replit):**
```bash
# Workflow name: PhotoVault Server
# Command: python dev.py
# Port: 5000
```

**Test backend:**
```bash
# Health check
curl http://localhost:5000/

# Test login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Test API
curl http://localhost:5000/api \
  -H "Authorization: Bearer <token>"
```

### Workflow 2: Mobile Development

**Configure workflow (Replit):**
```bash
# Workflow name: Expo Server
# Command: cd StoryKeep-iOS && npx expo start --tunnel
# Port: 8081
```

**Mobile development flow:**
1. Make changes to React Native code
2. Expo auto-reloads on save
3. Shake device to open dev menu
4. Use "Reload" or "Debug" as needed

## Database Management

### View Database

```bash
# Connect to database
psql $DATABASE_URL

# List tables
\dt

# View users
SELECT id, username, email, is_admin FROM "user";

# View photos
SELECT id, filename, user_id, created_at FROM photo LIMIT 10;

# Exit
\q
```

### Reset Database

```bash
# Drop all tables
flask db downgrade base

# Re-create tables
flask db upgrade

# Or reset completely
dropdb photovault
createdb photovault
flask db upgrade
```

### Backup Database

```bash
# Backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

## API Testing

### Using cURL

```bash
# Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123!"
  }'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!"
  }'

# Upload photo
curl -X POST http://localhost:5000/api/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/photo.jpg"

# Get photos
curl http://localhost:5000/api/photos \
  -H "Authorization: Bearer <token>"
```

### Using Postman

1. **Import Collection:**
   - Create new collection "PhotoVault API"
   - Set base URL variable: `{{base_url}}` = `http://localhost:5000`

2. **Setup Authentication:**
   - Login to get JWT token
   - Add to collection variables: `{{token}}`
   - Use in headers: `Authorization: Bearer {{token}}`

3. **Test Endpoints:**
   - Auth: Login, Register
   - Photos: Upload, List, Enhance, Colorize
   - Vaults: Create, List, Add Photo

## Debugging

### Backend Debugging

#### Enable Debug Mode

```python
# dev.py
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

#### VS Code Launch Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Flask",
      "type": "python",
      "request": "launch",
      "module": "flask",
      "env": {
        "FLASK_APP": "main.py",
        "FLASK_ENV": "development"
      },
      "args": ["run", "--no-debugger", "--no-reload"],
      "jinja": true
    }
  ]
}
```

#### View Logs

```bash
# Application logs
tail -f logs/photovault.log

# Database queries (enable in config)
app.config['SQLALCHEMY_ECHO'] = True
```

### Mobile Debugging

#### React Native Debugger

```bash
# Install
brew install --cask react-native-debugger

# Start
open "rndebugger://set-debugger-loc?host=localhost&port=8081"
```

#### Chrome DevTools

1. Shake device to open dev menu
2. Select "Debug Remote JS"
3. Chrome will open at `http://localhost:8081/debugger-ui`
4. Open DevTools (F12)

#### Expo Dev Tools

```bash
# Start with dev tools
npx expo start --dev-client

# Access at http://localhost:19002
```

## Testing

### Backend Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest

# With coverage
pytest --cov=photovault --cov-report=html

# View coverage
open htmlcov/index.html
```

#### Example Test

```python
# tests/test_auth.py
def test_login(client):
    response = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'Test123!'
    })
    assert response.status_code == 200

def test_upload_photo(client, auth_token):
    with open('test.jpg', 'rb') as f:
        response = client.post('/api/upload',
            headers={'Authorization': f'Bearer {auth_token}'},
            data={'file': f}
        )
    assert response.status_code == 201
```

### Mobile Tests

```bash
# Install test dependencies
npm install --save-dev jest @testing-library/react-native

# Run tests
npm test

# With coverage
npm test -- --coverage
```

#### Example Test

```javascript
// __tests__/LoginScreen.test.js
import { render, fireEvent } from '@testing-library/react-native';
import LoginScreen from '../src/screens/LoginScreen';

test('login form submits correctly', () => {
  const { getByPlaceholderText, getByText } = render(<LoginScreen />);
  
  fireEvent.changeText(getByPlaceholderText('Email'), 'test@example.com');
  fireEvent.changeText(getByPlaceholderText('Password'), 'password');
  fireEvent.press(getByText('Login'));
  
  // Assert API call made
});
```

## Common Issues & Solutions

### Issue: Database Connection Error

**Error:** `psycopg2.OperationalError: could not connect to server`

**Solution:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql
# or
brew services list

# Check DATABASE_URL is correct
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

### Issue: Module Not Found

**Error:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
# Verify virtual environment is activated
which python

# Reinstall dependencies
pip install -r requirements.txt

# Or in Replit
pip install --force-reinstall -r requirements.txt
```

### Issue: Port Already in Use

**Error:** `Address already in use: 5000`

**Solution:**
```bash
# Find process using port 5000
lsof -ti:5000

# Kill the process
kill -9 $(lsof -ti:5000)

# Or use different port
flask run --port=5001
```

### Issue: Migration Error

**Error:** `Target database is not up to date`

**Solution:**
```bash
# View current revision
flask db current

# View migration history
flask db history

# Downgrade to specific revision
flask db downgrade <revision>

# Upgrade to latest
flask db upgrade
```

### Issue: Expo Tunnel Not Working

**Error:** `Could not create tunnel`

**Solution:**
```bash
# Install ngrok
npm install -g @expo/ngrok

# Clear Expo cache
npx expo start --clear

# Use LAN instead
npx expo start --lan
```

### Issue: Images Not Loading in Mobile App

**Problem:** Photos show placeholder/broken image

**Solution:**
```javascript
// Verify BASE_URL is correct
console.log('API URL:', BASE_URL);

// Check Authorization header
console.log('Token:', await AsyncStorage.getItem('authToken'));

// Test image URL
const imageUrl = `${BASE_URL}${photo.original_url}`;
console.log('Image URL:', imageUrl);
```

## Code Style Guidelines

### Python (PEP 8)

```python
# Good
def upload_photo(user_id, file):
    """Upload photo for user"""
    filename = secure_filename(file.filename)
    return save_file(filename)

# Bad
def uploadPhoto(userId,file):
    filename=file.filename
    return save_file(filename)
```

### JavaScript (ESLint)

```javascript
// Good
const uploadPhoto = async (photo) => {
  const formData = new FormData();
  formData.append('file', photo);
  return await api.post('/api/upload', formData);
};

// Bad
async function uploadPhoto(photo){
  var formData=new FormData()
  formData.append('file',photo)
  return api.post('/api/upload',formData)
}
```

## Git Workflow

### Branching Strategy

```bash
# Main branches
main          # Production code
development   # Development code

# Feature branches
feature/photo-colorization
feature/family-vaults
bugfix/upload-error
hotfix/security-patch
```

### Commit Messages

```bash
# Format: <type>(<scope>): <subject>

# Examples
git commit -m "feat(auth): add JWT authentication"
git commit -m "fix(upload): handle large file uploads"
git commit -m "docs(api): update API documentation"
git commit -m "refactor(gallery): improve performance"
```

### Pull Request Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] CI/CD passing
- [ ] Reviewed by peer

## Next Steps

1. **Explore the codebase:**
   - Review `photovault/` for backend logic
   - Check `StoryKeep-iOS/` for mobile app
   - Read API documentation

2. **Make your first change:**
   - Add a new feature
   - Fix a bug
   - Improve documentation

3. **Test thoroughly:**
   - Run backend tests
   - Run mobile tests
   - Test on real devices

4. **Deploy to staging:**
   - Push to development branch
   - Verify on staging environment
   - Get peer review

## Additional Resources

- **Flask Documentation**: https://flask.palletsprojects.com
- **React Native Docs**: https://reactnative.dev
- **Expo Documentation**: https://docs.expo.dev
- **PostgreSQL Docs**: https://www.postgresql.org/docs
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org

## Getting Help

- Check the [Architecture Guide](./ARCHITECTURE.md)
- Review [API Documentation](./API_DOCUMENTATION.md)
- Read [Security Guide](./SECURITY.md)
- Ask in team chat
- Create GitHub issue
