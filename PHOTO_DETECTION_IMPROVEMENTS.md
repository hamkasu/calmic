# Photo Detection Sensitivity Improvements

## Problem Solved
The edge detection was **too sensitive** and was extracting items WITHIN photographs, such as:
- Picture frames on walls in photos
- Photos displayed on phones/tablets in images
- Small posters or artwork in the background
- Stickers, cards, or small objects

## Changes Made

### 1. **Minimum Photo Area** (25x increase!)
- **Before**: 2,000 pixels
- **After**: 50,000 pixels
- **Impact**: Filters out tiny objects and items within photos

### 2. **Minimum Confidence Threshold** (3.3x stricter!)
- **Before**: 0.15 (accepts almost anything)
- **After**: 0.50 (only confident detections)
- **Impact**: Dramatically reduces false positives

### 3. **Multi-Scale Detection** (removed small scale)
- **Before**: Scales [1.0, 0.75, 0.5] - detects very small objects
- **After**: Scales [1.0, 0.85] - focuses on full-size photos
- **Impact**: No longer detects tiny items at small scales

### 4. **Minimum Dimensions** (NEW!)
- **Requirement**: Photos must be at least 200x200 pixels
- **Impact**: Prevents detection of small items in photographs

### 5. **Minimum Perimeter** (NEW!)
- **Requirement**: Perimeter must be at least 1,000 pixels
- **Impact**: Filters out thin/small objects

### 6. **Aspect Ratio Refinement**
- **Before**: 0.15 to 6.0 (extremely wide range)
- **After**: 0.2 to 5.0 (more reasonable range)
- **Impact**: Rejects extreme shapes that aren't typical photos

### 7. **Maximum Photo Area Ratio**
- **Before**: 0.92 (92% of image)
- **After**: 0.85 (85% of image)
- **Impact**: More conservative maximum size

---

## Summary of Parameters

| Parameter | Before | After | Change |
|-----------|--------|-------|--------|
| Min Area | 2,000 | 50,000 | **+2,400%** |
| Min Confidence | 0.15 | 0.50 | **+233%** |
| Min Width/Height | None | 200px | **NEW** |
| Min Perimeter | None | 1,000px | **NEW** |
| Detection Scales | 3 scales | 2 scales | **-33%** |
| Aspect Ratio Min | 0.15 | 0.2 | **+33%** |
| Aspect Ratio Max | 6.0 | 5.0 | **-17%** |

---

## What This Means

**Before:**
- ✅ Detects everything (including noise)
- ❌ Extracts items WITHIN photos
- ❌ Too many false positives
- ❌ Tiny objects detected

**After:**
- ✅ Only detects actual physical photos
- ✅ Ignores items within photos
- ✅ Much fewer false positives
- ✅ Focuses on meaningful photo sizes

---

## Testing Recommendations

### Good Test Cases (Should Be Detected):
1. Standard 4x6 inch photos on a table
2. Polaroid photos with white borders
3. Large family portraits on walls
4. Photo albums (individual photos)
5. Stacks of photos

### Should NOT Be Detected:
1. ❌ Picture frames visible in photos
2. ❌ Photos displayed on phone screens in images
3. ❌ Small stickers or cards
4. ❌ Posters in the background of photos
5. ❌ Tiny artwork or decorations

---

## Railway Deployment

Your local Replit environment has been updated ✅

To deploy to Railway production:
1. Push changes to GitHub
2. Railway will auto-deploy
3. No SQL changes needed - this is a code-only update

---

## Still Too Sensitive?

If you find it's still detecting too many items, you can further increase:

```python
# In photovault/utils/photo_detection.py, line ~30

self.min_photo_area = 75000  # Increase from 50,000
self.min_confidence = 0.60    # Increase from 0.50
```

## Too Strict Now?

If legitimate photos are being missed, you can decrease:

```python
self.min_photo_area = 30000   # Decrease from 50,000
self.min_confidence = 0.40     # Decrease from 0.50
```

---

**Status**: ✅ Applied to Replit (local development)  
**Next Step**: Test with real photo extraction, then deploy to Railway
