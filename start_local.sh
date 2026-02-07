#!/bin/bash
export DATABASE_URL="sqlite:///./namaskah_local.db"
export SECRET_KEY="local-dev-secret-key-1234567890abcdefghijklmnop"
export JWT_SECRET_KEY="local-jwt-secret-key-67890abcdefghijklmnopqrst"
export ADMIN_EMAIL="admin@namaskah.app"
export ADMIN_PASSWORD="admin123"
export ENVIRONMENT="development"

source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
