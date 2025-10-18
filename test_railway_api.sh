#!/bin/bash
# Test Railway API Endpoints for iOS App
# Usage: ./test_railway_api.sh <your_auth_token>

RAILWAY_URL="https://web-production-535bd.up.railway.app"
AUTH_TOKEN="${1:-YOUR_TOKEN_HERE}"

echo "=================================================="
echo "Testing Railway API Endpoints for iOS App"
echo "=================================================="
echo ""

echo "1. Testing /api/dashboard endpoint..."
echo "Request: GET $RAILWAY_URL/api/dashboard"
curl -X GET "$RAILWAY_URL/api/dashboard" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s
echo ""
echo "=================================================="
echo ""

echo "2. Testing /api/photos endpoint..."
echo "Request: GET $RAILWAY_URL/api/photos"
curl -X GET "$RAILWAY_URL/api/photos?page=1&limit=20" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s
echo ""
echo "=================================================="
echo ""

echo "3. Testing /api/family/vaults endpoint..."
echo "Request: GET $RAILWAY_URL/api/family/vaults"
curl -X GET "$RAILWAY_URL/api/family/vaults" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s
echo ""
echo "=================================================="
echo ""

echo "TEST COMPLETE"
echo ""
echo "Expected Results:"
echo "- HTTP Status 200 = Endpoint exists and is working"
echo "- HTTP Status 401 = Authentication failed (check your token)"
echo "- HTTP Status 404 = Endpoint not deployed yet"
echo ""
