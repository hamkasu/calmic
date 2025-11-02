"""
PhotoVault Database Models
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

Complete models for User, Photo, Album, Person, and PhotoPerson management
"""
from datetime import datetime, timedelta
import secrets
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from photovault.extensions import db

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Admin and superuser fields
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_superuser = db.Column(db.Boolean, default=False, nullable=False)
    
    # Billing
    stripe_customer_id = db.Column(db.String(255), unique=True)
    
    # Push notifications
    expo_push_token = db.Column(db.String(255), unique=True)
    
    # Relationships
    photos = db.relationship('Photo', backref='user', lazy=True, cascade='all, delete-orphan', passive_deletes=True)
    albums = db.relationship('Album', backref='user', lazy=True, cascade='all, delete-orphan', passive_deletes=True)
    people = db.relationship('Person', backref='user', lazy=True, cascade='all, delete-orphan', passive_deletes=True)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Album(db.Model):
    """Album model for organizing photos"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Time period fields for organizing old photos
    date_start = db.Column(db.Date)  # Start date for photos in this album
    date_end = db.Column(db.Date)    # End date for photos in this album
    time_period = db.Column(db.String(100))  # e.g., "Summer 1987", "Early 1960s"
    location = db.Column(db.String(200))     # e.g., "Grandma's house", "Family farm"
    event_type = db.Column(db.String(100))   # e.g., "Wedding", "Christmas", "Vacation"
    
    # Relationships
    photos = db.relationship('Photo', backref='album', lazy=True)
    
    def __repr__(self):
        return f'<Album {self.name}>'
    
    @property
    def photo_count(self):
        """Return number of photos in album"""
        return len(self.photos)

class Person(db.Model):
    """Person model for tagging people in photos"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    nickname = db.Column(db.String(100))
    birth_year = db.Column(db.Integer)
    relationship = db.Column(db.String(100))  # e.g., "Mother", "Brother", "Friend"
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Back reference to association object
    photo_people_records = db.relationship('PhotoPerson', back_populates='person', overlaps="photos")
    
    def __repr__(self):
        return f'<Person {self.name}>'

