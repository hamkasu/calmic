"""
Push Notification Utility for Expo Push Notifications
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
"""
import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = 'https://exp.host/--/api/v2/push/send'

def send_push_notification(
    push_tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict] = None,
    priority: str = 'high'
) -> Dict:
    """
    Send push notification via Expo Push Notification Service
    
    Args:
        push_tokens: List of Expo push tokens
        title: Notification title
        body: Notification body text
        data: Optional data payload
        priority: 'default', 'normal', or 'high'
    
    Returns:
        Response dict with success/failure info
    """
    if not push_tokens:
        logger.warning("No push tokens provided")
        return {'success': False, 'error': 'No push tokens'}
    
    # Filter valid Expo tokens
    valid_tokens = [
        token for token in push_tokens
        if token and (token.startswith('ExponentPushToken[') or token.startswith('ExpoPushToken['))
    ]
    
    if not valid_tokens:
        logger.warning("No valid Expo push tokens")
        return {'success': False, 'error': 'No valid push tokens'}
    
    # Build notification messages
    messages = []
    for token in valid_tokens:
        message = {
            'to': token,
            'title': title,
            'body': body,
            'sound': 'default',
            'priority': priority,
            'channelId': 'default',
        }
        
        if data:
            message['data'] = data
        
        messages.append(message)
    
    try:
        # Send to Expo Push Notification Service
        response = requests.post(
            EXPO_PUSH_URL,
            json=messages,
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            timeout=10
        )
        
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"📱 Sent push notifications to {len(valid_tokens)} devices")
        
        return {
            'success': True,
            'sent_count': len(valid_tokens),
            'response': result
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Push notification error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def notify_vault_members(vault_id: int, title: str, body: str, exclude_user_id: Optional[int] = None):
    """
    Send push notification to all members of a family vault
    
    Args:
        vault_id: Family vault ID
        title: Notification title
        body: Notification body
        exclude_user_id: Optional user ID to exclude (e.g., the person who triggered the notification)
    
    Returns:
        Response dict with success/failure info
    """
    from photovault.models import FamilyMember, User
    
    try:
        # Get all members of the vault
        members = FamilyMember.query.filter_by(vault_id=vault_id).all()
        
        if not members:
            logger.warning(f"No members found for vault {vault_id}")
            return {'success': False, 'error': 'No vault members'}
        
        # Get push tokens for all members (excluding the triggering user)
        push_tokens = []
        for member in members:
            if exclude_user_id and member.user_id == exclude_user_id:
                continue
            
            user = User.query.get(member.user_id)
            if user and user.expo_push_token:
                push_tokens.append(user.expo_push_token)
        
        if not push_tokens:
            logger.info(f"No push tokens available for vault {vault_id} members")
            return {'success': False, 'error': 'No push tokens available'}
        
        # Send notification
        return send_push_notification(
            push_tokens=push_tokens,
            title=title,
            body=body,
            data={
                'type': 'vault_update',
                'vault_id': vault_id
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error notifying vault members: {str(e)}")
        return {'success': False, 'error': str(e)}
