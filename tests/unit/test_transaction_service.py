"""Unit tests for TransactionService."""

from unittest.mock import MagicMock

import pytest

from app.models.transaction import Transaction
from app.services.transaction_service import TransactionService


def test_record_sms_purchase():
    """Should record SMS purchase transaction."""
    # Mock database session
    db = MagicMock()

    # Record transaction
    result = TransactionService.record_sms_purchase(
        db=db,
        user_id="user123",
        amount=2.50,
        service="whatsapp",
        verification_id="ver123",
        old_balance=10.00,
        new_balance=7.50,
        filters={"area_code": "212"},
        tier="payg",
    )

    # Assertions
    db.add.assert_called_once()
    db.flush.assert_called_once()

    # Check transaction object
    call_args = db.add.call_args[0][0]
    assert isinstance(call_args, Transaction)
    assert call_args.user_id == "user123"
    assert call_args.amount == -2.50  # Negative for debit
    assert call_args.type == "sms_purchase"
    assert call_args.service == "whatsapp"
    assert call_args.tier == "payg"
    assert call_args.status == "completed"
    assert "ver123" in call_args.reference


def test_record_credit_addition():
    """Should record credit addition transaction."""
    # Mock database session
    db = MagicMock()

    # Record transaction
    result = TransactionService.record_credit_addition(
        db=db,
        user_id="user123",
        amount=50.00,
        payment_reference="pay_abc123",
        payment_method="paystack",
    )

    # Assertions
    db.add.assert_called_once()
    db.flush.assert_called_once()

    # Check transaction object
    call_args = db.add.call_args[0][0]
    assert isinstance(call_args, Transaction)
    assert call_args.user_id == "user123"
    assert call_args.amount == 50.00  # Positive for credit
    assert call_args.type == "credit"
    assert call_args.reference == "pay_abc123"
    assert call_args.status == "completed"


def test_record_refund():
    """Should record refund transaction."""
    # Mock database session
    db = MagicMock()

    # Record transaction
    result = TransactionService.record_refund(
        db=db,
        user_id="user123",
        amount=2.50,
        verification_id="ver123",
        reason="VOIP number rejected",
    )

    # Assertions
    db.add.assert_called_once()
    db.flush.assert_called_once()

    # Check transaction object
    call_args = db.add.call_args[0][0]
    assert isinstance(call_args, Transaction)
    assert call_args.user_id == "user123"
    assert call_args.amount == 2.50  # Positive for refund
    assert call_args.type == "refund"
    assert "refund_ver123" in call_args.reference
    assert call_args.status == "completed"
    assert "VOIP" in call_args.description