class Photo(db.Model):
    """Photo model for storing photo information"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))
    grid_thumbnail_path = db.Column(db.String(500))  # Small 200x200 thumbnail for gallery grid
    blurhash = db.Column(db.String(100))  # Blurhash for instant placeholder preview
    file_size = db.Column(db.Integer)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    upload_source = db.Column(db.String(50), default='file')  # 'file' or 'camera'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=True)
    
    # Enhanced fields for old photograph digitization
    photo_date = db.Column(db.Date)           # Best guess at actual photo date
    date_text = db.Column(db.String(100))     # Text like "Summer 1987", "Christmas 1985"
    date_circa = db.Column(db.Boolean, nullable=False, default=False)  # True if date is approximate
    
    # Location and context
    location_text = db.Column(db.String(200))  # "Grandma's house", "School playground"
    occasion = db.Column(db.String(200))       # "Wedding day", "Birthday party"
    
    # Physical photo condition and source
    condition = db.Column(db.String(50))       # "Excellent", "Faded", "Torn", "Stained"
    photo_source = db.Column(db.String(100))   # "Family album", "Shoebox", "Frame"
    back_text = db.Column(db.Text)             # Text written on back of photo
    
    # Processing metadata
    needs_restoration = db.Column(db.Boolean, nullable=False, default=False)
    auto_enhanced = db.Column(db.Boolean, nullable=False, default=False)
    processing_notes = db.Column(db.Text)
    edited_filename = db.Column(db.String(255))  # Stores the filename of the edited image
    edited_path = db.Column(db.String(500))  # Stores the path of the edited image
    enhancement_metadata = db.Column(db.JSON)  # Stores enhancement details (method, AI guidance, etc.)
    
    # Front/back pairing for photos with writing on back
    paired_photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'))
    is_back_side = db.Column(db.Boolean, nullable=False, default=False)
    
    # Enhanced version tracking - links enhanced photos to their original
    original_photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=True)
    is_enhanced_version = db.Column(db.Boolean, nullable=False, default=False)
    enhancement_type = db.Column(db.String(50))  # 'colorized', 'sharpened', 'auto_enhanced', etc.
    
    # Many-to-many relationship with people through PhotoPerson association
    people = db.relationship('Person', secondary='photo_people', lazy='subquery',
                           backref=db.backref('photos', lazy=True, overlaps="photo_people_records"), 
                           overlaps="photo_people_records")
    
    # Back reference to association object
    photo_people_records = db.relationship('PhotoPerson', back_populates='photo', overlaps="people,photos")
    
    def __repr__(self):
        return f'<Photo {self.filename}>'
    
    @property
    def file_size_mb(self):
        """Return file size in MB"""
        if self.file_size:
            return round(self.file_size / 1024 / 1024, 2)
        return 0
    
    @property
    def dimensions(self):
        """Return image dimensions as string"""
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return "Unknown"

class PhotoPerson(db.Model):
    """Association model for tagging people in photos with face detection metadata"""
    __tablename__ = 'photo_people'
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Face detection metadata
    confidence = db.Column(db.Float)  # Detection confidence (0.0-1.0)
    face_box_x = db.Column(db.Integer)  # Bounding box coordinates
    face_box_y = db.Column(db.Integer)
    face_box_width = db.Column(db.Integer)
    face_box_height = db.Column(db.Integer)
    manually_tagged = db.Column(db.Boolean, nullable=False, default=False)  # True if manually tagged vs auto-detected
    verified = db.Column(db.Boolean, nullable=False, default=False)  # True if user verified the detection
    notes = db.Column(db.String(255))  # Optional notes about the identification
    
    # Relationships
    photo = db.relationship('Photo', back_populates='photo_people_records', overlaps="people,photos")
    person = db.relationship('Person', back_populates='photo_people_records', overlaps="people,photos")
    
    def __repr__(self):
        return f'<PhotoPerson {self.photo_id}-{self.person_id}>'

class PasswordResetToken(db.Model):
    """Password reset token model for secure password resets"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('reset_tokens', cascade='all, delete-orphan', passive_deletes=True))
    
    def __init__(self, user_id):
        """Initialize password reset token"""
        self.user_id = user_id
        self.token = secrets.token_urlsafe(32)
        self.expires_at = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
    
    def is_valid(self):
        """Check if token is still valid and not used"""
        return not self.used and datetime.utcnow() < self.expires_at
    
    def mark_as_used(self):
        """Mark token as used"""
        self.used = True
    
    @staticmethod
    def clean_expired_tokens():
        """Remove expired tokens from database"""
        expired_tokens = PasswordResetToken.query.filter(
            PasswordResetToken.expires_at < datetime.utcnow()
        ).all()
        
        for token in expired_tokens:
            db.session.delete(token)
        db.session.commit()
        
        return len(expired_tokens)
    
    def __repr__(self):
        return f'<PasswordResetToken {self.token[:8]}...>'

