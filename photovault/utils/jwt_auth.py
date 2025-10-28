"""
JWT Authentication utility for mobile API endpoints
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
"""
from functools import wraps
from flask import request, jsonify, current_app, abort
from flask_login import current_user as flask_current_user, login_required
import jwt
from photovault.models import User

def token_required(f):
    """
    Decorator for JWT token authentication
    Extracts and verifies JWT token from Authorization header
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Invalid Authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Authorization token is missing'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            current_app.logger.error(f"JWT verification error: {str(e)}")
            return jsonify({'error': 'Token verification failed'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def hybrid_auth(f):
    """
    Decorator that supports both session-based and JWT authentication.
    Checks for JWT token first, falls back to session authentication.
    Used for routes that need to work with both web and mobile clients.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        authenticated_user = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
                data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
                authenticated_user = User.query.get(data['user_id'])
            except (IndexError, jwt.ExpiredSignatureError, jwt.InvalidTokenError, Exception) as e:
                current_app.logger.debug(f"JWT auth failed, trying session: {str(e)}")
                pass
        
        if not authenticated_user and flask_current_user.is_authenticated:
            authenticated_user = flask_current_user
        
        if not authenticated_user:
            abort(401)
        
        return f(authenticated_user, *args, **kwargs)
    
    return decorated
