#!/usr/bin/env python3
"""Create enhanced white-label tables."""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text

from app.core.config import settings


def create_whitelabel_tables():
    """Create enhanced white-label tables."""
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        # Create whitelabel_domains table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS whitelabel_domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_id INTEGER NOT NULL,
                domain VARCHAR(255) NOT NULL UNIQUE,
                subdomain VARCHAR(100),
                ssl_enabled BOOLEAN DEFAULT 0,
                ssl_cert_path VARCHAR(500),
                dns_verified BOOLEAN DEFAULT 0,
                is_primary BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (config_id) REFERENCES whitelabel_configs (id)
            )
        """
            )
        )

        # Create whitelabel_themes table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS whitelabel_themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                css_variables JSON,
                custom_css TEXT,
                font_family VARCHAR(100) DEFAULT 'Inter, sans-serif',
                logo_variants JSON,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (config_id) REFERENCES whitelabel_configs (id)
            )
        """
            )
        )

        # Create whitelabel_assets table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS whitelabel_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_id INTEGER NOT NULL,
                asset_type VARCHAR(50) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_name VARCHAR(255) NOT NULL,
                file_size INTEGER,
                mime_type VARCHAR(100),
                cdn_url VARCHAR(500),
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (config_id) REFERENCES whitelabel_configs (id)
            )
        """
            )
        )

        # Create partner_features table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS partner_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER NOT NULL,
                feature_key VARCHAR(100) NOT NULL,
                is_enabled BOOLEAN DEFAULT 1,
                configuration JSON,
                usage_limit INTEGER,
                usage_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES users (id)
            )
        """
            )
        )

        # Add relationships to users table if not exists
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN partner_features TEXT"))
        except:
            pass

        conn.commit()
        print("✅ Enhanced white-label tables created successfully!")
        print("🎨 Features available:")
        print("- Multi-domain management")
        print("- Custom themes and CSS")
        print("- Asset management")
        print("- Partner feature toggles")


if __name__ == "__main__":
    create_whitelabel_tables()