class VoiceMemo(db.Model):
    """Voice memo model for audio recordings attached to photos"""
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Audio file information
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # Size in bytes
    mime_type = db.Column(db.String(100))  # audio/webm, audio/wav, etc.
    duration = db.Column(db.Float)  # Duration in seconds
    
    # User metadata
    title = db.Column(db.String(200))  # Optional title for the voice memo
    transcript = db.Column(db.Text)  # Optional transcription of the memo
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    photo = db.relationship('Photo', backref='voice_memos')
    user = db.relationship('User', backref=db.backref('voice_memos', cascade='all, delete-orphan', passive_deletes=True))
    
    @property
    def file_size_mb(self):
        """Return file size in MB"""
        if self.file_size:
            return round(self.file_size / 1024 / 1024, 2)
        return 0
    
    @property
    def duration_formatted(self):
        """Return duration in MM:SS format"""
        if self.duration:
            minutes = int(self.duration // 60)
            seconds = int(self.duration % 60)
            return f"{minutes:02d}:{seconds:02d}"
        return "00:00"
    
    def __repr__(self):
        return f'<VoiceMemo {self.filename} for Photo {self.photo_id}>'

class PhotoComment(db.Model):
    """Photo comment/annotation model for text notes attached to photos"""
    __tablename__ = 'photo_comment'
    
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Comment content
    comment_text = db.Column(db.Text, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    photo = db.relationship('Photo', backref='comments')
    user = db.relationship('User', backref=db.backref('photo_comments', cascade='all, delete-orphan', passive_deletes=True))
    
    def __repr__(self):
        return f'<PhotoComment {self.id} for Photo {self.photo_id}>'

class FamilyVault(db.Model):
    """Family vault model for shared photo collections"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vault_code = db.Column(db.String(20), unique=True, nullable=False)  # Unique code for sharing
    is_public = db.Column(db.Boolean, default=False)  # Whether discoverable by vault code
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref=db.backref('created_vaults', cascade='all, delete-orphan', passive_deletes=True))
    members = db.relationship('FamilyMember', backref='vault', lazy='dynamic', cascade='all, delete-orphan')
    invitations = db.relationship('VaultInvitation', backref='vault', lazy='dynamic', cascade='all, delete-orphan')
    shared_photos = db.relationship('VaultPhoto', backref='vault', lazy='dynamic', cascade='all, delete-orphan')
    stories = db.relationship('Story', backref='vault', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def member_count(self):
        """Count of active members in this vault"""
        return self.members.filter_by(status='active').count()
    
    @property
    def photo_count(self):
        """Count of photos in this vault"""
        return self.shared_photos.count()
    
    def get_member_role(self, user_id):
        """Get the role of a user in this vault"""
        member = self.members.filter_by(user_id=user_id, status='active').first()
        return member.role if member else None
    
    def has_member(self, user_id):
        """Check if user is an active member of this vault"""
        return self.members.filter_by(user_id=user_id, status='active').first() is not None
    
    def __repr__(self):
        return f'<FamilyVault {self.name}>'

class FamilyMember(db.Model):
    """Family member model for vault access control"""
    id = db.Column(db.Integer, primary_key=True)
    vault_id = db.Column(db.Integer, db.ForeignKey('family_vault.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')  # 'admin', 'contributor', 'member'
    status = db.Column(db.String(20), nullable=False, default='active')  # 'active', 'inactive', 'removed'
    invited_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('vault_memberships', cascade='all, delete-orphan', passive_deletes=True))
    inviter = db.relationship('User', foreign_keys=[invited_by], passive_deletes=True)
    
    def can_manage_vault(self):
        """Check if member can manage vault settings"""
        return self.role in ['admin']
    
    def can_add_content(self):
        """Check if member can add photos and stories"""
        return self.role in ['admin', 'contributor']
    
    def can_view_content(self):
        """Check if member can view vault content"""
        return self.status == 'active'
    
    def __repr__(self):
        return f'<FamilyMember {self.user.username if self.user else "Unknown"} in {self.vault.name if self.vault else "Unknown"}>'

class VaultInvitation(db.Model):
    """Vault invitation model for inviting family members"""
    id = db.Column(db.Integer, primary_key=True)
    vault_id = db.Column(db.Integer, db.ForeignKey('family_vault.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    invited_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'accepted', 'declined', 'expired'
    invitation_token = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime)
    last_sent_at = db.Column(db.DateTime)
    
    # Relationships
    inviter = db.relationship('User', backref=db.backref('sent_invitations', cascade='all, delete-orphan', passive_deletes=True))
    
    @property
    def is_expired(self):
        """Check if invitation has expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_pending(self):
        """Check if invitation is still pending"""
        return self.status == 'pending' and not self.is_expired
    
    def can_resend(self, min_seconds=60):
        """Check if invitation can be resent (rate limiting)"""
        if not self.is_pending:
            return False
        if not self.last_sent_at:
            return True
        time_since_last = datetime.utcnow() - self.last_sent_at
        return time_since_last.total_seconds() >= min_seconds
    
    def mark_as_sent(self):
        """Update last_sent_at timestamp"""
        self.last_sent_at = datetime.utcnow()
    
    def accept(self, user):
        """Accept the invitation and create family member"""
        if not self.is_pending:
            return False
            
        # Create family member
        member = FamilyMember(
            vault_id=self.vault_id,
            user_id=user.id,
            role=self.role,
            invited_by=self.invited_by
        )
        db.session.add(member)
        
        # Update invitation status
        self.status = 'accepted'
        self.accepted_at = datetime.utcnow()
        
        return True
    
    def __repr__(self):
        return f'<VaultInvitation {self.email} to {self.vault.name if self.vault else "Unknown"}>'

class VaultPhoto(db.Model):
    """Association model for photos shared in family vaults"""
    id = db.Column(db.Integer, primary_key=True)
    vault_id = db.Column(db.Integer, db.ForeignKey('family_vault.id'), nullable=False)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)
    shared_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    caption = db.Column(db.Text)  # Caption specific to this vault
    shared_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    photo = db.relationship('Photo', backref='vault_shares')
    sharer = db.relationship('User', backref=db.backref('shared_photos', cascade='all, delete-orphan', passive_deletes=True))
    
    def __repr__(self):
        return f'<VaultPhoto {self.photo.original_name if self.photo else "Unknown"} in {self.vault.name if self.vault else "Unknown"}>'

class Story(db.Model):
    """Story model for family narratives and memories"""
    id = db.Column(db.Integer, primary_key=True)
    vault_id = db.Column(db.Integer, db.ForeignKey('family_vault.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    story_type = db.Column(db.String(50), default='memory')  # 'memory', 'biography', 'event', 'tradition'
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref=db.backref('authored_stories', cascade='all, delete-orphan', passive_deletes=True))
    photo_attachments = db.relationship('StoryPhoto', backref='story', lazy='dynamic', cascade='all, delete-orphan')
    person_mentions = db.relationship('StoryPerson', backref='story', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def word_count(self):
        """Approximate word count of the story"""
        return len(self.content.split()) if self.content else 0
    
    def __repr__(self):
        return f'<Story "{self.title}" by {self.author.username if self.author else "Unknown"}>'

class StoryPhoto(db.Model):
    """Association model for photos attached to stories"""
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)
    caption = db.Column(db.Text)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    photo = db.relationship('Photo', backref='story_attachments')
    
    def __repr__(self):
        return f'<StoryPhoto {self.photo.original_name if self.photo else "Unknown"} in Story {self.story_id}>'

class StoryPerson(db.Model):
    """Association model for people mentioned in stories"""
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)
    role_in_story = db.Column(db.String(100))  # Their role or significance in this story
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    person = db.relationship('Person', backref='story_mentions')
    
    def __repr__(self):
        return f'<StoryPerson {self.person.name if self.person else "Unknown"} in Story {self.story_id}>'


# ============================================================================
# BILLING MODELS - Malaysian Subscription System with SST Tax
# ============================================================================

class SubscriptionPlan(db.Model):
    """Subscription plan model for Malaysian market with SST"""
    __tablename__ = 'subscription_plan'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # Basic, Pro, Premium
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Pricing in Malaysian Ringgit (MYR)
    price_myr = db.Column(db.Numeric(10, 2), nullable=False)  # Base price before tax
    sst_rate = db.Column(db.Numeric(5, 2), default=6.00)  # 6% Service Tax (SST)
    
    # Features and limits
    storage_gb = db.Column(db.Numeric(10, 2), nullable=False)  # Storage limit in GB (allows decimals like 0.5)
    max_photos = db.Column(db.Integer)  # Max photos (null = unlimited)
    max_family_vaults = db.Column(db.Integer, default=0)  # Number of family vaults allowed
    ai_enhancement_quota = db.Column(db.Integer, default=0)  # Monthly AI enhancement quota (colorization/restoration)
    
    # Feature flags
    face_detection = db.Column(db.Boolean, default=False)
    photo_enhancement = db.Column(db.Boolean, default=False)
    smart_tagging = db.Column(db.Boolean, default=False)
    social_media_integration = db.Column(db.Boolean, default=False)
    api_access = db.Column(db.Boolean, default=False)
    priority_support = db.Column(db.Boolean, default=False)
    
    # Stripe integration
    stripe_price_id = db.Column(db.String(255))  # Stripe Price ID for subscriptions
    stripe_product_id = db.Column(db.String(255))  # Stripe Product ID
    
    # Billing cycle
    billing_period = db.Column(db.String(20), default='monthly')  # monthly, yearly
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = db.relationship('UserSubscription', backref='plan', lazy='dynamic')
    
    @property
    def total_price_myr(self):
        """Calculate total price including SST"""
        if self.price_myr and self.sst_rate:
            return float(self.price_myr) * (1 + float(self.sst_rate) / 100)
        return float(self.price_myr) if self.price_myr else 0
    
    @property
    def sst_amount(self):
        """Calculate SST tax amount"""
        if self.price_myr and self.sst_rate:
            return float(self.price_myr) * (float(self.sst_rate) / 100)
        return 0
    
    def __repr__(self):
        return f'<SubscriptionPlan {self.name}>'


class UserSubscription(db.Model):
    """User subscription model tracking active subscriptions"""
    __tablename__ = 'user_subscription'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plan.id'), nullable=False)
    
    # Subscription status
    status = db.Column(db.String(20), default='active')  # active, canceled, expired, trial
    
    # Stripe subscription details
    stripe_subscription_id = db.Column(db.String(255), unique=True)
    stripe_customer_id = db.Column(db.String(255))
    
    # Dates
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    canceled_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    trial_end = db.Column(db.DateTime)
    
    # Billing
    last_payment_date = db.Column(db.DateTime)
    next_billing_date = db.Column(db.DateTime)
    
    # Metadata
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    cancel_reason = db.Column(db.Text)
    
    # AI Enhancement tracking
    ai_enhancements_used = db.Column(db.Integer, default=0)  # Current month's usage
    ai_enhancements_reset_date = db.Column(db.DateTime)  # When to reset the counter
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('user_subscriptions', cascade='all, delete-orphan', passive_deletes=True))
    invoices = db.relationship('Invoice', backref='subscription', lazy='dynamic')
    
    @property
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status == 'active' and (
            not self.current_period_end or self.current_period_end > datetime.utcnow()
        )
    
    @property
    def days_remaining(self):
        """Days remaining in current billing period"""
        if self.current_period_end:
            delta = self.current_period_end - datetime.utcnow()
            return max(0, delta.days)
        return 0
    
    def __repr__(self):
        return f'<UserSubscription {self.user_id}:{self.plan_id}>'


