#!/usr/bin/env python3
"""Migration validation and rollback testing script."""
import sys
from pathlib import Path

from sqlalchemy import inspect

from app.core.database import SessionLocal, engine
from app.models import APIKey, Transaction, User, Verification

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def validate_schema():
    """Validate that all expected tables and columns exist."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    expected_tables = [
        "users",
        "api_keys",
        "webhooks",
        "verifications",
        "number_rentals",
        "transactions",
        "payment_logs",
        "service_status",
        "support_tickets",
        "activity_logs",
    ]

    print("🔍 Validating database schema...")

    missing_tables = []
    for table in expected_tables:
        if table not in tables:
            missing_tables.append(table)
        else:
            print(f"✅ Table '{table}' exists")

    if missing_tables:
        print(f"❌ Missing tables: {missing_tables}")
        return False

    # Validate key columns
    user_columns = [col["name"] for col in inspector.get_columns("users")]
    required_user_columns = ["id", "email", "password_hash", "credits", "created_at"]

    for col in required_user_columns:
        if col not in user_columns:
            print(f"❌ Missing column '{col}' in users table")
            return False
        else:
            print(f"✅ Column 'users.{col}' exists")

    print("✅ Schema validation passed!")
    return True


def validate_relationships():
    """Validate that model relationships work correctly."""
    print("\n🔗 Validating model relationships...")

    db = SessionLocal()
    try:
        # Test creating related objects
        user = User(
            email="test@validation.com",
            password_hash="test_hash",
            referral_code="TEST123",
        )
        db.add(user)
        db.flush()  # Get ID without committing

        # Test API key relationship
        api_key = APIKey(user_id=user.id, key="test_key_123", name="Test Key")
        db.add(api_key)
        db.flush()

        # Test verification relationship
        verification = Verification(user_id=user.id, service_name="telegram", cost=1.0)
        db.add(verification)
        db.flush()

        # Test transaction relationship
        transaction = Transaction(
            user_id=user.id, amount=10.0, type="credit", description="Test transaction"
        )
        db.add(transaction)
        db.flush()

        # Validate relationships
        if len(user.api_keys) != 1:
            raise ValueError(f"Expected 1 API key, got {len(user.api_keys)}")
        if len(user.verifications) != 1:
            raise ValueError(f"Expected 1 verification, got {len(user.verifications)}")
        if len(user.transactions) != 1:
            raise ValueError(f"Expected 1 transaction, got {len(user.transactions)}")
        if api_key.user.email != "test@validation.com":
            raise ValueError(f"API key user email mismatch: {api_key.user.email}")
        if verification.user.email != "test@validation.com":
            raise ValueError(
                f"Verification user email mismatch: {verification.user.email}"
            )
        if transaction.user.email != "test@validation.com":
            raise ValueError(
                f"Transaction user email mismatch: {transaction.user.email}"
            )

        print("✅ All relationships working correctly!")

        # Rollback test data
        db.rollback()
        return True

    except Exception as e:
        print(f"❌ Relationship validation failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def validate_indexes():
    """Validate that important indexes exist."""
    print("\n📊 Validating database indexes...")

    inspector = inspect(engine)

    # Check users table indexes
    user_indexes = inspector.get_indexes("users")
    user_index_columns = [idx["column_names"] for idx in user_indexes]

    expected_indexes = [["email"], ["referral_code"]]

    for expected in expected_indexes:
        if expected in user_index_columns:
            print(f"✅ Index on users.{expected[0]} exists")
        else:
            print(f"⚠️ Missing index on users.{expected[0]}")

    # Check verifications table indexes
    verification_indexes = inspector.get_indexes("verifications")
    verification_index_columns = [idx["column_names"] for idx in verification_indexes]

    if ["service_name"] in verification_index_columns:
        print("✅ Index on verifications.service_name exists")
    else:
        print("⚠️ Missing index on verifications.service_name")

    return True


def test_data_integrity():
    """Test data integrity constraints."""
    print("\n🛡️ Testing data integrity constraints...")

    db = SessionLocal()
    try:
        # Test unique email constraint
        user1 = User(email="duplicate@test.com", password_hash="hash1")
        user2 = User(email="duplicate@test.com", password_hash="hash2")

        db.add(user1)
        db.commit()

        db.add(user2)
        try:
            db.commit()
            print("❌ Unique email constraint not working!")
            return False
        except Exception:
            print("✅ Unique email constraint working")
            db.rollback()

        # Test foreign key constraint
        verification = Verification(
            user_id="nonexistent_user", service_name="telegram", cost=1.0
        )
        db.add(verification)
        try:
            db.commit()
            print("❌ Foreign key constraint not working!")
            return False
        except Exception:
            print("✅ Foreign key constraint working")
            db.rollback()

        return True

    except Exception as e:
        print(f"❌ Data integrity test failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """Run all validation tests."""
    print("🚀 Starting migration validation...\n")

    tests = [
        ("Schema Validation", validate_schema),
        ("Relationship Validation", validate_relationships),
        ("Index Validation", validate_indexes),
        ("Data Integrity", test_data_integrity),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 50)
    print("📋 VALIDATION SUMMARY")
    print("=" * 50)

    all_passed = True
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False

    if all_passed:
        print("\n🎉 All validation tests passed! Migration is ready.")
        return 0
    else:
        print("\n⚠️ Some validation tests failed. Please review before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
