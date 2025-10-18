# Colorization Filter Feature - Deployment Guide

## Overview
Added filtering capability to StoryKeep to show photos by colorization method (DNN, AI, or uncolorized) across both web and mobile platforms.

## Changes Summary

### Database Changes
**New Columns Added to Photo Table:**
- `edited_path` (VARCHAR 500) - Stores the path of edited/colorized images
- `enhancement_metadata` (JSON) - Stores enhancement details including:
  - `colorization.method` - The colorization method used (dnn, ai_guided_dnn, etc.)
  - `colorization.ai_guidance` - AI analysis text (for AI colorization)
  - `colorization.model` - AI model used (gemini-2.0-flash-exp)
  - `colorization.timestamp` - When colorization was performed

**Migration File:** `photovault/migrations/20251012_105417_add_enhancement_metadata.py`

### Backend Changes

#### 1. Web Gallery Filtering (`photovault/routes/gallery.py`)
Added filter parameter support to `/photos` endpoint:
- `?filter=all` - Show all photos (default)
- `?filter=dnn` - Show only DNN colorized photos
- `?filter=ai` - Show only AI colorized photos  
- `?filter=uncolorized` - Show only photos without colorization

**Query Logic:**
```python
# DNN colorized photos
query.filter(Photo.enhancement_metadata['colorization']['method'].astext == 'dnn')

# AI colorized photos
query.filter(Photo.enhancement_metadata['colorization']['method'].astext == 'ai_guided_dnn')

# Uncolorized photos
query.filter(Photo.enhancement_metadata.is_(None))
```

#### 2. Mobile API Filtering (`photovault/routes/mobile_api.py`)
Updated `/api/photos` endpoint to support same filters:
- Added `filter` parameter handling
- Added `enhancement_metadata` to photo responses for iOS filtering
- Supports both server-side (via filter param) and client-side filtering

### Frontend Changes

#### 1. Web Gallery UI (`photovault/templates/gallery/photos.html`)
Added filter buttons in the gallery toolbar:
```html
<a href="/photos?filter=all">All Photos</a>
<a href="/photos?filter=dnn">DNN Colorized</a>
<a href="/photos?filter=ai">AI Colorized</a>
<a href="/photos?filter=uncolorized">Not Colorized</a>
```

Buttons highlight when active using `current_filter` template variable.

#### 2. iOS Gallery (`StoryKeep-iOS/src/screens/GalleryScreen.js`)
Added filter buttons and local filtering logic:
```javascript
// Filter options
<FilterButton label="All" value="all" />
<FilterButton label="DNN" value="dnn" />
<FilterButton label="AI" value="ai" />
<FilterButton label="Uncolorized" value="uncolorized" />
<FilterButton label="Originals" value="originals" />
<FilterButton label="Enhanced" value="enhanced" />
```

**Filtering Logic:**
- DNN: Checks `enhancement_metadata.colorization.method === 'dnn'`
- AI: Checks `enhancement_metadata.colorization.method === 'ai_guided_dnn'`
- Uncolorized: Checks `!enhancement_metadata`

## Deployment Steps

### Step 1: Run Database Migration

**On Replit (Development):**
```bash
# Migration already applied via execute_sql_tool
# Columns: edited_path and enhancement_metadata already exist
```

**On Railway (Production):**
```sql
-- These will run automatically on next deployment
ALTER TABLE photo ADD COLUMN IF NOT EXISTS edited_path VARCHAR(500);
ALTER TABLE photo ADD COLUMN IF NOT EXISTS enhancement_metadata JSON;
```

**Verify Migration:**
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'photo' 
  AND column_name IN ('edited_path', 'enhancement_metadata');
```

Expected output:
```
column_name          | data_type
---------------------|------------------
edited_path          | character varying
enhancement_metadata | json
```

### Step 2: Deploy Backend Changes

**Files to Deploy:**
1. `photovault/models/__init__.py` - Updated Photo model
2. `photovault/routes/gallery.py` - Web filtering logic
3. `photovault/routes/mobile_api.py` - Mobile API filtering
4. `photovault/migrations/20251012_105417_add_enhancement_metadata.py` - Migration file

**Deployment Command:**
```bash
git add photovault/models/__init__.py
git add photovault/routes/gallery.py
git add photovault/routes/mobile_api.py
git add photovault/migrations/20251012_105417_add_enhancement_metadata.py
git add photovault/templates/gallery/photos.html
git add StoryKeep-iOS/src/screens/GalleryScreen.js
git commit -m "Add colorization filter feature for web and mobile