class Invoice(db.Model):
    """Invoice model for SST-compliant billing records"""
    __tablename__ = 'invoice'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)  # INV-2025-001
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('user_subscription.id'))
    
    # Billing details
    billing_name = db.Column(db.String(255))
    billing_email = db.Column(db.String(255))
    billing_address = db.Column(db.Text)
    
    # Malaysian business details (optional)
    company_name = db.Column(db.String(255))
    business_registration_number = db.Column(db.String(100))  # SSM registration
    sst_registration_number = db.Column(db.String(100))  # SST number if applicable
    
    # Invoice amounts in MYR
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)  # Before tax
    sst_rate = db.Column(db.Numeric(5, 2), default=6.00)  # SST percentage
    sst_amount = db.Column(db.Numeric(10, 2), nullable=False)  # Tax amount
    total = db.Column(db.Numeric(10, 2), nullable=False)  # Total including tax
    
    currency = db.Column(db.String(3), default='MYR')
    
    # Invoice details
    description = db.Column(db.Text)
    billing_period_start = db.Column(db.Date)
    billing_period_end = db.Column(db.Date)
    
    # Status
    status = db.Column(db.String(20), default='draft')  # draft, issued, paid, void
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    paid_date = db.Column(db.DateTime)
    
    # Payment tracking
    stripe_invoice_id = db.Column(db.String(255))
    stripe_payment_intent_id = db.Column(db.String(255))
    payment_method = db.Column(db.String(50))  # card, fpx, e-wallet
    
    # E-invoice compliance fields (for future MyInvois integration)
    einvoice_uuid = db.Column(db.String(255))  # MyInvois UUID
    einvoice_qr_code = db.Column(db.Text)  # QR code data
    einvoice_validation_date = db.Column(db.DateTime)
    
    # Metadata
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('invoices', cascade='all, delete-orphan', passive_deletes=True))
    payment_records = db.relationship('PaymentHistory', backref='invoice', lazy='dynamic')
    
    @property
    def is_paid(self):
        """Check if invoice has been paid"""
        return self.status == 'paid'
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        if self.status != 'issued' or not self.due_date:
            return False
        return datetime.utcnow() > self.due_date
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'


