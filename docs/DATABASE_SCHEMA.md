# Database Schema Documentation

## Overview

PhotoVault uses PostgreSQL with SQLAlchemy 2.0 ORM. The database is designed to support user management, photo storage, family sharing, subscriptions, and AI-enhanced features.

## Entity Relationship Diagram

```
┌─────────────┐
│    User     │
└─────────────┘
      │ 1
      │
      │ *
┌─────────────┐       ┌──────────────┐
│   Photo     │───────│  VoiceMemo   │
└─────────────┘   *   └──────────────┘
      │ *
      │
      │ *
┌─────────────┐       ┌──────────────┐
│ FamilyVault │───────│ VaultPhoto   │
└─────────────┘   *   └──────────────┘
      │
      │
┌─────────────┐       ┌──────────────┐
│FamilyMember │       │    Album     │
└─────────────┘       └──────────────┘
```

## Core Tables

### User
Stores user account information and authentication data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Unique user identifier |
| username | String(80) | UNIQUE, NOT NULL | Unique username |
| email | String(120) | UNIQUE, NOT NULL | User email address |
| password_hash | String(128) | NOT NULL | Bcrypt password hash |
| is_active | Boolean | DEFAULT TRUE | Account active status |
| is_admin | Boolean | DEFAULT FALSE | Admin role flag |
| is_superuser | Boolean | DEFAULT FALSE | Superuser role flag |
| created_at | DateTime | | Account creation timestamp |
| updated_at | DateTime | | Last update timestamp |

**Relationships:**
- `photos` → Photo (one-to-many)
- `albums` → Album (one-to-many)
- `subscriptions` → UserSubscription (one-to-many)
- `vault_memberships` → FamilyMember (one-to-many)

**Indexes:**
- `username` (unique)
- `email` (unique)

---

### Photo
Stores comprehensive photo metadata and processing information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Unique photo identifier |
| user_id | Integer | FOREIGN KEY (User.id), NOT NULL | Photo owner |
| filename | String(255) | NOT NULL | Stored filename |
| original_name | String(255) | NOT NULL | Original upload name |
| file_path | String(500) | NOT NULL | File storage path |
| thumbnail_path | String(500) | | Thumbnail path |
| edited_filename | String(255) | | Edited version filename |
| edited_path | String(500) | | Edited version path |
| file_size | Integer | | File size in bytes |
| width | Integer | | Image width in pixels |
| height | Integer | | Image height in pixels |
| mime_type | String(100) | | MIME type |
| upload_source | String(50) | DEFAULT 'file' | Upload method (file/camera) |

**EXIF Metadata:**
| Column | Type | Description |
|--------|------|-------------|
| date_taken | DateTime | Original capture date |
| camera_make | String(100) | Camera manufacturer |
| camera_model | String(100) | Camera model |
| iso | Integer | ISO sensitivity |
| aperture | Float | F-stop value |
| shutter_speed | String(50) | Exposure time |
| focal_length | Float | Focal length (mm) |
| flash_used | Boolean | Flash fired |
| gps_latitude | Float | GPS latitude |
| gps_longitude | Float | GPS longitude |
| gps_altitude | Float | GPS altitude (m) |
| location_name | String(255) | Location name |

**Processing Metadata:**
| Column | Type | Description |
|--------|------|-------------|
| enhancement_settings | JSON | Enhancement parameters |
| colorization_method | String(50) | Colorization type (dnn/ai) |
| colorization_metadata | JSON | Colorization details |
| ai_analysis | JSON | AI analysis results |
| processing_status | String(50) | Processing state |

**User Metadata:**
| Column | Type | Description |
|--------|------|-------------|
| description | Text | User description |
| tags | String(500) | Comma-separated tags |
| is_favorite | Boolean | Favorite flag |

**Timestamps:**
| Column | Type | Description |
|--------|------|-------------|
| created_at | DateTime | Upload timestamp |
| updated_at | DateTime | Last modification |

