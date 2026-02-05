#!/usr/bin/env python3
"""Test the authentication fix."""

import os
import requests
import time
import subprocess
import signal
import sys

def test_auth():
    """Test authentication system."""
    
    # Set the correct database URL
    os.environ['DATABASE_URL'] = 'sqlite:///./sms.db'
    
    print("🧪 Testing Authentication Fix...")
    
    # Start server in background
    print("Starting server...")
    server_process = subprocess.Popen([
        'python3', '-c', 
        '''
import os
os.environ["DATABASE_URL"] = "sqlite:///./sms.db"
from main import app
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=9527, log_level="error")
        '''
    ])
    
    # Wait for server to start
    time.sleep(5)
    
    try:
        # Test login
        response = requests.post(
            "http://localhost:9527/api/auth/login",
            json={"email": "admin@namaskah.app", "password": "admin123"},
            timeout=10
        )
        
        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Authentication fix successful!")
            data = response.json()
            print(f"   Token: {data.get('access_token', 'N/A')[:20]}...")
            print(f"   User: {data.get('user', {}).get('email', 'N/A')}")
        else:
            print("❌ Authentication still failing")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        # Clean up
        print("Stopping server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    test_auth()
