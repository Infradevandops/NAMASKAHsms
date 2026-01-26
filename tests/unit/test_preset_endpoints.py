"""Tests for verification preset endpoints."""

from unittest.mock import Mock, patch

import pytest

from app.api.verification.preset_endpoints import PresetCreate


def test_preset_create_model():
    """Test PresetCreate model validation."""
    preset = PresetCreate(name="Test Preset", service_id="whatsapp", country_id="US", area_code="212")
    assert preset.name == "Test Preset"
    assert preset.service_id == "whatsapp"
    assert preset.country_id == "US"
    assert preset.area_code == "212"


def test_preset_create_defaults():
    """Test PresetCreate with default values."""
    preset = PresetCreate(name="Test", service_id="telegram")
    assert preset.country_id == "US"
    assert preset.area_code is None
    assert preset.carrier is None