**Relationships:**
- `user` → User (many-to-one)
- `voice_memos` → VoiceMemo (one-to-many)
- `vault_shares` → VaultPhoto (one-to-many)
- `story_links` → StoryPhoto (one-to-many)

**Indexes:**
- `user_id` (foreign key)
- `created_at` (for sorting)
- `is_favorite` (for filtering)

---

### Album
Organizes photos into collections.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Unique album identifier |
| user_id | Integer | FOREIGN KEY (User.id), NOT NULL | Album owner |
| name | String(100) | NOT NULL | Album name |
| description | Text | | Album description |
| cover_photo_id | Integer | FOREIGN KEY (Photo.id) | Cover photo |
| time_period | String(100) | | Time period (e.g., "Summer 2024") |
| location | String(200) | | Location |
| is_public | Boolean | DEFAULT FALSE | Public visibility |
| created_at | DateTime | | Creation timestamp |
| updated_at | DateTime | | Last update |

---

### Person
Represents individuals for photo tagging.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Unique person identifier |
| user_id | Integer | FOREIGN KEY (User.id), NOT NULL | Creator user |
| name | String(100) | NOT NULL | Person's name |
| nickname | String(100) | | Nickname |
| birth_year | Integer | | Birth year |
| relationship | String(100) | | Relationship to user |
| notes | Text | | Additional notes |
| created_at | DateTime | | Creation timestamp |

---

### PhotoPerson (Association Table)
Links photos to tagged people.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Unique tag identifier |
| photo_id | Integer | FOREIGN KEY (Photo.id), NOT NULL | Tagged photo |
| person_id | Integer | FOREIGN KEY (Person.id), NOT NULL | Tagged person |
| confidence | Float | | Detection confidence (0.0-1.0) |
| bounding_box | JSON | | Face bounding box coordinates |
| created_at | DateTime | | Tag creation timestamp |

**Unique Constraint:** (photo_id, person_id)

---

## Family Vault Tables

### FamilyVault
Shared photo collections for families.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Unique vault identifier |
| name | String(100) | NOT NULL | Vault name |
| description | Text | | Vault description |
| creator_id | Integer | FOREIGN KEY (User.id), NOT NULL | Vault creator |
| vault_code | String(20) | UNIQUE | Access code |
| is_public | Boolean | DEFAULT FALSE | Public visibility |
| created_at | DateTime | | Creation timestamp |
| updated_at | DateTime | | Last update |

**Relationships:**
- `creator` → User (many-to-one)
- `members` → FamilyMember (one-to-many)
- `invitations` → VaultInvitation (one-to-many)
- `photos` → VaultPhoto (one-to-many)
- `stories` → Story (one-to-many)

---

### FamilyMember
Vault membership and roles.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Unique membership ID |
| vault_id | Integer | FOREIGN KEY (FamilyVault.id), NOT NULL | Vault |
| user_id | Integer | FOREIGN KEY (User.id), NOT NULL | Member |
| role | String(50) | DEFAULT 'member' | Role (owner/admin/member) |
| status | String(50) | DEFAULT 'active' | Status (active/pending/removed) |
| joined_at | DateTime | | Join timestamp |

**Unique Constraint:** (vault_id, user_id)

---

### VaultPhoto (Association Table)
Links photos to vaults.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Unique share ID |
| vault_id | Integer | FOREIGN KEY (FamilyVault.id), NOT NULL | Vault |
| photo_id | Integer | FOREIGN KEY (Photo.id), NOT NULL | Photo |
| added_by | Integer | FOREIGN KEY (User.id), NOT NULL | User who added |
| caption | Text | | Photo caption |
| added_at | DateTime | | Share timestamp |

**Unique Constraint:** (vault_id, photo_id)

---

