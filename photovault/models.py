"""
PhotoVault Database Models
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
"""
# photovault/models.py

from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from photovault.extensions import db

class User(UserMixin, db.Model):
    """User model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)  # ← ADD THIS LINE
    is_admin = db.Column(db.Boolean, default=False)
    is_superuser = db.Column(db.Boolean, default=False)
    profile_picture = db.Column(db.String(500))  # Profile picture filename
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    photos = db.relationship('Photo', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Photo(db.Model):
    """Photo model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))
    edited_filename = db.Column(db.String(255))  # For edited versions
    edited_path = db.Column(db.String(500))  # For edited versions
    file_size = db.Column(db.Integer)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    upload_source = db.Column(db.String(50), default='file')  # 'file' or 'camera'

    # EXIF Metadata fields
    date_taken = db.Column('photo_date', db.DateTime)  # Original date photo was taken
    camera_make = db.Column(db.String(100))  # Camera manufacturer
    camera_model = db.Column(db.String(100))  # Camera model
    
    # Camera settings
    iso = db.Column(db.Integer)  # ISO sensitivity
    aperture = db.Column(db.Float)  # f-stop value
    shutter_speed = db.Column(db.String(50))  # Exposure time
    focal_length = db.Column(db.Float)  # Focal length in mm
    flash_used = db.Column(db.Boolean)  # Whether flash was fired
    
    # GPS coordinates
    gps_latitude = db.Column(db.Float)  # GPS latitude in decimal degrees
    gps_longitude = db.Column(db.Float)  # GPS longitude in decimal degrees
    gps_altitude = db.Column(db.Float)  # GPS altitude in meters
    location_name = db.Column(db.String(255))  # Human-readable location
    
    # Image properties
    orientation = db.Column(db.Integer)  # EXIF orientation value
    color_space = db.Column(db.String(50))  # Color space (sRGB, Adobe RGB, etc.)
    
    # Enhancement settings
    auto_enhanced = db.Column(db.Boolean, default=False)  # Whether auto-enhancement was applied
    enhancement_settings = db.Column(db.Text)  # JSON of enhancement parameters applied
    processing_notes = db.Column(db.Text)  # Notes about processing applied to this photo
    
    # User-added metadata
    description = db.Column(db.Text)  # User description of the photo
    tags = db.Column(db.String(500))  # Comma-separated tags
    event_name = db.Column(db.String(255))  # Event or occasion name
    estimated_year = db.Column(db.Integer)  # Estimated year if date_taken unavailable
    
    # AI-generated metadata
    ai_metadata = db.Column(db.Text)  # JSON storage for AI-generated tags, poses, composition analysis

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Photo {self.original_name}>'

class Person(db.Model):
    """Person model for photo tagging"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(50))
    relationship = db.Column(db.String(50))
    birth_year = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    photo_tags = db.relationship('PhotoTag', backref='person', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def photo_count(self):
        """Count of photos this person is tagged in"""
        return self.photo_tags.count()
    
    def __repr__(self):
        return f'<Person {self.name}>'

class PhotoTag(db.Model):
    """Photo tagging model"""
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)
    manually_tagged = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    photo = db.relationship('Photo', backref='tags')
    
    def __repr__(self):
        return f'<PhotoTag {self.photo_id}-{self.person_id}>'


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
    user = db.relationship('User', backref='voice_memos')
    
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
    user = db.relationship('User', backref='photo_comments')
    
    def __repr__(self):
        return f'<PhotoComment {self.id} for Photo {self.photo_id}>'


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
    storage_gb = db.Column(db.Numeric(10, 2), nullable=False)  # Storage limit in GB (supports decimals)
    max_photos = db.Column(db.Integer)  # Max photos (null = unlimited)
    max_family_vaults = db.Column(db.Integer, default=0)  # Number of family vaults allowed
    
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
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='subscriptions')
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
    user = db.relationship('User', backref='invoices')
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
    user = db.relationship('User', backref='payment_history')
    
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
    metadata = db.Column(db.JSON)  # Store platform-specific data (e.g., page IDs, board IDs)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='social_media_connections')
    
    # Composite unique constraint - one connection per user per platform
    __table_args__ = (
        db.UniqueConstraint('user_id', 'platform', name='_user_platform_uc'),
    )
    
    def __repr__(self):
        return f'<SocialMediaConnection {self.user_id} - {self.platform}>'

