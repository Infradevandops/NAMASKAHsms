from unittest.mock import MagicMock

import pytest

from app.models.whitelabel import WhiteLabelConfig
from app.models.whitelabel_enhanced import (
    WhiteLabelAsset,
    WhiteLabelDomain,
    WhiteLabelTheme,
)
from app.services.whitelabel_enhanced import WhiteLabelEnhancedService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return WhiteLabelEnhancedService(mock_db)


@pytest.mark.asyncio
async def test_setup_complete_whitelabel(service, mock_db):
    branding = {
        "logo_url": "http://logo.com",
        "primary_color": "#000",
        "features": {"sms": True},
    }

    result = await service.setup_complete_whitelabel(
        partner_id=1,
        domain="partner.com",
        company_name="Partner Inc",
        branding_config=branding,
    )

    assert result["success"] is True
    assert result["domain"] == "partner.com"

    # Check Adds: Config, Domain, Theme
    assert mock_db.add.call_count == 3
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_update_branding(service, mock_db):
    config = WhiteLabelConfig(id=1, company_name="Old", primary_color="#fff")
    theme = WhiteLabelTheme(config_id=1, is_active=True, css_variables={})

    mock_db.query.return_value.filter.return_value.first.side_effect = [config, theme]

    result = await service.update_branding(config_id=1, branding_data={"company_name": "New", "primary_color": "#000"})

    assert result["success"] is True
    assert config.company_name == "New"
    assert config.primary_color == "#000"
    assert theme.css_variables["--primary - color"] == "#000"
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_verify_domain_success(service, mock_db):
    domain_entry = WhiteLabelDomain(id=5, domain="test.com", dns_verified=False)
    mock_db.query.return_value.filter.return_value.first.return_value = domain_entry

    result = await service.verify_domain("test.com")

    assert result["verified"] is True
    assert domain_entry.dns_verified is True
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_verify_domain_not_found(service, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None
    result = await service.verify_domain("unknown.com")
    assert "error" in result


@pytest.mark.asyncio
async def test_get_partner_config(service, mock_db):
    config = WhiteLabelConfig(id=1, company_name="Co", features={})
    theme = WhiteLabelTheme(name="Theme")
    asset = WhiteLabelAsset(file_name="Logo", asset_type="image")

    # Mock chain
    # 1. Config
    # 2. Theme
    # 3. Assets (all())

    # Need to separate query chains
    # query(Config)
    # query(Theme)
    # query(Asset)

    # This is hard with simple side_effect on first().
    # Let's inspect call args or use a more robust mock if failed.
    # But here, query() is called with different models.

    # We can side_effect on query() to return different mock query objects

    mock_query_config = MagicMock()
    mock_query_config.filter.return_value.first.return_value = config

    mock_query_theme = MagicMock()
    mock_query_theme.filter.return_value.first.return_value = theme

    mock_query_asset = MagicMock()
    mock_query_asset.filter.return_value.all.return_value = [asset]

    def side_effect(model):
        if model == WhiteLabelConfig:
            return mock_query_config
        if model == WhiteLabelTheme:
            return mock_query_theme
        if model == WhiteLabelAsset:
            return mock_query_asset
        return MagicMock()

    mock_db.query.side_effect = side_effect

    result = await service.get_partner_config("domain.com")

    assert result["company_name"] == "Co"
    assert result["theme"]["name"] == "Theme"
    assert len(result["assets"]) == 1


@pytest.mark.asyncio
async def test_generate_custom_css(service, mock_db):
    theme = WhiteLabelTheme(css_variables={"--a": "10px"}, custom_css=".cls { color: red; }")
    mock_db.query.return_value.filter.return_value.first.return_value = theme

    css = await service.generate_custom_css(1)

    assert "--a: 10px;" in css
    assert ".cls { color: red; }" in css
    assert "@media" in css


@pytest.mark.asyncio
async def test_create_pwa_manifest(service, mock_db):
    config = WhiteLabelConfig(company_name="Corp", primary_color="#f00", logo_url="/logo.png")
    mock_db.query.return_value.filter.return_value.first.return_value = config

    manifest = await service.create_pwa_manifest(1)

    assert manifest["name"] == "Corp SMS Platform"
    assert manifest["background_color"] == "#f00"
    assert manifest["icons"][0]["src"] == "/logo.png"
