#!/usr/bin/env python3
"""
import os
import sqlite3
import sys
from datetime import datetime

Cancel pending SMS verifications and update timestamps
"""

# Add app directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def cancel_pending_verifications():

try:
        conn = sqlite3.connect("namaskah.db")
        cursor = conn.cursor()

        # Get current pending verifications
        cursor.execute(
            'SELECT id, status, created_at FROM verifications WHERE status = "pending"'
        )
        pending = cursor.fetchall()

        print(f"Found {len(pending)} pending verifications:")
for v in pending:
            print(f"  ID: {v[0]}, Status: {v[1]}, Created: {v[2]}")

if pending:
            # Cancel all pending verifications
            now = datetime.now().isoformat()
            cursor.execute(
                """
                UPDATE verifications
                SET status = "cancelled",
                    updated_at = ?,
                    cancelled_reason = "System cleanup - SMS service not configured"
                WHERE status = "pending"
            """,
                (now,),
            )

            print(f"\n✅ Cancelled {cursor.rowcount} pending verifications")
            print(f"   Updated timestamp: {now}")

            conn.commit()
else:
            print("No pending verifications found")

except Exception as e:
        print(f"❌ Error: {e}")
finally:
        conn.close()


if __name__ == "__main__":
    cancel_pending_verifications()