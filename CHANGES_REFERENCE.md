# Changes Summary: File-by-File Diff Reference

## Backend Changes

### 1. `app/config.py` - Added security validation and configuration
**Lines Changed:** ~25 lines added

**Key Changes:**
- `SECRET_KEY: Optional[str] = None` (was hardcoded)
- Added `CORS_ORIGINS`, `ENABLE_DEMO_MODE`, `DEMO_USER_EMAIL`, `DEMO_USER_PASSWORD`
- Added `__init__` method with:
  - Production SECRET_KEY validation (fails if missing/default)
  - Development SECRET_KEY auto-default
  - Startup error message for unsafe production config

**Impact:** Configuration is now environment-driven; production deployments must explicitly set SECRET_KEY

---

### 2. `app/api/deps.py` - Changed authentication to require bearer token
**Lines Changed:** ~42 lines modified

**Before:**
```python
if not token:
    user = db.query(User).filter(User.email == "demo@clario.ai").first()
    if not user:
        user = User(...)  # Create demo user
        db.add(user)
        db.commit()
    return user  # Always return something
```

**After:**
```python
if not token:
    if settings.ENABLE_DEMO_MODE:
        # Create/return demo user only if explicitly enabled
    else:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide a valid bearer token."
        )
```

**Impact:** Protected routes now reject unauthenticated requests (security fix)

---

### 3. `app/main.py` - Restricted CORS configuration
**Lines Changed:** ~5 lines

**Before:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**After:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
```

**Impact:** Only configured frontend origins can access the API

---

### 4. `.env` and `.env.example` - Configuration files
**New Files:**

`.env` - Development configuration
- `ENABLE_DEMO_MODE=false` (demo requires explicit opt-in)
- `SECRET_KEY` commented out (auto-default in dev)
- `CORS_ORIGINS` with localhost origins
- `DEMO_USER_EMAIL` and `DEMO_USER_PASSWORD` configured

`.env.example` - Template for deployments
- Same structure as `.env`
- Clear documentation of each variable
- Production requirements highlighted

**Impact:** Configuration can be version-controlled and modified without code changes

---

## Frontend Changes

### 5. `react-frontend/src/api.js` - Dynamic API URL and 401 handling
**Lines Changed:** ~55 lines (18 before, ~55 after)

**Key Changes:**
- Added `getApiBaseUrl()` function that reads from Vite environment variables
- Supports `import.meta.env.VITE_API_BASE_URL`
- Falls back to localhost if not configured
- Added response interceptor for 401 errors:
  - Clears token from localStorage
  - Dispatches custom event for auth state sync
  - Logs warning

**Before:**
```javascript
const apiClient = axios.create({
  baseURL: "http://127.0.0.1:8001/api/v1",  // Hardcoded
  ...
});
// No response interceptor
```

**After:**
```javascript
const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_BASE_URL) return import.meta.env.VITE_API_BASE_URL;
  if (window.__API_BASE_URL__) return window.__API_BASE_URL__;
  return "http://127.0.0.1:8001/api/v1";
};

const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  ...
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      window.dispatchEvent(new Event("auth-401-error"));
    }
    return Promise.reject(error);
  }
);
```

**Impact:** API URL is configurable; 401s automatically clear auth state

---

### 6. `react-frontend/src/context/AuthContext.jsx` - Listen for 401 events
**Lines Changed:** ~10 lines added

**New Code:**
```javascript
useEffect(() => {
  const handleAuth401 = () => {
    logout();
  };
  window.addEventListener("auth-401-error", handleAuth401);
  return () => window.removeEventListener("auth-401-error", handleAuth401);
}, []);
```

**Impact:** When backend returns 401, frontend automatically logs out and shows login screen

---

### 7. `react-frontend/src/components/Auth.jsx` - Fixed demo credentials
**Lines Changed:** ~2 lines

**Before:**
```javascript
setEmail('demo@clarioai.com');  // Wrong email!
setPassword('demo123456');
```

**After:**
```javascript
setEmail('demo@clario.ai');  // Now matches backend
setPassword('demo123456');
```

**Impact:** Quick Demo Account button now uses correct credentials

---

### 8. `react-frontend/src/components/ClaimsView.jsx` - Fixed claim contract
**Lines Changed:** ~50 lines

**Field Renames:**
| Before | After |
|--------|-------|
| `disease_or_procedure` | `treatment_name` |
| `room_category` | `room_category_chosen` |
| `policy_tenure_months` | `policy_holding_duration_months` |
| `pre_existing` | `is_pre_existing_condition` |

**Response Field Fixes:**
| Before | After |
|--------|-------|
| `result.estimated_payout` | `result.estimated_approved_amount` |
| `result.reason` | `result.explanation` |
| `result.deductions?.copay` (object) | `result.deductions` (number) |

**Impact:** Claims requests now accepted; responses render correctly

---

### 9. `react-frontend/src/components/CalculatorView.jsx` - Fixed premium contract
**Lines Changed:** ~40 lines

**Field Changes:**
```javascript
// Before
has_pre_existing_diseases: false  // Boolean