class PaymentHistory(db.Model):
    """Payment history model for transaction records"""
    __tablename__ = 'payment_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'))
    
    # Payment details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='MYR')
    
    # Stripe details
    stripe_payment_intent_id = db.Column(db.String(255), unique=True)
    stripe_charge_id = db.Column(db.String(255))
    
    # Payment method
    payment_method = db.Column(db.String(50))  # card, fpx, grabpay, tng, boost
    card_brand = db.Column(db.String(20))  # visa, mastercard, amex
    card_last4 = db.Column(db.String(4))  # Last 4 digits
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, succeeded, failed, refunded
    
    # Dates
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    refunded_date = db.Column(db.DateTime)
    
    # Additional info
    description = db.Column(db.Text)
    failure_reason = db.Column(db.Text)
    receipt_url = db.Column(db.String(500))  # Stripe receipt URL
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('payment_history', cascade='all, delete-orphan', passive_deletes=True))
    
    @property
    def is_successful(self):
        """Check if payment was successful"""
        return self.status == 'succeeded'
    
    def __repr__(self):
        return f'<PaymentHistory {self.id} - {self.amount} {self.currency}>'


class SocialMediaConnection(db.Model):
    """Social media account connection model"""
    __tablename__ = 'social_media_connection'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Platform details
    platform = db.Column(db.String(50), nullable=False)  # instagram, facebook, twitter, pinterest
    platform_user_id = db.Column(db.String(255))  # Platform-specific user ID
    platform_username = db.Column(db.String(255))  # Platform username/handle
    
    # OAuth tokens
    access_token = db.Column(db.Text, nullable=False)  # OAuth access token
    refresh_token = db.Column(db.Text)  # OAuth refresh token (if available)
    token_expires_at = db.Column(db.DateTime)  # Token expiration time
    
    # Connection status
    is_active = db.Column(db.Boolean, default=True)
    last_used_at = db.Column(db.DateTime)  # Last time this connection was used
    
    # Platform-specific metadata
    connection_data = db.Column(db.JSON)  # Store platform-specific data (e.g., page IDs, board IDs)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('social_media_connections', cascade='all, delete-orphan', passive_deletes=True))
    
    # Composite unique constraint - one connection per user per platform
    __table_args__ = (
        db.UniqueConstraint('user_id', 'platform', name='_user_platform_uc'),
    )
    
    def __repr__(self):
        return f'<SocialMediaConnection {self.user_id} - {self.platform}>'


