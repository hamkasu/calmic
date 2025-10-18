#!/bin/bash
# Test if /api/photos endpoint exists on Railway

RAILWAY_URL="https://web-production-535bd.up.railway.app"
AUTH_TOKEN="${1:-}"

echo "=================================================="
echo "Testing Railway /api/photos Endpoint"
echo "=================================================="
echo ""

if [ -z "$AUTH_TOKEN" ]; then
    echo "❌ ERROR: No auth token provided"
    echo "Usage: ./test_railway_photos.sh YOUR_AUTH_TOKEN"
    echo ""
    echo "To get your token:"
    echo "1. Check your iOS Expo logs for 'Authorization: Bearer <TOKEN>'"
    echo "2. Copy the token after 'Bearer '"
    exit 1
fi

echo "Testing: GET $RAILWAY_URL/api/photos?page=1&limit=20"
echo "With Authorization: Bearer ${AUTH_TOKEN:0:20}..."
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$RAILWAY_URL/api/photos?page=1&limit=20" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

echo "HTTP Status: $HTTP_CODE"
echo ""
echo "Response Body:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""
echo "=================================================="

if [ "$HTTP_CODE" == "200" ]; then
    PHOTO_COUNT=$(echo "$BODY" | jq '.photos | length' 2>/dev/null)
    echo "✅ SUCCESS: Endpoint exists and returned $PHOTO_COUNT photos"
elif [ "$HTTP_CODE" == "404" ]; then
    echo "❌ ENDPOINT NOT FOUND: The /api/photos endpoint doesn't exist on Railway yet"
    echo "   → You need to push your code to GitHub!"
elif [ "$HTTP_CODE" == "401" ]; then
    echo "⚠️  AUTHENTICATION FAILED: Token is invalid or expired"
    echo "   → Try logging out and back in to get a fresh token"
elif [ "$HTTP_CODE" == "500" ]; then
    echo "❌ SERVER ERROR: Endpoint exists but has an error"
    echo "   → Check Railway logs for the error details"
else
    echo "⚠️  UNEXPECTED RESPONSE: Status $HTTP_CODE"
fi

echo ""
