"""White - label platform service."""
from typing import Dict, Optional
from app.models.whitelabel import WhiteLabelConfig


class WhiteLabelService:
    """White - label platform management."""

    async def get_config_by_domain(self, domain: str) -> Optional[Dict]:
        """Get white - label config by domain."""
        db = next(get_db())

        try:
            config = db.query(WhiteLabelConfig).filter(
                WhiteLabelConfig.domain == domain,
                WhiteLabelConfig.is_active
            ).first()
        except Exception:
            # Table doesn't exist, return None
            return None

        if not config:
            return None

        return {
            "company_name": config.company_name,
            "logo_url": config.logo_url,
            "primary_color": config.primary_color,
            "secondary_color": config.secondary_color,
            "custom_css": config.custom_css,
            "features": config.features
        }

    async def create_config(self, domain: str, config_data: Dict) -> Dict:
        """Create new white - label configuration."""
        db = next(get_db())

        config = WhiteLabelConfig(
            domain=domain,
            company_name=config_data["company_name"],
            logo_url=config_data.get("logo_url"),
            primary_color=config_data.get("primary_color", "#667eea"),
            secondary_color=config_data.get("secondary_color", "#10b981"),
            custom_css=config_data.get("custom_css"),
            api_subdomain=config_data.get("api_subdomain"),
            features=config_data.get("features", {
                "sms": True, "whatsapp": True, "telegram": True, "analytics": True
            })
        )

        db.add(config)
        db.commit()

        return {"success": True, "domain": domain}


# Global service instance
whitelabel_service = WhiteLabelService()