### VaultInvitation
Tracks vault invitations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Unique invitation ID |
| vault_id | Integer | FOREIGN KEY (FamilyVault.id), NOT NULL | Vault |
| inviter_id | Integer | FOREIGN KEY (User.id), NOT NULL | Inviter |
| invitee_email | String(120) | NOT NULL | Invitee email |
| status | String(50) | DEFAULT 'pending' | Status (pending/accepted/declined) |
| created_at | DateTime | | Invitation timestamp |
| last_sent_at | DateTime | | Last email sent |

---

## Subscription & Billing Tables

### SubscriptionPlan
Available subscription tiers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Plan identifier |
| name | String(50) | UNIQUE, NOT NULL | Plan name (Free/Basic/Pro/Premium) |
| price_myr | Numeric(10,2) | NOT NULL | Price in Malaysian Ringgit |
| storage_gb | Numeric(10,2) | NOT NULL | Storage quota (GB) |
| max_photos | Integer | | Maximum photos (NULL = unlimited) |
| max_vaults | Integer | | Maximum vaults |
| ai_features | Boolean | DEFAULT FALSE | AI features enabled |
| social_media_integration | Boolean | DEFAULT FALSE | Social sharing enabled |
| stripe_price_id | String(100) | | Stripe price ID |
| features_json | JSON | | Additional features |
| is_active | Boolean | DEFAULT TRUE | Plan active status |

---

### UserSubscription
User subscription records.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Subscription ID |
| user_id | Integer | FOREIGN KEY (User.id), NOT NULL | Subscriber |
| plan_id | Integer | FOREIGN KEY (SubscriptionPlan.id), NOT NULL | Subscription plan |
| status | String(50) | DEFAULT 'active' | Status (active/cancelled/expired) |
| stripe_subscription_id | String(100) | | Stripe subscription ID |
| stripe_customer_id | String(100) | | Stripe customer ID |
| current_period_start | DateTime | | Billing period start |
| current_period_end | DateTime | | Billing period end |
| cancel_at_period_end | Boolean | DEFAULT FALSE | Auto-cancel flag |
| created_at | DateTime | | Subscription start |
| updated_at | DateTime | | Last update |

---

### Invoice
Billing records with SST compliance.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Invoice ID |
| user_id | Integer | FOREIGN KEY (User.id), NOT NULL | Customer |
| subscription_id | Integer | FOREIGN KEY (UserSubscription.id) | Related subscription |
| invoice_number | String(50) | UNIQUE, NOT NULL | Invoice number |
| amount_myr | Numeric(10,2) | NOT NULL | Amount (MYR) |
| sst_amount | Numeric(10,2) | | SST tax amount |
| total_amount | Numeric(10,2) | NOT NULL | Total with tax |
| status | String(50) | DEFAULT 'pending' | Payment status |
| stripe_invoice_id | String(100) | | Stripe invoice ID |
| issued_at | DateTime | | Issue date |
| paid_at | DateTime | | Payment date |

---

## Voice & Media Tables

### VoiceMemo
Audio recordings attached to photos.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Memo ID |
| photo_id | Integer | FOREIGN KEY (Photo.id), NOT NULL | Associated photo |
| user_id | Integer | FOREIGN KEY (User.id), NOT NULL | Recorder |
| filename | String(255) | NOT NULL | Audio filename |
| original_name | String(255) | NOT NULL | Original name |
| file_path | String(500) | NOT NULL | Storage path |
| file_size | Integer | | File size (bytes) |
| mime_type | String(100) | | MIME type |
| duration | Float | | Duration (seconds) |
| title | String(200) | | Memo title |
| transcript | Text | | Speech-to-text transcript |
| created_at | DateTime | | Recording timestamp |
| updated_at | DateTime | | Last update |

---

## Authentication & Security Tables

### PasswordResetToken
Secure password reset tokens.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Token ID |
| user_id | Integer | FOREIGN KEY (User.id), NOT NULL | User |
| token | String(100) | UNIQUE, NOT NULL | Reset token |
| expires_at | DateTime | NOT NULL | Expiration time |
| created_at | DateTime | | Creation timestamp |

