"""
PhotoVault Development Server
Runs Flask development server on 0.0.0.0:5000 for Replit environment
"""
import os

# Set development environment
os.environ['FLASK_CONFIG'] = 'development'
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = 'True'

# Import and run the app
from main import app

if __name__ == '__main__':
    port = 5000
    print(f"Starting PhotoVault development server on 0.0.0.0:{port}")
    print(f"Environment: development")
    print(f"Debug mode: enabled")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
        threaded=True
    )
