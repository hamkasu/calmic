# Railway Deployment Guide: Vault Invite Member Feature

## Issue Fixed
The iOS app's "Invite Member" feature (+ button next to Members) was not working on Railway production because the `/api/family/vault/<vault_id>/invite` endpoint was missing from the mobile API.

## What Was Changed

### File: `photovault/routes/mobile_api.py`

1. **Added VaultInvitation model import** (line 8)
   ```python
   from photovault.models import ..., VaultInvitation
   ```

2. **Created new endpoint: `/api/family/vault/<vault_id>/invite`** (lines 929-1086)
   - POST endpoint with JWT authentication (`@token_required`)
   - Accepts JSON: `{ "email": "user@example.com", "role": "member" }`
   - Validates email format and role
   - Checks user permissions (must be vault admin or creator)
   - Checks for existing members and pending invitations
   - Creates VaultInvitation record
   - Sends invitation email via SendGrid
   - Returns success response with invitation details

## Deployment Steps

### Step 1: Push Changes to GitHub
```bash
git add photovault/routes/mobile_api.py
git commit -m "Add mobile API endpoint for vault member invitations"
git push origin main
```

### Step 2: Verify Railway Auto-Deployment
1. Go to your Railway dashboard: https://railway.app/
2. Navigate to your PhotoVault project
3. Check the "Deployments" tab
4. Wait for the new deployment to complete (usually 2-3 minutes)
5. Look for status: "Success" or "Active"

### Step 3: Test on iOS App
1. Open the StoryKeep app on your iPhone
2. Navigate to a Family Vault where you're the admin/creator
3. Tap the **+ button next to "Members"**
4. Enter an email address and select a role
5. Tap "Send Invitation"
6. You should see: "Invitation sent to [email]"

## API Endpoint Details

### POST /api/family/vault/{vault_id}/invite

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "friend@example.com",
  "role": "member"
}
```

**Response (Success - 201):**
```json
{
  "success": true,
  "message": "Invitation sent to friend@example.com",
  "invitation": {
    "id": 123,
    "email": "friend@example.com",
    "role": "member",
    "invitation_url": "https://your-app.com/family/invitation/abc123...",
    "expires_at": "2025-10-18T10:30:00"
  }
}
```

**Error Responses:**
- `400` - Invalid email, invalid role, or validation error
- `403` - User lacks permission to invite members
- `404` - Vault not found
- `500` - Server error

## Validation Rules
- **Email**: Must be valid format (user@domain.com)
- **Role**: Must be 'admin' or 'member'
- **Permission**: Only vault creator or admin members can invite
- **Duplicates**: Cannot invite existing members or duplicate pending invitations

## Related Features
This fix also ensures:
- ✅ Add photos to vault works (endpoint already existed)
- ✅ View vault details works
- ✅ Create vault works
- ✅ List vaults works

## Rollback Instructions
If issues occur after deployment:

```bash
# Revert to previous version
git revert HEAD
git push origin main
```

Then wait for Railway to auto-deploy the reverted version.

## Support
If the invite feature still doesn't work after deployment:
1. Check Railway logs for errors
2. Verify the iOS app is using the correct Railway URL
3. Ensure SendGrid is configured for email sending
4. Check that VaultInvitation table exists in production database
