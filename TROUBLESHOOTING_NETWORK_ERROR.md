# Quick Troubleshooting: Network Error Fix

## Problem
```
Auth error: AxiosError: Network Error
    at async Object.register (api.js:60:22)
    at async register (AuthContext.jsx:64:21)
    at async handleSubmit (Auth.jsx:29:9)
```

This means the frontend **cannot connect to the backend**.

---

## Solution: Start Backend First

### Step 1: Check Backend Status
Open a terminal in the `clarioAI` directory and run the diagnostic:

```bash
python check_backend.py
```

**Expected output:**
```
🔍 ClarioAI Backend Diagnostics

✓ Python version: 3.x.x
✓ FastAPI: 0.x.x
✓ SQLAlchemy: 2.x.x
✓ Pydantic Settings installed

✓ Configuration loaded
  - Environment: development
  - Database: sqlite:///./health_insurance.db
  ...

✓ Database connection successful
✓ Database schema initialized
✓ FastAPI app loaded
✓ [n] routes registered

✅ Backend diagnostics passed!
```

If you get errors, address them before continuing.

---

### Step 2: Start the Backend

In the **clarioAI** directory (terminal 1):

```bash
python -m uvicorn app.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Initializing Health Insurance Assistant Backend...
INFO:     Application startup complete.
```

**Do NOT proceed until you see "Application startup complete"**

---

### Step 3: Start the Frontend

In the **clarioAI/react-frontend** directory (terminal 2):

```bash
npm run dev
```

**Expected output:**
```
  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to access from other machines
```

---

### Step 4: Test the Connection

1. Open browser to **http://localhost:5173**
2. Fill in the registration form
3. Click "Create Account"
4. Should succeed (or show validation error, not network error)

---

## Verification Checklist

- [ ] Backend starts without errors (run `python check_backend.py`)
- [ ] Backend is running on `http://127.0.0.1:8001` (check terminal output)
- [ ] Frontend is running on `http://localhost:5173` (check terminal output)
- [ ] No CORS errors in browser console (F12 → Console tab)
- [ ] Network tab shows requests to `/api/v1/auth/register` are **200 or 422** (not connection error)

---

## If Still Getting Network Error

### Check 1: Backend URL
Open browser console (F12) and run:
```javascript
import.meta.env.VITE_API_BASE_URL
// Should output: http://127.0.0.1:8001/api/v1
```

If it shows something else, check `.env` file in `react-frontend/`.

### Check 2: Firewall/Port
Make sure port 8001 is accessible:
```bash
# On Windows (PowerShell)
Test-NetConnection -ComputerName 127.0.0.1 -Port 8001

# On Mac/Linux
nc -zv 127.0.0.1 8001
```

Should show: **Connection successful** (not refused)

### Check 3: Backend Process
Verify backend is actually running:
```bash
# On Windows (PowerShell)
Get-Process | grep uvicorn

# On Mac/Linux
ps aux | grep uvicorn
```

Should show one process running with `uvicorn app.main:app`

### Check 4: Error in Backend Terminal
Look at the backend terminal for any errors. If you see:
```
ValueError: SECRET_KEY must be set to a strong value in production
```

**Fix:** Ensure `.env` has:
```
ENVIRONMENT=development
```

(It should be set to "development" by default)

---

## Environment Variables

Make sure these files exist and are configured:

**Backend: `clarioAI/.env`**
```
ENVIRONMENT=development
ENABLE_DEMO_MODE=false
SECRET_KEY=dev-secret-key-change-in-production-policybazaar-ai
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DATABASE_URL=sqlite:///./health_insurance.db
```

**Frontend: `clarioAI/react-frontend/.env`**
```
VITE_API_BASE_URL=http://127.0.0.1:8001/api/v1
```

---

## Still Not Working?

1. **Kill processes:**
   - Close both terminals (Ctrl+C)
   - Wait 5 seconds

2. **Clear cache:**
   - Delete `clarioAI/__pycache__/` and `clarioAI/app/__pycache__/`
   - Delete `node_modules/.vite/` (browser cache)

3. **Fresh start:**
   - Start backend first: `python -m uvicorn app.main:app --reload`
   - Wait for "Application startup complete"
   - Then start frontend: `npm run dev`

4. **Check browser console:**
   - F12 → Console tab
   - Copy exact error message
   - Search error on Stack Overflow or GitHub issues

---

**Last Updated:** 2026-09-23
