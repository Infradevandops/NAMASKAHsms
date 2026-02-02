#!/usr/bin/env python3
"""Generate secure keys for production deployment."""


import secrets

def generate_key(length=32):

    """Generate a secure random key."""
    return secrets.token_urlsafe(length)


if __name__ == "__main__":
    print("=" * 60)
    print("SECURE KEYS FOR PRODUCTION")
    print("=" * 60)
    print("\nAdd these to your production environment variables:\n")
    print(f"SECRET_KEY={generate_key(32)}")
    print(f"JWT_SECRET_KEY={generate_key(32)}")
    print("\n" + "=" * 60)
    print("⚠️  IMPORTANT: Keep these keys secure and never commit them!")
    print("=" * 60)