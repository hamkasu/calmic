# Voice Memo Badge Feature - Railway Deployment Guide

## Feature Overview
Added voice memo indicators (🎤 microphone badges) to the iOS gallery. Photos with voice memos now display a badge showing the count.

## Changes Made

### Backend Changes (`photovault/routes/mobile_api.py`)

#### Updated `/api/dashboard` endpoint:
```python
# Efficient voice memo count query (single SQL query, not N+1)
voice_memo_counts = db.session.query(
    VoiceMemo.photo_id,
    func.count(VoiceMemo.id).label('count')
).filter(
    VoiceMemo.photo_id.in_([p.id for p in photos])
).group_by(VoiceMemo.photo_id).all()

# Create dictionary for O(1) lookup
voice_memo_dict = {photo_id: count for photo_id, count in voice_memo_counts}

# Add count to each photo
all_photos.append({
    # ... existing fields ...
    'voice_memo_count': voice_memo_dict.get(photo.id, 0)  # NEW FIELD
})
```

### Frontend Changes (iOS App)
**No changes needed!** The iOS app (`GalleryScreen.js`) already has the UI code:

```javascript
{item.voice_memo_count > 0 && (
  <View style={styles.voiceBadge}>
    <Ionicons name="mic" size={14} color="#fff" />
    <Text style={styles.voiceBadgeText}>{item.voice_memo_count}</Text>
  </View>
)}
```

## Railway Deployment Steps

### 1. Stage and Commit Changes
```bash
git add photovault/routes/mobile_api.py
git commit -m "Add voice memo count to gallery photos for iOS badge display"
```

### 2. Push to Railway
```bash
git push origin main
```

### 3. Wait for Deployment
- Railway auto-deploys in 2-3 minutes
- Monitor Railway dashboard for deployment status

### 4. Test in iOS App
Once deployed:
1. Open StoryKeep app on iOS
2. Navigate to Gallery tab
3. Look for microphone badges 🎤 on photos with voice memos
4. Badge shows count (e.g., "2" if there are 2 voice notes)

## Technical Details

### Performance Optimization
- **Before**: Would require N queries (one per photo)
- **After**: Single GROUP BY query with dictionary lookup
- **Result**: O(1) lookup time, minimal database load

### Database Query
```sql
SELECT voice_memo.photo_id, COUNT(voice_memo.id) AS count 
FROM voice_memo 
WHERE voice_memo.photo_id IN (?, ?, ...)  -- all user's photo IDs
GROUP BY voice_memo.photo_id
```

### API Response Structure
```json
{
  "all_photos": [
    {
      "id": 123,
      "filename": "photo.jpg",
      "url": "/uploads/1/photo.jpg",
      "voice_memo_count": 2,  // ← NEW FIELD
      "has_edited": false,
      // ... other fields
    }
  ],
  "total_photos": 46,
  // ... other stats
}
```

## Expected Result
After deployment, the iOS gallery will show:
- ✅ Microphone icon 🎤 on photos with voice memos
- ✅ Count badge showing number of voice memos
- ✅ Clean visual indicator (already styled in iOS app)

## Files Modified
- ✅ `photovault/routes/mobile_api.py` - Added voice memo count to dashboard endpoint

## Verification Steps
1. Check Railway deployment logs for successful deployment
2. Open iOS app and navigate to Gallery
3. Upload a voice memo to a photo
4. Return to Gallery - badge should appear on that photo
5. Upload another voice memo to same photo - count should update to "2"

## Rollback (if needed)
If issues arise, revert the commit:
```bash
git revert HEAD
git push origin main
```

## Dependencies
- Requires `VoiceMemo` model (already exists)
- Requires SQLAlchemy `func.count()` (already imported)
- No new packages needed