---

### SocialMediaConnection
Social media OAuth connections.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Connection ID |
| user_id | Integer | FOREIGN KEY (User.id), NOT NULL | User |
| platform | String(50) | NOT NULL | Platform (facebook/instagram/twitter) |
| access_token | String(500) | | OAuth access token |
| refresh_token | String(500) | | OAuth refresh token |
| token_expires_at | DateTime | | Token expiration |
| platform_user_id | String(100) | | Platform user ID |
| is_active | Boolean | DEFAULT TRUE | Connection active |
| created_at | DateTime | | Connection timestamp |
| updated_at | DateTime | | Last update |

**Unique Constraint:** (user_id, platform)

---

## Story & Narrative Tables

### Story
User-generated narratives.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Story ID |
| vault_id | Integer | FOREIGN KEY (FamilyVault.id), NOT NULL | Associated vault |
| creator_id | Integer | FOREIGN KEY (User.id), NOT NULL | Story creator |
| title | String(200) | NOT NULL | Story title |
| content | Text | | Story content |
| time_period | String(100) | | Time period |
| created_at | DateTime | | Creation timestamp |
| updated_at | DateTime | | Last update |

---

### StoryPhoto (Association Table)
Links photos to stories.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Link ID |
| story_id | Integer | FOREIGN KEY (Story.id), NOT NULL | Story |
| photo_id | Integer | FOREIGN KEY (Photo.id), NOT NULL | Photo |
| order_index | Integer | DEFAULT 0 | Display order |

---

### StoryPerson (Association Table)
Links people to stories.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PRIMARY KEY | Link ID |
| story_id | Integer | FOREIGN KEY (Story.id), NOT NULL | Story |
| person_id | Integer | FOREIGN KEY (Person.id), NOT NULL | Person |

---

## Database Migrations

Database schema changes are managed using Alembic migrations located in `migrations/versions/`.

### Running Migrations

**Upgrade to latest:**
```bash
flask db upgrade
```

**Downgrade one version:**
```bash
flask db downgrade
```

**Create new migration:**
```bash
flask db migrate -m "Description of changes"
```

### Migration History

Key migrations in order:
1. Initial schema creation
2. Add EXIF metadata fields to Photo
3. Add colorization fields
4. Add voice memo support
5. Add family vault tables
6. Add subscription and billing
7. Add social media integration
8. Add SST compliance fields

---

## Indexes and Performance

### Primary Indexes
- All foreign keys are automatically indexed
- Unique constraints create implicit indexes

### Additional Indexes (Recommended)
```sql
CREATE INDEX idx_photo_created_at ON photo(created_at DESC);
CREATE INDEX idx_photo_user_favorite ON photo(user_id, is_favorite);
CREATE INDEX idx_vault_photo_vault ON vault_photo(vault_id);
CREATE INDEX idx_subscription_user_status ON user_subscription(user_id, status);
```

---

## Query Optimization Tips

1. **Use pagination** for large result sets:
```python
photos = Photo.query.filter_by(user_id=user_id)\
    .limit(20).offset((page-1)*20).all()
```

2. **Eager load relationships** to avoid N+1 queries:
```python
photos = Photo.query.options(
    joinedload(Photo.user),
    joinedload(Photo.voice_memos)
).filter_by(user_id=user_id).all()
```

3. **Use selective columns** when full objects aren't needed:
```python
photos = db.session.query(Photo.id, Photo.filename)\
    .filter_by(user_id=user_id).all()
```

4. **Filter with indexes** for better performance:
```python
# Good - uses index
photos = Photo.query.filter_by(user_id=1, is_favorite=True).all()

# Bad - full table scan
photos = Photo.query.filter(Photo.tags.like('%vacation%')).all()
```
