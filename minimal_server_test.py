#!/usr/bin/env python3
"""Minimal server test."""

import os
os.environ['DATABASE_URL'] = 'sqlite:///./sms.db'

from fastapi import FastAPI
from app.api.auth_consolidated import router as auth_router

# Create minimal app
app = FastAPI(title="Test Auth")
app.include_router(auth_router)

if __name__ == "__main__":
    import uvicorn
    print("Starting minimal test server...")
    uvicorn.run(app, host="0.0.0.0", port=9528, log_level="info")
