#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMSIsInJvbGUiOiJzdXBlcmFkbWluIiwiZXhwIjoxNzYyMzM3NDQ2fQ.z3QzKWO2KVGj0Oz8ICioktPe2w84jyF854sDrGRRCrE"
API_URL="https://openschoolbackend-production.up.railway.app"

echo -e "${YELLOW}=== Шаг 1: Создание школы ===${NC}"
SCHOOL_RESPONSE=$(curl -s -X POST "$API_URL/api/superadmin/create-school" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "International school Haileybury Almaty", "code": "SCHOOL1"}')

echo "$SCHOOL_RESPONSE" | python3 -m json.tool
SCHOOL_ID=$(echo "$SCHOOL_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo -e "${GREEN}✅ Школа создана с ID: $SCHOOL_ID${NC}\n"

echo -e "${YELLOW}=== Шаг 2: Создание школьного админа ===${NC}"
ADMIN_RESPONSE=$(curl -s -X POST "$API_URL/api/superadmin/create-school-admin" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"full_name\": \"Админ Школы\", \"email\": \"admin@haileybury.com\", \"password\": \"Admin123!\", \"school_id\": $SCHOOL_ID}")

echo "$ADMIN_RESPONSE" | python3 -m json.tool
echo -e "${GREEN}✅ Школьный админ создан${NC}\n"

echo -e "${YELLOW}=== Шаг 3: Проверка входа школьного админа ===${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@haileybury.com", "password": "Admin123!"}')

echo "$LOGIN_RESPONSE" | python3 -m json.tool
echo -e "${GREEN}✅ Вход успешен! role = school_admin${NC}"
