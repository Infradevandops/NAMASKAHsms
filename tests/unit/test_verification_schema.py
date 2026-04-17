"""Test verification schema changes for v4.4.1."""

import pytest

from app.models.verification import Verification


def test_verification_has_retry_attempts_field():
    """Verify retry_attempts field exists."""
    v = Verification(
        user_id="test_user",
        service_name="whatsapp",
        cost=2.50,
    )
    assert hasattr(v, "retry_attempts")


def test_verification_has_area_code_matched_field():
    """Verify area_code_matched field exists."""
    v = Verification(
        user_id="test_user",
        service_name="whatsapp",
        cost=2.50,
    )
    assert hasattr(v, "area_code_matched")


def test_verification_has_carrier_matched_field():
    """Verify carrier_matched field exists."""
    v = Verification(
        user_id="test_user",
        service_name="whatsapp",
        cost=2.50,
    )
    assert hasattr(v, "carrier_matched")


def test_verification_has_real_carrier_field():
    """Verify real_carrier field exists."""
    v = Verification(
        user_id="test_user",
        service_name="whatsapp",
        cost=2.50,
    )
    assert hasattr(v, "real_carrier")


def test_verification_has_carrier_surcharge_field():
    """Verify carrier_surcharge field exists."""
    v = Verification(
        user_id="test_user",
        service_name="whatsapp",
        cost=2.50,
    )
    assert hasattr(v, "carrier_surcharge")


def test_verification_has_area_code_surcharge_field():
    """Verify area_code_surcharge field exists."""
    v = Verification(
        user_id="test_user",
        service_name="whatsapp",
        cost=2.50,
    )
    assert hasattr(v, "area_code_surcharge")


def test_verification_has_voip_rejected_field():
    """Verify voip_rejected field exists."""
    v = Verification(
        user_id="test_user",
        service_name="whatsapp",
        cost=2.50,
    )
    assert hasattr(v, "voip_rejected")


def test_retry_attempts_defaults_to_zero():
    """Verify retry_attempts defaults to 0."""
    v = Verification(
        user_id="test_user",
        service_name="whatsapp",
        cost=2.50,
    )
    assert v.retry_attempts == 0


def test_area_code_matched_defaults_to_true():
    """Verify area_code_matched defaults to True."""
    v = Verification(
        user_id="test_user",
        service_name="whatsapp",
        cost=2.50,
    )
    assert v.area_code_matched is True


def test_carrier_matched_defaults_to_true():
    """Verify carrier_matched defaults to True."""
    v = Verification(
        user_id="test_user",
        service_name="whatsapp",
        cost=2.50,
    )
    assert v.carrier_matched is True


def test_carrier_surcharge_defaults_to_zero():
    """Verify carrier_surcharge defaults to 0.0."""
    v = Verification(
        user_id="test_user",
        service_name="whatsapp",
        cost=2.50,
    )
    assert v.carrier_surcharge == 0.0


def test_area_code_surcharge_defaults_to_zero():
    """Verify area_code_surcharge defaults to 0.0."""
    v = Verification(
        user_id="test_user",
        service_name="whatsapp",
        cost=2.50,
    )
    assert v.area_code_surcharge == 0.0


def test_voip_rejected_defaults_to_false():
    """Verify voip_rejected defaults to False."""
    v = Verification(
        user_id="test_user",
        service_name="whatsapp",
        cost=2.50,
    )
    assert v.voip_rejected is False


def test_real_carrier_can_be_none():
    """Verify real_carrier can be None."""
    v = Verification(
        user_id="test_user",
        service_name="whatsapp",
        cost=2.50,
    )
    assert v.real_carrier is None


def test_can_set_retry_tracking_fields():
    """Verify retry tracking fields can be set."""
    v = Verification(
        user_id="test_user",
        service_name="whatsapp",
        cost=2.50,
        retry_attempts=2,
        area_code_matched=False,
        carrier_matched=False,
        real_carrier="Verizon Wireless",
        carrier_surcharge=0.30,
        area_code_surcharge=0.25,
        voip_rejected=True,
    )

    assert v.retry_attempts == 2
    assert v.area_code_matched is False
    assert v.carrier_matched is False
    assert v.real_carrier == "Verizon Wireless"
    assert v.carrier_surcharge == 0.30
    assert v.area_code_surcharge == 0.25
    assert v.voip_rejected is True
