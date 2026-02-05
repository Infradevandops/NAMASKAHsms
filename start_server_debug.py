#!/usr/bin/env python3
"""Debug server startup."""

import os
import sys

# Set the correct database URL
os.environ['DATABASE_URL'] = 'sqlite:///./sms.db'

try:
    print("🔧 Starting server with debug info...")
    print(f"Database URL: {os.environ.get('DATABASE_URL')}")
    
    # Test database connection first
    from app.core.database import get_db, test_database_connection
    db_status = test_database_connection()
    print(f"Database status: {db_status}")
    
    # Test user query
    from app.models.user import User
    db = next(get_db())
    user_count = db.query(User).count()
    print(f"Users in database: {user_count}")
    
    # Start server
    from main import app
    import uvicorn
    
    print("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=9527, log_level="info")
    
except Exception as e:
    print(f"❌ Server startup failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
