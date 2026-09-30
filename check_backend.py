#!/usr/bin/env python3
"""
Diagnostic script to check if ClarioAI backend can start successfully.
Run this from the clarioAI directory: python check_backend.py
"""

import sys
import os

print("🔍 ClarioAI Backend Diagnostics\n")

# Check 1: Python version
print(f"✓ Python version: {sys.version.split()[0]}")

# Check 2: Required packages
print("\n📦 Checking required packages...")
try:
    import fastapi
    print(f"✓ FastAPI: {fastapi.__version__}")
except ImportError:
    print("✗ FastAPI not installed")
    sys.exit(1)

try:
    import sqlalchemy
    print(f"✓ SQLAlchemy: {sqlalchemy.__version__}")
except ImportError:
    print("✗ SQLAlchemy not installed")
    sys.exit(1)

try:
    import pydantic_settings
    print("✓ Pydantic Settings installed")
except ImportError:
    print("✗ Pydantic Settings not installed")
    sys.exit(1)

# Check 3: Configuration
print("\n⚙️  Checking configuration...")
try:
    from app.config import settings
    print(f"✓ Configuration loaded")
    print(f"  - Environment: {settings.ENVIRONMENT}")
    print(f"  - Database: {settings.DATABASE_URL}")
    print(f"  - API V1 Prefix: {settings.API_V1_STR}")
    print(f"  - Demo Mode: {settings.ENABLE_DEMO_MODE}")
    print(f"  - CORS Origins: {settings.CORS_ORIGINS}")
    print(f"  - SECRET_KEY: {'Set' if settings.SECRET_KEY else 'Not set (using dev default)'}")
except Exception as e:
    print(f"✗ Configuration error: {e}")
    sys.exit(1)

# Check 4: Database
print("\n🗄️  Checking database...")
try:
    from app.database import init_db, SessionLocal, engine
    from sqlalchemy import text
    
    # Try to connect
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"✓ Database connection successful")
    
    # Initialize schema
    init_db()
    print(f"✓ Database schema initialized")
except Exception as e:
    print(f"✗ Database error: {e}")
    print(f"  Database URL: {settings.DATABASE_URL}")
    sys.exit(1)

# Check 5: App initialization
print("\n🚀 Checking app initialization...")
try:
    from app.main import app
    print(f"✓ FastAPI app loaded")
    print(f"  - Title: {app.title}")
    print(f"  - Version: {app.version}")
    print(f"  - Docs: http://127.0.0.1:8001/docs")
except Exception as e:
    print(f"✗ App initialization error: {e}")
    sys.exit(1)

# Check 6: Routes
print("\n🛣️  Checking routes...")
try:
    routes_count = len([r for r in app.routes if hasattr(r, 'path')])
    print(f"✓ {routes_count} routes registered")
    
    # Check critical endpoints
    auth_routes = [r for r in app.routes if hasattr(r, 'path') and '/auth' in r.path]
    print(f"  - Auth endpoints: {len(auth_routes)}")
    
    api_routes = [r for r in app.routes if hasattr(r, 'path') and '/api/v1' in r.path]
    print(f"  - API v1 endpoints: {len(api_routes)}")
except Exception as e:
    print(f"⚠️  Could not enumerate routes: {e}")

print("\n" + "="*50)
print("✅ Backend diagnostics passed!")
print("\nYou can now start the backend with:")
print("  python -m uvicorn app.main:app --reload")
print("\nOr:")
print("  uvicorn app.main:app --reload")
print("\nThe API will be available at:")
print("  http://127.0.0.1:8001/api/v1")
print("="*50)
