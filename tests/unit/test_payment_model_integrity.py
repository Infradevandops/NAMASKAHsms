"""Tests confirming payment_logs table has a single definition and works correctly."""

import uuid
import pytest
from app.models.transaction import PaymentLog, Transaction


def test_only_one_paymentlog_class():
    """Confirm app.models.payment no longer exists — only transaction.PaymentLog."""
    try:
        import app.models.payment  # noqa

        assert False, "app.models.payment should have been deleted"
    except ImportError:
        pass  # expected


def test_paymentlog_tablename():
    """PaymentLog maps to payment_logs table."""
    assert PaymentLog.__tablename__ == "payment_logs"


def test_paymentlog_has_required_columns():
    """PaymentLog has all columns needed by payment_service."""
    cols = {c.name for c in PaymentLog.__table__.columns}
    required = {
        "user_id",
        "email",
        "reference",
        "amount_usd",
        "namaskah_amount",
        "status",
        "credited",
    }
    assert required.issubset(cols), f"Missing columns: {required - cols}"


def test_paymentlog_create_and_query(db):
    """PaymentLog can be written and read from the test DB."""
    ref = f"test_ref_{uuid.uuid4().hex[:8]}"
    log = PaymentLog(
        user_id=str(uuid.uuid4()),
        email="test@example.com",
        reference=ref,
        amount_ngn=5000.0,
        amount_usd=3.0,
        namaskah_amount=3.0,
        status="success",
        credited=True,
    )
    db.add(log)
    db.commit()

    fetched = db.query(PaymentLog).filter(PaymentLog.reference == ref).first()
    assert fetched is not None
    assert fetched.amount_usd == 3.0
    assert fetched.credited is True


def test_transaction_and_paymentlog_coexist(db):
    """Transaction and PaymentLog can both be imported and used without mapper conflict."""
    uid = str(uuid.uuid4())
    tx = Transaction(
        user_id=uid,
        amount=3.0,
        type="credit",
        description="Test",
        status="completed",
        reference=f"tx_{uuid.uuid4().hex[:8]}",
    )
    db.add(tx)

    log = PaymentLog(
        user_id=uid,
        email="coexist@example.com",
        reference=f"pl_{uuid.uuid4().hex[:8]}",
        amount_ngn=5000.0,
        amount_usd=3.0,
        namaskah_amount=3.0,
        status="success",
        credited=True,
    )
    db.add(log)
    db.commit()

    assert db.query(Transaction).filter(Transaction.user_id == uid).count() == 1
    assert db.query(PaymentLog).filter(PaymentLog.user_id == uid).count() == 1