# ============================================================================
# SECURITY & AUTH MODELS
# ============================================================================

class LoginAttempt(db.Model):
    """Track login attempts for rate limiting and security monitoring"""
    __tablename__ = 'login_attempt'
    
    id = db.Column(db.Integer, primary_key=True)
    username_or_email = db.Column(db.String(255), nullable=False, index=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    success = db.Column(db.Boolean, default=False, nullable=False)
    failure_reason = db.Column(db.String(255))
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f'<LoginAttempt {self.username_or_email} at {self.attempted_at}>'


class AccountLockout(db.Model):
    """Track account lockouts due to failed login attempts"""
    __tablename__ = 'account_lockout'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    locked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    unlock_at = db.Column(db.DateTime, nullable=False, index=True)
    reason = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    unlocked_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref=db.backref('lockouts', cascade='all, delete-orphan', passive_deletes=True))
    
    def __repr__(self):
        return f'<AccountLockout user_id={self.user_id} until {self.unlock_at}>'


class RefreshToken(db.Model):
    """Store refresh tokens for token refresh mechanism"""
    __tablename__ = 'refresh_token'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    token = db.Column(db.String(500), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = db.Column(db.DateTime)
    device_info = db.Column(db.String(500))
    ip_address = db.Column(db.String(45))
    
    user = db.relationship('User', backref=db.backref('refresh_tokens', cascade='all, delete-orphan', passive_deletes=True))
    
    @property
    def is_valid(self):
        """Check if token is still valid"""
        if self.revoked_at:
            return False
        return datetime.utcnow() < self.expires_at
    
    def revoke(self):
        """Revoke this token"""
        self.revoked_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<RefreshToken user_id={self.user_id}>'


class MFASecret(db.Model):
    """Store MFA/2FA TOTP secrets for users"""
    __tablename__ = 'mfa_secret'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True, index=True)
    secret = db.Column(db.String(32), nullable=False)
    is_enabled = db.Column(db.Boolean, default=False, nullable=False)
    backup_codes = db.Column(db.Text)
    enabled_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref=db.backref('mfa_secret', uselist=False, cascade='all, delete-orphan', passive_deletes=True))
    
    def __repr__(self):
        return f'<MFASecret user_id={self.user_id} enabled={self.is_enabled}>'


