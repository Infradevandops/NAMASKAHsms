"""Enhanced white-label service with advanced features."""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.whitelabel import WhiteLabelConfig
from app.models.whitelabel_enhanced import (WhiteLabelAsset, WhiteLabelDomain,
                                            WhiteLabelTheme)


class WhiteLabelEnhancedService:
    """Enhanced white-label platform management."""

    def __init__(self, db: Session):
        self.db = db

    async def setup_complete_whitelabel(
        self,
        partner_id: int,
        domain: str,
        company_name: str,
        branding_config: Dict
    ) -> Dict:
        """Complete white-label setup wizard."""

        # Create main config
        config = WhiteLabelConfig(
            domain=domain,
            company_name=company_name,
            logo_url=branding_config.get("logo_url"),
            primary_color=branding_config.get("primary_color", "#667eea"),
            secondary_color=branding_config.get("secondary_color", "#10b981"),
            custom_css=branding_config.get("custom_css"),
            api_subdomain=branding_config.get("api_subdomain"),
            features=branding_config.get("features", {
                "sms": True, "whatsapp": True, "telegram": True, "analytics": True
            })
        )

        self.db.add(config)
        self.db.flush()  # Get ID

        # Create domain entry
        domain_entry = WhiteLabelDomain(
            config_id=config.id,
            domain=domain,
            subdomain=branding_config.get("api_subdomain"),
            is_primary=True
        )

        self.db.add(domain_entry)

        # Create default theme
        theme = WhiteLabelTheme(
            config_id=config.id,
            name="Default Theme",
            css_variables={
                "--primary-color": branding_config.get("primary_color", "#667eea"),
                "--secondary-color": branding_config.get("secondary_color", "#10b981"),
                "--font-family": branding_config.get("font_family", "Inter, sans-serif"),
                "--border-radius": "8px",
                "--shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"
            },
            custom_css=branding_config.get("custom_css"),
            is_active=True
        )

        self.db.add(theme)
        self.db.commit()

        return {
            "success": True,
            "config_id": config.id,
            "domain": domain,
            "setup_complete": True
        }

    async def update_branding(self, config_id: int, branding_data: Dict) -> Dict:
        """Update complete branding configuration."""

        config = self.db.query(WhiteLabelConfig).filter(
            WhiteLabelConfig.id == config_id
        ).first()

        if not config:
            raise ValueError("Configuration not found")

        # Update main config
        config.company_name = branding_data.get("company_name", config.company_name)
        config.logo_url = branding_data.get("logo_url", config.logo_url)
        config.primary_color = branding_data.get("primary_color", config.primary_color)
        config.secondary_color = branding_data.get("secondary_color", config.secondary_color)
        config.custom_css = branding_data.get("custom_css", config.custom_css)

        # Update theme
        theme = self.db.query(WhiteLabelTheme).filter(
            WhiteLabelTheme.config_id == config_id,
            WhiteLabelTheme.is_active == True
        ).first()

        if theme:
            theme.css_variables.update({
                "--primary-color": branding_data.get("primary_color", config.primary_color),
                "--secondary-color": branding_data.get("secondary_color", config.secondary_color),
                "--font-family": branding_data.get("font_family", "Inter, sans-serif")
            })
            theme.custom_css = branding_data.get("custom_css")

        self.db.commit()

        return {"success": True, "updated": True}

    async def verify_domain(self, domain: str) -> Dict:
        """Verify domain ownership."""

        domain_entry = self.db.query(WhiteLabelDomain).filter(
            WhiteLabelDomain.domain == domain
        ).first()

        if not domain_entry:
            return {"error": "Domain not found"}

        # Simple verification (in production, implement DNS TXT record check)
        verification_token = f"namaskah-verify-{domain_entry.id}"

        # For now, mark as verified (implement actual DNS verification)
        domain_entry.dns_verified = True
        self.db.commit()

        return {
            "verified": True,
            "verification_token": verification_token,
            "instructions": f"Add TXT record: {verification_token}"
        }

    async def get_partner_config(self, domain: str) -> Optional[Dict]:
        """Get complete partner configuration by domain."""

        config = self.db.query(WhiteLabelConfig).filter(
            WhiteLabelConfig.domain == domain,
            WhiteLabelConfig.is_active == True
        ).first()

        if not config:
            return None

        # Get theme
        theme = self.db.query(WhiteLabelTheme).filter(
            WhiteLabelTheme.config_id == config.id,
            WhiteLabelTheme.is_active == True
        ).first()

        # Get assets
        assets = self.db.query(WhiteLabelAsset).filter(
            WhiteLabelAsset.config_id == config.id,
            WhiteLabelAsset.is_active == True
        ).all()

        return {
            "company_name": config.company_name,
            "logo_url": config.logo_url,
            "primary_color": config.primary_color,
            "secondary_color": config.secondary_color,
            "custom_css": config.custom_css,
            "features": config.features,
            "theme": {
                "name": theme.name if theme else "Default",
                "css_variables": theme.css_variables if theme else {},
                "custom_css": theme.custom_css if theme else None,
                "font_family": theme.font_family if theme else "Inter, sans-serif"
            },
            "assets": [
                {
                    "type": asset.asset_type,
                    "url": asset.cdn_url or asset.file_path,
                    "name": asset.file_name
                }
                for asset in assets
            ]
        }

    async def generate_custom_css(self, config_id: int) -> str:
        """Generate complete custom CSS for partner."""

        theme = self.db.query(WhiteLabelTheme).filter(
            WhiteLabelTheme.config_id == config_id,
            WhiteLabelTheme.is_active == True
        ).first()

        if not theme:
            return ""

        css_vars = theme.css_variables or {}
        custom_css = theme.custom_css or ""

        # Generate CSS with variables
        generated_css = ":root {\n"
        for key, value in css_vars.items():
            generated_css += f"  {key}: {value};\n"
        generated_css += "}\n\n"

        # Add custom CSS
        if custom_css:
            generated_css += custom_css

        # Add responsive design
        generated_css += """
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .card { margin: 10px 0; }
        }
        """

        return generated_css

    async def create_pwa_manifest(self, config_id: int) -> Dict:
        """Generate PWA manifest for partner."""

        config = self.db.query(WhiteLabelConfig).filter(
            WhiteLabelConfig.id == config_id
        ).first()

        if not config:
            return {}

        return {
            "name": f"{config.company_name} SMS Platform",
            "short_name": config.company_name,
            "description": f"SMS verification platform by {config.company_name}",
            "start_url": "/",
            "display": "standalone",
            "background_color": config.primary_color,
            "theme_color": config.primary_color,
            "icons": [
                {
                    "src": config.logo_url or "/static/icons/icon-192x192.png",
                    "sizes": "192x192",
                    "type": "image/png"
                }
            ]
        }


# Global service instance
whitelabel_enhanced_service = None


def get_whitelabel_enhanced_service(db: Session) -> WhiteLabelEnhancedService:
    """Get enhanced white-label service instance."""
    return WhiteLabelEnhancedService(db)