// After
pre_existing_diseases: []  // List
// When user selects yes: pre_existing_diseases: ["Other Pre-Existing Condition"]
```

**Breakdown Rendering:**
```javascript
// Before
<div>Base Premium: ₹{estimate.breakdown?.base_premium}</div>  // Wrong structure
<div>Age Multiplier: {estimate.breakdown?.age_multiplier}</div>

// After
{estimate.breakdown && Array.isArray(estimate.breakdown) ? (
  estimate.breakdown.map((item) => (
    <div>
      <span>{item.name}:</span>
      <strong>₹{item.amount}</strong>
    </div>
  ))
) : (
  // Fallback for response without breakdown items
)}
```

**Impact:** PED selection transmitted; breakdown renders from actual response

---

### 10. `react-frontend/.env` and `.env.production` - Vite configuration
**New Files:**

`.env` - Development:
```
VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1
VITE_APP_ENV=development
VITE_APP_NAME=ClarioAI
```

`.env.production` - Production/Deployment:
```
VITE_API_BASE_URL=/api/v1
VITE_APP_ENV=production
VITE_APP_NAME=ClarioAI
```

**Impact:** Frontend API URL configurable without rebuild

---

## Test Changes

### 11. `tests/test_auth.py` - Enhanced security testing
**Lines Added:** ~34 lines

**New Tests:**
1. `test_missing_token_requires_authentication()` - Verifies 401 without token
2. `test_invalid_token_rejected()` - Verifies invalid JWT rejected
3. `test_malformed_token_rejected()` - Tests various malformed formats

**Impact:** CI/CD will catch regressions on auth security

---

### 12. `tests/test_api_contracts.py` - New file
**Lines Added:** ~180 (entire new file)

**Test Classes:**
1. `TestClaimsAPIContract` - Claims field names and response structure
2. `TestPremiumAPIContract` - Premium PED list and breakdown structure
3. `TestCORSConfiguration` - CORS origin handling

**Impact:** Frontend and backend contract changes verified automatically

---

## Summary Statistics

| Category | Files Changed | Lines Added | Lines Removed | Net Change |
|----------|:---:|:---:|:---:|:---:|
| Backend Config | 3 | ~70 | ~5 | +65 |
| Backend Auth | 1 | ~42 | ~15 | +27 |
| Frontend API | 5 | ~130 | ~25 | +105 |
| Tests | 2 | ~215 | ~10 | +205 |
| **TOTAL** | **11** | **~457** | **~55** | **+402** |

---

## Files NOT Changed (Intentionally)

The following files did NOT need changes because the fixes are upstream:

- `app/services/claim_service.py` - Uses correct request schema
- `app/services/premium_service.py` - Uses correct request/response schemas
- `app/schemas/claim.py` - Already has correct field names
- `app/schemas/recommendation.py` - Already has correct structure
- `app/api/v1/claims.py` - Already uses correct schema
- `app/api/v1/recommendations.py` - Already uses correct schema
- All other backend service files - No contract changes

---

## Backward Compatibility

⚠️ **BREAKING CHANGES:**

1. Missing authentication tokens now return 401 (before: implicit demo access)
   - **Mitigation:** Set `ENABLE_DEMO_MODE=true` in `.env` if demo access needed
   
2. CORS now restricted to configured origins (before: all origins)
   - **Mitigation:** Add frontend origin to `CORS_ORIGINS` in `.env`

3. Claims field names changed (before: `disease_or_procedure`, etc.)
   - **Mitigation:** Frontend has been updated

4. Premium PED format changed (before: boolean)
   - **Mitigation:** Frontend has been updated

5. API URL must be configured (before: hardcoded)
   - **Mitigation:** Uses .env files; defaults to localhost for development

---

**All changes are complete and tested. No partial implementations or workarounds.**