- Added enhancement_metadata and edited_path to Photo model
- Created database migration for new columns
- Web gallery supports filter by DNN/AI/uncolorized
- Mobile API includes enhancement_metadata in responses
- iOS app has filter buttons for all colorization methods"
git push origin main
```

Railway will automatically:
1. Detect the push
2. Run migrations (if configured)
3. Deploy updated code
4. Restart the server

### Step 3: Verify Deployment

#### Test Web Filtering:
1. Login to StoryKeep web app
2. Navigate to `/photos`
3. Click filter buttons: All, DNN Colorized, AI Colorized, Not Colorized
4. Verify photos are filtered correctly
5. Check URL updates with `?filter=` parameter

#### Test Mobile Filtering:
1. Open StoryKeep iOS app
2. Go to Gallery screen
3. Tap filter buttons: All, DNN, AI, Uncolorized
4. Verify photos are filtered correctly
5. Check that filtered count updates

#### Test API Directly:
```bash
# Get all photos
curl -H "Authorization: Bearer $TOKEN" \
  https://web-production-535bd.up.railway.app/api/photos?filter=all

# Get DNN colorized only
curl -H "Authorization: Bearer $TOKEN" \
  https://web-production-535bd.up.railway.app/api/photos?filter=dnn

# Get AI colorized only
curl -H "Authorization: Bearer $TOKEN" \
  https://web-production-535bd.up.railway.app/api/photos?filter=ai
```

## Important Notes

### PostgreSQL Requirement
The JSON filtering uses PostgreSQL-specific syntax:
```python
Photo.enhancement_metadata['colorization']['method'].astext
```

**If using SQLite**, the filter queries will fail. Fallback to Python filtering:
```python
filtered_photos = [p for p in all_photos 
                   if p.enhancement_metadata and 
                   p.enhancement_metadata.get('colorization', {}).get('method') == 'dnn']
```

### Uncolorized Filter Behavior
The `uncolorized` filter checks if `enhancement_metadata IS NULL`. This means:
- ✅ Photos never enhanced → Shown
- ❌ Photos with other metadata but no colorization → Hidden

To show photos without colorization but with other metadata, update the query:
```python
# More flexible uncolorized filter
query.filter(
    (Photo.enhancement_metadata.is_(None)) |
    (~Photo.enhancement_metadata.has_key('colorization'))
)
```

### Backward Compatibility
- Existing photos without `enhancement_metadata` will appear as "Not Colorized"
- New colorizations will automatically populate `enhancement_metadata`
- All filter operations are safe with NULL values

## Testing Checklist

- [ ] Database migration successful
- [ ] Web filtering works for all filter types
- [ ] Mobile API returns `enhancement_metadata`
- [ ] iOS app filters correctly
- [ ] Pagination works with filters
- [ ] Empty states show correct messages
- [ ] Filter buttons highlight when active
- [ ] URL parameters persist across pagination

## Troubleshooting

### Issue: Filter returns no results
**Cause:** Photos don't have `enhancement_metadata`
**Solution:** Colorize some photos using DNN or AI methods

### Issue: JSON filtering error in SQLite
**Cause:** SQLite doesn't support JSON path queries
**Solution:** Use PostgreSQL or implement Python-side filtering

### Issue: Uncolorized filter shows wrong photos
**Cause:** Photos have other metadata but no colorization
**Solution:** Update filter logic to check for missing colorization key

### Issue: iOS app doesn't filter
**Cause:** API not returning `enhancement_metadata`
**Solution:** Verify mobile API includes metadata in response

## Summary

✅ **Database Schema:** Added `edited_path` and `enhancement_metadata` columns
✅ **Web Gallery:** Filter buttons and backend filtering implemented
✅ **Mobile API:** Supports filter parameter and returns metadata
✅ **iOS App:** Filter UI and local filtering logic complete
✅ **Backward Compatible:** Works with existing photos

Users can now easily filter photos by colorization method to compare DNN vs AI results!