class OAuthProvider(db.Model):
    """OAuth provider connections for social login (Google, Apple, etc.)"""
    __tablename__ = 'oauth_provider'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    provider = db.Column(db.String(50), nullable=False)
    provider_user_id = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    display_name = db.Column(db.String(255))
    profile_picture_url = db.Column(db.String(500))
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref=db.backref('oauth_providers', cascade='all, delete-orphan', passive_deletes=True))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'provider', name='_user_oauth_provider_uc'),
        db.Index('idx_provider_user_id', 'provider', 'provider_user_id'),
    )
    
    def __repr__(self):
        return f'<OAuthProvider {self.provider} for user_id={self.user_id}>'


class SecurityLog(db.Model):
    """Security event logging for auditing and monitoring"""
    __tablename__ = 'security_log'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    event_type = db.Column(db.String(100), nullable=False, index=True)
    severity = db.Column(db.String(20), nullable=False, index=True)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    event_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    user = db.relationship('User', backref=db.backref('security_logs', cascade='all, delete-orphan', passive_deletes=True))
    
    def __repr__(self):
        return f'<SecurityLog {self.event_type} at {self.created_at}>'


class AIEnhancementLog(db.Model):
    """Track AI enhancement usage for quota management"""
    __tablename__ = 'ai_enhancement_log'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=True)
    enhancement_type = db.Column(db.String(50), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    user = db.relationship('User', backref=db.backref('ai_enhancements', cascade='all, delete-orphan', passive_deletes=True))
    photo = db.relationship('Photo', backref=db.backref('ai_enhancement_logs', cascade='all, delete-orphan', passive_deletes=True))
    
    __table_args__ = (
        db.Index('idx_user_created', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f'<AIEnhancementLog user_id={self.user_id} type={self.enhancement_type}>'
