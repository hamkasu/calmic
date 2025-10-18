#!/bin/bash

# Test Multiple Vault Creation on Railway
# This script tests if users can create multiple family vaults

RAILWAY_URL="https://web-production-535bd.up.railway.app"
TIMESTAMP=$(date +%s)
USERNAME="vaulttest${TIMESTAMP}"
EMAIL="vaulttest${TIMESTAMP}@test.com"
PASSWORD="testpass123"

echo "🧪 Testing Multiple Vault Creation on Railway"
echo "=============================================="
echo ""

# Step 1: Register new user
echo "📝 Step 1: Registering new test user..."
echo "Username: ${USERNAME}"
echo "Email: ${EMAIL}"
REGISTER_RESPONSE=$(curl -s -X POST "${RAILWAY_URL}/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${USERNAME}\",\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}")

TOKEN=$(echo $REGISTER_RESPONSE | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "⚠️ Registration failed, trying to login instead..."
  # Try login
  LOGIN_RESPONSE=$(curl -s -X POST "${RAILWAY_URL}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}")
  TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
fi

if [ -z "$TOKEN" ]; then
  echo "❌ Registration/Login failed. Response:"
  echo "$REGISTER_RESPONSE"
  exit 1
fi

echo "✅ User authenticated!"
echo "Token: ${TOKEN:0:20}..."
echo ""

# Step 2: Get existing vaults
echo "📋 Step 2: Fetching existing vaults..."
VAULTS_RESPONSE=$(curl -s -X GET "${RAILWAY_URL}/api/family/vaults" \
  -H "Authorization: Bearer ${TOKEN}")

VAULT_COUNT=$(echo $VAULTS_RESPONSE | grep -o '"id":[0-9]*' | wc -l)
echo "Found $VAULT_COUNT existing vaults"
echo "Response: $VAULTS_RESPONSE"
echo ""

# Step 3: Create first vault
echo "🏗️  Step 3: Creating Vault #1..."
VAULT1_RESPONSE=$(curl -s -X POST "${RAILWAY_URL}/api/family/vaults" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Vault 1","description":"First test vault for multiple vault testing"}')

VAULT1_SUCCESS=$(echo $VAULT1_RESPONSE | grep -o '"success":true')
VAULT1_ID=$(echo $VAULT1_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -n "$VAULT1_SUCCESS" ]; then
  echo "✅ Vault #1 created successfully! ID: $VAULT1_ID"
  echo "Response: $VAULT1_RESPONSE"
else
  echo "❌ Vault #1 creation failed"
  echo "Response: $VAULT1_RESPONSE"
fi
echo ""

# Step 4: Create second vault
echo "🏗️  Step 4: Creating Vault #2..."
VAULT2_RESPONSE=$(curl -s -X POST "${RAILWAY_URL}/api/family/vaults" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Vault 2","description":"Second test vault - proving multiple vaults work"}')

VAULT2_SUCCESS=$(echo $VAULT2_RESPONSE | grep -o '"success":true')
VAULT2_ID=$(echo $VAULT2_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -n "$VAULT2_SUCCESS" ]; then
  echo "✅ Vault #2 created successfully! ID: $VAULT2_ID"
  echo "Response: $VAULT2_RESPONSE"
else
  echo "❌ Vault #2 creation failed"
  echo "Response: $VAULT2_RESPONSE"
fi
echo ""

# Step 5: Create third vault
echo "🏗️  Step 5: Creating Vault #3..."
VAULT3_RESPONSE=$(curl -s -X POST "${RAILWAY_URL}/api/family/vaults" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Vault 3","description":"Third test vault - no limits!"}')

VAULT3_SUCCESS=$(echo $VAULT3_RESPONSE | grep -o '"success":true')
VAULT3_ID=$(echo $VAULT3_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -n "$VAULT3_SUCCESS" ]; then
  echo "✅ Vault #3 created successfully! ID: $VAULT3_ID"
  echo "Response: $VAULT3_RESPONSE"
else
  echo "❌ Vault #3 creation failed"
  echo "Response: $VAULT3_RESPONSE"
fi
echo ""

# Step 6: Get all vaults again to verify
echo "📊 Step 6: Verifying all vaults..."
FINAL_VAULTS=$(curl -s -X GET "${RAILWAY_URL}/api/family/vaults" \
  -H "Authorization: Bearer ${TOKEN}")

FINAL_COUNT=$(echo $FINAL_VAULTS | grep -o '"id":[0-9]*' | wc -l)
echo "Total vaults now: $FINAL_COUNT"
echo ""
echo "All vaults:"
echo $FINAL_VAULTS | jq '.' 2>/dev/null || echo $FINAL_VAULTS
echo ""

# Summary
echo "=============================================="
echo "📊 TEST SUMMARY"
echo "=============================================="
echo "✅ Vault #1: ${VAULT1_SUCCESS:+Created} ${VAULT1_SUCCESS:-Failed} (ID: ${VAULT1_ID:-N/A})"
echo "✅ Vault #2: ${VAULT2_SUCCESS:+Created} ${VAULT2_SUCCESS:-Failed} (ID: ${VAULT2_ID:-N/A})"
echo "✅ Vault #3: ${VAULT3_SUCCESS:+Created} ${VAULT3_SUCCESS:-Failed} (ID: ${VAULT3_ID:-N/A})"
echo ""
echo "🎯 RESULT: Multiple vault creation $([ -n "$VAULT1_SUCCESS" ] && [ -n "$VAULT2_SUCCESS" ] && [ -n "$VAULT3_SUCCESS" ] && echo "WORKS! ✅" || echo "FAILED ❌")"
echo "Total vaults: $FINAL_COUNT"
