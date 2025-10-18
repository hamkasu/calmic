# Railway Deployment Guide - iOS Vault Creation Fix

## Issue Fixed
iOS app was unable to create family vaults on Railway production. The mobile API was missing the `POST /api/family/vaults` endpoint for vault creation.

## What Was Changed
Added vault creation endpoint to `photovault/routes/mobile_api.py`:
- **New Endpoint**: `POST /api/family/vaults` 
- **Authentication**: JWT token required
- **CSRF**: Exempted for mobile clients
- **Functionality**: 
  - Validates vault name and description
  - Generates unique vault code
  - Creates vault record
  - Automatically adds creator as admin member
  - Returns vault details in JSON format

## Deployment Steps

### 1. Add and Commit Changes
```bash
git add photovault/routes/mobile_api.py
git commit -m "Add vault creation endpoint for iOS app"
```

### 2. Push to GitHub (Railway Auto-Deploy)
```bash
git push origin main
```

### 3. Monitor Railway Deployment
- Go to your Railway dashboard
- Watch the deployment logs
- Wait for "Deployment successful" message
- Usually takes 2-3 minutes

### 4. Test on iOS App
1. Open StoryKeep app on your iPhone
2. Go to Family Vaults section
3. Tap "Create Vault" button
4. Enter vault name and description
5. Tap "Create"
6. ✅ Should successfully create vault and show vault code

## Expected Response
```json
{
  "success": true,
  "vault": {
    "id": 1,
    "name": "Family Photos",
    "description": "Our family memories",
    "vault_code": "ABC123",
    "is_public": false,
    "created_at": "2025-10-11T01:40:00"
  }
}
```

## Verification
After deployment, the iOS app should be able to:
- ✅ Create new family vaults
- ✅ Receive unique vault codes
- ✅ Automatically become vault admin
- ✅ View the newly created vault in the vaults list

## Troubleshooting
If vault creation still fails after deployment:
1. Check Railway logs for errors
2. Verify the endpoint exists: `GET https://web-production-535bd.up.railway.app/api/family/vaults`
3. Test with Postman/curl:
   ```bash
   curl -X POST https://web-production-535bd.up.railway.app/api/family/vaults \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Vault", "description": "Testing vault creation"}'
   ```

## Local Testing (Already Working)
The fix has been tested locally and is working correctly on the Replit development server.

---
**Status**: Ready for Railway deployment
**Priority**: High - blocking iOS vault creation feature
