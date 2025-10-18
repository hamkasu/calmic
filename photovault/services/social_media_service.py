"""
Social Media Integration Service
Handles OAuth authentication and photo sharing to various platforms
"""
import os
import requests
from typing import Optional, Dict, List
from flask import url_for
import secrets
import hashlib
import base64


class SocialMediaService:
    """Service for managing social media integrations"""
    
    SUPPORTED_PLATFORMS = ['instagram', 'facebook', 'twitter', 'pinterest']
    
    def __init__(self):
        self.config = {
            'instagram': {
                'client_id': os.environ.get('INSTAGRAM_CLIENT_ID'),
                'client_secret': os.environ.get('INSTAGRAM_CLIENT_SECRET'),
                'auth_url': 'https://api.instagram.com/oauth/authorize',
                'token_url': 'https://api.instagram.com/oauth/access_token',
                'api_base': 'https://graph.instagram.com/v19.0',
                'scopes': ['instagram_basic', 'instagram_content_publish']
            },
            'facebook': {
                'client_id': os.environ.get('FACEBOOK_APP_ID'),
                'client_secret': os.environ.get('FACEBOOK_APP_SECRET'),
                'auth_url': 'https://www.facebook.com/v19.0/dialog/oauth',
                'token_url': 'https://graph.facebook.com/v19.0/oauth/access_token',
                'api_base': 'https://graph.facebook.com/v19.0',
                'scopes': ['pages_manage_posts', 'pages_read_engagement', 'instagram_basic', 'instagram_content_publish']
            },
            'twitter': {
                'client_id': os.environ.get('TWITTER_CLIENT_ID'),
                'client_secret': os.environ.get('TWITTER_CLIENT_SECRET'),
                'auth_url': 'https://twitter.com/i/oauth2/authorize',
                'token_url': 'https://api.twitter.com/2/oauth2/token',
                'api_base': 'https://api.twitter.com/2',
                'upload_url': 'https://upload.twitter.com/1.1/media/upload.json',
                'scopes': ['tweet.read', 'tweet.write', 'users.read', 'offline.access']
            },
            'pinterest': {
                'client_id': os.environ.get('PINTEREST_APP_ID'),
                'client_secret': os.environ.get('PINTEREST_APP_SECRET'),
                'auth_url': 'https://www.pinterest.com/oauth/',
                'token_url': 'https://api.pinterest.com/v5/oauth/token',
                'api_base': 'https://api.pinterest.com/v5',
                'scopes': ['boards:read', 'pins:read', 'pins:write']
            }
        }
    
    def generate_pkce_pair(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge (RFC 7636)"""
        # Generate code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Generate code challenge (SHA256 hash of verifier)
        challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def get_authorization_url(self, platform: str, redirect_uri: str, state: str) -> tuple[str, str, str]:
        """
        Generate OAuth authorization URL with PKCE
        Returns: (auth_url, state, code_verifier)
        """
        if platform not in self.config:
            raise ValueError(f"Unsupported platform: {platform}")
        
        config = self.config[platform]
        
        if not config['client_id']:
            raise ValueError(f"{platform.title()} client ID not configured")
        
        # Generate PKCE pair
        code_verifier, code_challenge = self.generate_pkce_pair()
        
        # Build authorization URL
        params = {
            'client_id': config['client_id'],
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(config['scopes']),
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        # Platform-specific adjustments
        if platform == 'pinterest':
            params['response_type'] = 'code'
        
        auth_url = f"{config['auth_url']}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        
        return auth_url, state, code_verifier
    
    def exchange_code_for_token(self, platform: str, code: str, redirect_uri: str, code_verifier: str) -> Dict:
        """Exchange authorization code for access token"""
        if platform not in self.config:
            raise ValueError(f"Unsupported platform: {platform}")
        
        config = self.config[platform]
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'code_verifier': code_verifier
        }
        
        response = requests.post(config['token_url'], data=data)
        response.raise_for_status()
        
        return response.json()
    
    def refresh_access_token(self, platform: str, refresh_token: str) -> Dict:
        """Refresh an expired access token"""
        if platform not in self.config:
            raise ValueError(f"Unsupported platform: {platform}")
        
        config = self.config[platform]
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': config['client_id'],
            'client_secret': config['client_secret']
        }
        
        response = requests.post(config['token_url'], data=data)
        response.raise_for_status()
        
        return response.json()
    
    def post_to_instagram(self, user_id: str, access_token: str, image_url: str, caption: str) -> Dict:
        """
        Post photo to Instagram (Business/Creator accounts only)
        Two-step process: create container -> publish
        """
        config = self.config['instagram']
        
        # Step 1: Create media container
        container_url = f"{config['api_base']}/{user_id}/media"
        container_data = {
            'image_url': image_url,
            'caption': caption,
            'access_token': access_token
        }
        
        container_response = requests.post(container_url, data=container_data)
        container_response.raise_for_status()
        container_id = container_response.json()['id']
        
        # Step 2: Publish the container
        publish_url = f"{config['api_base']}/{user_id}/media_publish"
        publish_data = {
            'creation_id': container_id,
            'access_token': access_token
        }
        
        publish_response = requests.post(publish_url, data=publish_data)
        publish_response.raise_for_status()
        
        return publish_response.json()
    
    def post_to_facebook(self, page_id: str, access_token: str, image_url: str, message: str) -> Dict:
        """Post photo to Facebook Page"""
        config = self.config['facebook']
        
        url = f"{config['api_base']}/{page_id}/photos"
        data = {
            'url': image_url,
            'message': message,
            'access_token': access_token
        }
        
        response = requests.post(url, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def post_to_twitter(self, access_token: str, image_path: str, tweet_text: str) -> Dict:
        """
        Post photo to Twitter/X
        Two-step process: upload media -> create tweet
        """
        config = self.config['twitter']
        
        # Step 1: Upload media (using v1.1 API)
        with open(image_path, 'rb') as image_file:
            files = {'media': image_file}
            headers = {'Authorization': f'Bearer {access_token}'}
            
            media_response = requests.post(config['upload_url'], files=files, headers=headers)
            media_response.raise_for_status()
            media_id = media_response.json()['media_id_string']
        
        # Step 2: Create tweet with media (using v2 API)
        tweet_url = f"{config['api_base']}/tweets"
        tweet_data = {
            'text': tweet_text,
            'media': {
                'media_ids': [media_id]
            }
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        tweet_response = requests.post(tweet_url, json=tweet_data, headers=headers)
        tweet_response.raise_for_status()
        
        return tweet_response.json()
    
    def post_to_pinterest(self, access_token: str, board_id: str, image_url: str, title: str, description: str, link: str = None) -> Dict:
        """Create a Pin on Pinterest"""
        config = self.config['pinterest']
        
        url = f"{config['api_base']}/pins"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'board_id': board_id,
            'title': title,
            'description': description,
            'media_source': {
                'source_type': 'image_url',
                'url': image_url
            }
        }
        
        if link:
            data['link'] = link
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def is_platform_configured(self, platform: str) -> bool:
        """Check if a platform has required credentials configured"""
        if platform not in self.config:
            return False
        
        config = self.config[platform]
        return bool(config.get('client_id') and config.get('client_secret'))
    
    def get_available_platforms(self) -> List[str]:
        """Get list of platforms with configured credentials"""
        return [platform for platform in self.SUPPORTED_PLATFORMS if self.is_platform_configured(platform)]
