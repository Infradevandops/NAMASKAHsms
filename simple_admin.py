#!/usr/bin/env python3
"""Simple admin user creation for local testing."""

import sqlite3

from app.utils.security import hash_password


def create_admin():
    conn = sqlite3.connect("test_sms.db")
    cursor = conn.cursor()

    # Check if admin exists
    cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@test.com",))
    if cursor.fetchone():
        print("Admin user already exists")
        return

    # Create admin user
    hashed_pw = hash_password("admin123")
    cursor.execute(
        """
        INSERT INTO users (email, username, hashed_password, is_active, is_admin, is_verified)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        ("admin@test.com", "admin", hashed_pw, True, True, True),
    )

    conn.commit()
    conn.close()
    print("✅ Admin user created: admin@test.com / admin123")


if __name__ == "__main__":
    create_admin()
