"""Startup initialization for the application."""

import os

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.database import SessionLocal, engine
from app.core.logging import get_logger
from app.models.user import User
from app.utils.security import hash_password

logger = get_logger("startup")


def ensure_subscription_tiers_table():
    """Ensure subscription_tiers table exists with all tier definitions."""
    try:
        with engine.connect() as conn:
            # Create subscription_tiers table
            logger.info("Checking subscription_tiers table...")
            conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS subscription_tiers (
                    id TEXT PRIMARY KEY,
                    tier TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    price_monthly INTEGER NOT NULL,
                    quota_usd DECIMAL(10, 2) NOT NULL,
                    overage_rate DECIMAL(10, 2) NOT NULL,
                    has_api_access BOOLEAN DEFAULT FALSE,
                    has_area_code_selection BOOLEAN DEFAULT FALSE,
                    has_isp_filtering BOOLEAN DEFAULT FALSE,
                    api_key_limit INTEGER DEFAULT 0,
                    support_level TEXT DEFAULT 'community',
                    payment_required BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
                )
            )
            conn.commit()

            # Insert/update tier definitions
            tiers = [
                (
                    "tier_freemium",
                    "freemium",
                    "Freemium",
                    0,
                    False,
                    0,
                    2.22,
                    False,
                    False,
                    False,
                    0,
                    "community",
                ),
                (
                    "tier_payg",
                    "payg",
                    "Pay-As-You-Go",
                    0,
                    False,
                    0,
                    2.50,
                    True,
                    True,
                    False,
                    5,
                    "community",
                ),
                (
                    "tier_pro",
                    "pro",
                    "Pro",
                    2500,
                    True,
                    30.00,
                    2.20,
                    True,
                    True,
                    True,
                    10,
                    "priority",
                ),
                (
                    "tier_custom",
                    "custom",
                    "Custom",
                    3500,
                    True,
                    50.00,
                    2.10,
                    True,
                    True,
                    True,
                    -1,
                    "dedicated",
                ),
            ]

            for tier_data in tiers:
                conn.execute(
                    text(
                        """
                    INSERT INTO subscription_tiers
                    (id, tier, name, price_monthly, payment_required, quota_usd, overage_rate,
                     has_api_access, has_area_code_selection, has_isp_filtering,
                     api_key_limit, support_level)
                    VALUES
                    (:id, :tier, :name, :price_monthly, :payment_required, :quota_usd, :overage_rate,
                     :has_api_access, :has_area_code_selection, :has_isp_filtering,
                     :api_key_limit, :support_level)
                    ON CONFLICT (tier) DO UPDATE SET
                        name = EXCLUDED.name,
                        price_monthly = EXCLUDED.price_monthly,
                        payment_required = EXCLUDED.payment_required,
                        quota_usd = EXCLUDED.quota_usd,
                        overage_rate = EXCLUDED.overage_rate,
                        has_api_access = EXCLUDED.has_api_access,
                        has_area_code_selection = EXCLUDED.has_area_code_selection,
                        has_isp_filtering = EXCLUDED.has_isp_filtering,
                        api_key_limit = EXCLUDED.api_key_limit,
                        support_level = EXCLUDED.support_level,
                        updated_at = CURRENT_TIMESTAMP;
                """
                    ),
                    {
                        "id": tier_data[0],
                        "tier": tier_data[1],
                        "name": tier_data[2],
                        "price_monthly": tier_data[3],
                        "payment_required": tier_data[4],
                        "quota_usd": tier_data[5],
                        "overage_rate": tier_data[6],
                        "has_api_access": tier_data[7],
                        "has_area_code_selection": tier_data[8],
                        "has_isp_filtering": tier_data[9],
                        "api_key_limit": tier_data[10],
                        "support_level": tier_data[11],
                    },
                )

            conn.commit()
            logger.info("Subscription tiers table initialized successfully")
    except Exception as e:
        logger.warning(f"Subscription tiers initialization failed: {e}")


