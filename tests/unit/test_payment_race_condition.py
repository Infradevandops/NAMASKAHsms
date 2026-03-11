"""Race condition test: concurrent credits for the same payment reference."""

import threading
import tempfile
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User
from app.models.transaction import PaymentLog, Transaction
from app.services.payment_service import PaymentService


@pytest.fixture
def db_url(tmp_path):
    return f"sqlite:///{tmp_path}/test_race.db"


@pytest.fixture
def db(db_url):
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def user(db):
    u = User(
        email="race@test.com",
        password_hash="x",
        credits=0.0,
        subscription_tier="freemium",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def payment_log(db, user):
    log = PaymentLog(
        user_id=user.id,
        email=user.email,
        reference="ref_race_001",
        amount_usd=10.0,
        namaskah_amount=10.0,
        status="success",
        credited=False,
        state="pending",
    )
    db.add(log)
    db.commit()
    return log


def test_concurrent_credits_only_applied_once(db, db_url, user, payment_log):
    """Two concurrent credit_user calls for the same reference must credit exactly once."""
    results = []
    errors = []

    def attempt_credit():
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Session = sessionmaker(bind=engine)
        s = Session()
        try:
            svc = PaymentService(s)
            result = svc.credit_user(user.id, 10.0, "ref_race_001")
            results.append(result)
        except Exception as e:
            errors.append(e)
        finally:
            s.close()
            engine.dispose()

    t1 = threading.Thread(target=attempt_credit)
    t2 = threading.Thread(target=attempt_credit)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    db.expire(user)
    db.refresh(user)

    assert not errors, f"Unexpected errors: {errors}"
    assert (
        user.credits == 10.0
    ), f"Expected 10.0, got {user.credits} (double-credit detected)"

    tx_count = (
        db.query(Transaction).filter(Transaction.reference == "ref_race_001").count()
    )
    assert tx_count == 1, f"Expected 1 transaction record, got {tx_count}"
