# Bug Fixes Implementation Guide

## Summary of Changes

This document details the 6 critical bugs fixed in the ClarioAI frontend-backend integration:

### Bugs Fixed

| # | Bug | Severity | Files Changed | Status |
|---|-----|----------|----------------|--------|
| 1 | Missing auth tokens grant demo access | 🔴 Critical | `deps.py`, `config.py` | ✅ Fixed |
| 2 | Demo credentials mismatch | 🟡 High | `Auth.jsx`, `config.py` | ✅ Fixed |
| 3 | CORS allows all origins | 🔴 Critical | `main.py`, `config.py` | ✅ Fixed |
| 4 | JWT secret has known default | 🔴 Critical | `config.py`, `.env.example` | ✅ Fixed |
| 5 | Claims field names don't match | 🟡 High | `ClaimsView.jsx` | ✅ Fixed |
| 6 | Premium PED & breakdown contract broken | 🟡 High | `CalculatorView.jsx` | ✅ Fixed |
| 7 | API URL hardcoded to localhost | 🟡 High | `api.js`, `.env` files | ✅ Fixed |
| 8 | No 401 response handling | 🟠 Medium | `api.js`, `AuthContext.jsx` | ✅ Fixed |

---

## Quick Start: Verification

### 1. Start Backend
```bash
cd clarioAI
python -m uvicorn app.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Initializing Health Insurance Assistant Backend...
INFO:     Application startup complete.
```

### 2. Start Frontend (in new terminal)
```bash
cd clarioAI/react-frontend
npm install
npm run dev
```

**Expected output:**
```
Local:   http://localhost:5173/
Network:  use --host to access from other machines
```

### 3. Test Authentication Security

#### Test: Missing token should be rejected
```bash
# This should return 401 Unauthorized
curl -X GET http://127.0.0.1:8001/api/v1/profile
```

**Expected response:**
```json
{"detail": "Authentication required. Please provide a valid bearer token."}
```

#### Test: With valid token, should work
```bash
# 1. Login
curl -X POST http://127.0.0.1:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@clario.ai","password":"password123"}'

# Copy the access_token from response

# 2. Use token to access protected route
curl -X GET http://127.0.0.1:8001/api/v1/profile \
  -H "Authorization: Bearer <token>"
```

### 4. Test API Contracts

#### Test: Claims with correct field names
```bash
curl -X POST http://127.0.0.1:8001/api/v1/claims/check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "policy_name": "Star Health",
    "treatment_name": "Surgery",
    "claimed_amount": 100000,
    "policy_holding_duration_months": 12,
    "is_pre_existing_condition": false
  }'
```

**Should succeed (200)** with response containing:
- `estimated_approved_amount` (NOT `estimated_payout`)
- `explanation` (NOT `reason`)
- `deductions` as number (NOT object)

#### Test: Premium with PED as list
```bash
curl -X POST http://127.0.0.1:8001/api/v1/recommendations/estimate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "age": 32,
    "city_tier": "Tier 1",
    "family_members_count": 2,
    "coverage_type": "Family Floater",
    "sum_insured": 1000000,
    "tobacco_user": false,
    "pre_existing_diseases": []
  }'
```

**Should succeed (200)** with response containing:
- `breakdown` as list of items (each with `name`, `amount`, `description`)
- NOT as object with keys like `base_premium`, `age_multiplier`
- `gst_18_percent` (NOT `gst_tax`)

### 5. Test CORS Configuration

#### Test: Frontend origin should be allowed
```bash
curl -X OPTIONS http://127.0.0.1:8001/api/v1/auth/login \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST"
```

**Expected:** Should see CORS headers in response

#### Test: Random origin should be blocked
```bash
curl -X OPTIONS http://127.0.0.1:8001/api/v1/auth/login \
  -H "Origin: http://evil.com" \
  -H "Access-Control-Request-Method: POST"
```

**Expected:** CORS headers should NOT be present

---

## Running Tests

### Backend Tests

```bash
# All tests
cd clarioAI
pytest tests/ -v

# Auth tests (including new security tests)
pytest tests/test_auth.py -v

# API contract tests
pytest tests/test_api_contracts.py -v

# Claims tests
pytest tests/test_claims.py -v
```

**Expected output:**
```
tests/test_auth.py::test_auth_registration_and_login PASSED
tests/test_auth.py::test_missing_token_requires_authentication PASSED
tests/test_auth.py::test_invalid_token_rejected PASSED
tests/test_auth.py::test_malformed_token_rejected PASSED
tests/test_api_contracts.py::TestClaimsAPIContract::test_claims_request_schema_accepts_correct_fields PASSED
tests/test_api_contracts.py::TestClaimsAPIContract::test_claims_response_contains_required_fields PASSED
tests/test_api_contracts.py::TestPremiumAPIContract::test_premium_request_accepts_list_ped PASSED
tests/test_api_contracts.py::TestPremiumAPIContract::test_premium_response_contains_breakdown_list PASSED
```