def ensure_database_schema():
    """Ensure database has all required columns."""
    try:
        with engine.connect() as conn:
            # Add ALL missing columns from User model
            columns_to_add = [
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS bonus_sms_balance FLOAT DEFAULT 0.0",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS monthly_quota_used FLOAT DEFAULT 0.0",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS monthly_quota_reset_date TIMESTAMP",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en'",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'USD'",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_suspended BOOLEAN DEFAULT FALSE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS suspended_at TIMESTAMP",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS suspension_reason VARCHAR(500)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS banned_at TIMESTAMP",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS ban_reason VARCHAR(500)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS deletion_reason VARCHAR(500)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_start_date TIMESTAMP",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS affiliate_id VARCHAR(50)",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS partner_type VARCHAR(20) DEFAULT 'standard'",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS commission_tier VARCHAR(20) DEFAULT 'standard'",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_affiliate BOOLEAN DEFAULT FALSE",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_earnings DECIMAL(10, 2) DEFAULT 0.0",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP",
                "ALTER TABLE subscription_tiers ADD COLUMN IF NOT EXISTS description VARCHAR(500)",
                "ALTER TABLE subscription_tiers ADD COLUMN IF NOT EXISTS payment_required BOOLEAN DEFAULT FALSE",
                "ALTER TABLE subscription_tiers ADD COLUMN IF NOT EXISTS daily_verification_limit INTEGER DEFAULT -1",
                "ALTER TABLE subscription_tiers ADD COLUMN IF NOT EXISTS monthly_verification_limit INTEGER DEFAULT -1",
                "ALTER TABLE subscription_tiers ADD COLUMN IF NOT EXISTS country_limit TEXT DEFAULT 'all'",
                "ALTER TABLE subscription_tiers ADD COLUMN IF NOT EXISTS sms_retention_days INTEGER DEFAULT 7",
                "ALTER TABLE subscription_tiers ADD COLUMN IF NOT EXISTS features TEXT",
                "ALTER TABLE subscription_tiers ADD COLUMN IF NOT EXISTS rate_limit_per_minute INTEGER DEFAULT 60",
                "ALTER TABLE subscription_tiers ADD COLUMN IF NOT EXISTS rate_limit_per_hour INTEGER DEFAULT 1000",
            ]

            for sql in columns_to_add:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                except Exception as e:
                    logger.debug(f"Column may already exist: {e}")

            logger.info("Database schema verified")
    except Exception as e:
        logger.warning(f"Schema check failed: {e}")


def ensure_admin_user():
    """Ensure admin user exists on startup."""
    db = SessionLocal()
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@namaskah.app")
        admin_password = os.getenv("ADMIN_PASSWORD")

        logger.info(f"🔐 Admin user check starting for: {admin_email}")

        if not admin_password:
            logger.warning("⚠️ ADMIN_PASSWORD not set in environment. Skipping admin user creation.")
            logger.warning("⚠️ Set ADMIN_PASSWORD environment variable to enable admin access.")
            return

        logger.info(f"✅ ADMIN_PASSWORD found (length: {len(admin_password)} chars)")

        # Check if admin exists
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if existing_admin:
            logger.info(f"👤 Admin user exists: {admin_email} (ID: {existing_admin.id})")

            # ALWAYS update password on startup to ensure it matches env var
            old_hash_preview = existing_admin.password_hash[:30] if existing_admin.password_hash else "None"
            existing_admin.password_hash = hash_password(admin_password)
            new_hash_preview = existing_admin.password_hash[:30]

            existing_admin.is_admin = True
            existing_admin.email_verified = True
            existing_admin.subscription_tier = "custom"
            existing_admin.credits = max(existing_admin.credits or 0, 10000.0)
            existing_admin.is_active = True
            existing_admin.is_suspended = False
            existing_admin.is_banned = False

            db.commit()

            logger.info("✅ Admin user updated successfully")
            logger.info(f"   Email: {admin_email}")
            logger.info(f"   Tier: {existing_admin.subscription_tier}")
            logger.info(f"   Credits: {existing_admin.credits}")
            logger.info(f"   Old hash: {old_hash_preview}...")
            logger.info(f"   New hash: {new_hash_preview}...")
            logger.info(f"   Password length: {len(admin_password)} chars")

            # Verify the password works
            from app.utils.security import verify_password

            if verify_password(admin_password, existing_admin.password_hash):
                logger.info("✅ Password verification successful!")
            else:
                logger.error("❌ Password verification FAILED after update!")

            return

        # Create admin user with custom tier access
        logger.info(f"🆕 Creating new admin user: {admin_email}")

        admin_user = User(
            email=admin_email,
            password_hash=hash_password(admin_password),
            credits=10000.0,
            is_admin=True,
            email_verified=True,
            free_verifications=1000.0,
            subscription_tier="custom",
            is_active=True,
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        logger.info("✅ Admin user created successfully")
        logger.info(f"   Email: {admin_email}")
        logger.info(f"   ID: {admin_user.id}")
        logger.info(f"   Tier: {admin_user.subscription_tier}")
        logger.info(f"   Credits: {admin_user.credits}")
        logger.info(f"   Hash: {admin_user.password_hash[:30]}...")

        # Verify the password works
        from app.utils.security import verify_password

        if verify_password(admin_password, admin_user.password_hash):
            logger.info("✅ Password verification successful!")
        else:
            logger.error("❌ Password verification FAILED after creation!")

    except IntegrityError as e:
        logger.warning(f"⚠️ Admin user creation failed - user may already exist: {e}")
        db.rollback()
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error creating admin user: {e}")
        db.rollback()
    except Exception as e:
        logger.error(f"❌ Unexpected error in ensure_admin_user: {e}")
        import traceback

        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def run_startup_initialization():
    """Run all startup initialization tasks."""
    logger.info("Running startup initialization")

    try:
        ensure_subscription_tiers_table()  # Create tiers table first
        ensure_database_schema()
        ensure_admin_user()
        logger.info("Startup initialization completed")
    except SQLAlchemyError as e:
        logger.error(f"Database error during startup initialization: {e}")
    except OSError as e:
        logger.error(f"Environment configuration error during startup: {e}")
    except (ImportError, AttributeError, TypeError) as e:
        logger.error(f"Configuration or import error during startup initialization: {e}")
    except Exception as e:
        logger.critical(f"Critical unexpected error during startup initialization: {e}")
        raise
