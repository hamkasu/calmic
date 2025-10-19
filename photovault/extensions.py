"""
PhotoVault Extensions
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

Centralized extension initialization to avoid instance duplication.
"""

import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize extensions as singletons
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# Flask-Limiter with configurable backend (Redis for production, memory for dev)
# Set RATELIMIT_STORAGE_URL env var for production (e.g., redis://localhost:6379)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URL", "memory://")
)