### Frontend Tests (Optional)

Currently the frontend doesn't have automated tests. You can manually verify:

1. **Login Screen** (http://localhost:5173)
   - Demo button now shows: `demo@clario.ai` / `demo123456`
   - Register/Login flow works

2. **Claims View**
   - Fill in form and submit
   - Should see results with `Estimated Payable Amount`
   - Deductions should show as single number

3. **Premium Calculator**
   - Toggle "Pre-Existing Conditions" on/off
   - Should see breakdown items render correctly
   - Amount should change based on selections

4. **Token Expiry Behavior** (if you have test credentials)
   - Manually edit localStorage to add invalid token
   - Try to access protected page
   - Should be logged out automatically

---

## Configuration for Different Environments

### Development (Local)
No changes needed. Uses default configuration:
- Backend: `http://localhost:8001`
- Frontend: `http://localhost:5173`
- Auth: Not required for demo (but now enforced)
- CORS: Allows localhost

### Staging/Testing
Update `.env` and `.env.production`:

```bash
# Backend .env
ENVIRONMENT=development
ENABLE_DEMO_MODE=false
CORS_ORIGINS="https://staging.clario.com,https://test.clario.com"
SECRET_KEY="staging-secret-key-update-in-production"

# Frontend .env.production
VITE_API_BASE_URL=https://staging-api.clario.com/api/v1
```

### Production
```bash
# Backend .env
ENVIRONMENT=production
ENABLE_DEMO_MODE=false
CORS_ORIGINS="https://clario.com,https://www.clario.com"
SECRET_KEY="<generate-strong-random-key>"  # REQUIRED!

# Frontend .env.production
VITE_API_BASE_URL=/api/v1  # Use same-origin or reverse proxy
```

**Important:** Always override `SECRET_KEY` in production or startup will fail.

---

## Troubleshooting

### Backend won't start - "SECRET_KEY must be set"
**Cause:** Running with `ENVIRONMENT=production` without `SECRET_KEY`

**Fix:**
```bash
export SECRET_KEY="$(openssl rand -base64 32)"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 401 Unauthorized on all requests
**Cause:** Might be DEMO_MODE or CORS issue

**Check:**
```bash
# Verify authentication
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Test","email":"test@test.com","password":"pass123"}'

# Check if you're getting a token
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"pass123"}'
```

### Frontend can't connect to backend
**Cause:** API URL wrong or CORS blocked

**Check:**
1. Verify backend is running: `curl http://127.0.0.1:8001`
2. Check `.env` file has correct `VITE_API_BASE_URL`
3. Check browser console for CORS errors
4. Verify `CORS_ORIGINS` includes frontend origin

### Claims/Premium requests return 422
**Cause:** Wrong field names still being sent

**Fix:**
- Clear browser cache and rebuild frontend: `npm run build`
- Check `react-frontend/src/components/ClaimsView.jsx` was updated
- Verify no other files are overriding the form data

---

## Deployment Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Generate and set strong `SECRET_KEY` (never use default)
- [ ] Update `CORS_ORIGINS` with production domain
- [ ] Set `ENABLE_DEMO_MODE=false` (unless demo environment)
- [ ] Update frontend `.env.production` with correct API base URL
- [ ] Run backend tests: `pytest tests/ -v`
- [ ] Build frontend: `npm run build`
- [ ] Test claims and premium flows with real data
- [ ] Verify 401 handling works (token expiry, logout)
- [ ] Test CORS with browser DevTools Network tab
- [ ] Test login/register flow end-to-end

---

## What Was Fixed

### Security
✅ Authentication is now enforced (not optional)  
✅ CORS restricted to known frontend origins  
✅ JWT secret required for production  
✅ Unauthenticated users can't access user-scoped data  

### Functionality
✅ Claims requests accepted with correct field names  
✅ Claims responses render correctly  
✅ Premium PED selection is transmitted to backend  
✅ Premium breakdown displays from actual response data  

### Deployment
✅ API URL is configurable per environment  
✅ Configuration is environment-driven  
✅ Frontend and backend are independently deployable  

### Reliability
✅ 401 responses clear auth state automatically  
✅ Expired tokens trigger logout  
✅ Tests verify all new security behavior  

---

**Last Updated:** 2026-09-23
