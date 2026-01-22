"""Add database indexes for performance optimization"""

from sqlalchemy import create_engine, text

from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)


def add_indexes():
    """Add indexes to improve query performance"""
    with engine.connect() as conn:
        print("Adding indexes...")

        # Verifications indexes
        try:
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_verifications_user_id ON verifications(user_id)"
                )
            )
            print("✅ Created idx_verifications_user_id")
        except Exception as e:
            print(f"⚠️  idx_verifications_user_id: {e}")

        try:
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_verifications_status ON verifications(status)"
                )
            )
            print("✅ Created idx_verifications_status")
        except Exception as e:
            print(f"⚠️  idx_verifications_status: {e}")

        try:
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_verifications_created_at ON verifications(created_at DESC)"
                )
            )
            print("✅ Created idx_verifications_created_at")
        except Exception as e:
            print(f"⚠️  idx_verifications_created_at: {e}")

        try:
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_verifications_user_status ON verifications(user_id, status)"
                )
            )
            print("✅ Created idx_verifications_user_status")
        except Exception as e:
            print(f"⚠️  idx_verifications_user_status: {e}")

        # Transactions indexes
        try:
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)"
                )
            )
            print("✅ Created idx_transactions_user_id")
        except Exception as e:
            print(f"⚠️  idx_transactions_user_id: {e}")

        try:
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at DESC)"
                )
            )
            print("✅ Created idx_transactions_created_at")
        except Exception as e:
            print(f"⚠️  idx_transactions_created_at: {e}")

        conn.commit()
        print("\n✅ All indexes created successfully!")


if __name__ == "__main__":
    add_indexes()
