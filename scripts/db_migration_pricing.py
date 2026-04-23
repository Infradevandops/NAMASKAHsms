"""Migration script for Admin Pricing Management."""

import os
import sys
from sqlalchemy import text, create_engine
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_migration():
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL not found in .env")
        return

    print(f"Connecting to database: {database_url.split('@')[0]}@...")
    engine = create_engine(database_url)

    with engine.connect() as conn:
        print("Connected successfully.")

        # 1. Create PriceSnapshot table
        print("Creating price_snapshots table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS price_snapshots (
                id VARCHAR PRIMARY KEY,
                service_id VARCHAR(100) NOT NULL,
                service_name VARCHAR(255) NOT NULL,
                provider_cost DECIMAL(10, 4) NOT NULL,
                platform_price DECIMAL(10, 4) NOT NULL,
                markup_percentage DECIMAL(5, 2) NOT NULL,
                currency VARCHAR(3) DEFAULT 'USD',
                captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                source VARCHAR(50) DEFAULT 'textverified',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            );
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_price_snapshots_service ON price_snapshots(service_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_price_snapshots_captured ON price_snapshots(captured_at DESC);"))

        # 2. Create AdminNotification table
        print("Creating admin_notifications table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS admin_notifications (
                id VARCHAR PRIMARY KEY,
                admin_id VARCHAR,
                notification_type VARCHAR(50) NOT NULL,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                severity VARCHAR(20) DEFAULT 'info',
                is_read BOOLEAN DEFAULT FALSE,
                metadata_json JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            );
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_admin_notifications_type ON admin_notifications(notification_type);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_admin_notifications_is_read ON admin_notifications(is_read);"))

        # 3. Enhance pricing_templates table
        print("Enhancing pricing_templates table...")
        
        # Check existing columns to avoid errors
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'pricing_templates';
        """))
        existing_cols = [row[0] for row in result]

        new_cols = [
            ("markup_multiplier", "DECIMAL(10, 4) DEFAULT 1.1000"),
            ("is_promotional", "BOOLEAN DEFAULT FALSE"),
            ("discount_percentage", "DECIMAL(5, 2) DEFAULT 0.00"),
            ("applies_to_services", "JSONB")
        ]

        for col_name, col_type in new_cols:
            if col_name not in existing_cols:
                print(f"Adding column {col_name} to pricing_templates...")
                conn.execute(text(f"ALTER TABLE pricing_templates ADD COLUMN {col_name} {col_type};"))
            else:
                print(f"Column {col_name} already exists in pricing_templates.")

        conn.commit()
        print("Migration completed successfully.")

if __name__ == "__main__":
    run_migration()
