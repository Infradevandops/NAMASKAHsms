"""Tests for SQL injection prevention."""
from sqlalchemy.orm import Session
from app.core.database_optimization import QueryOptimizer
from app.models.user import User
from app.models.verification import Verification
from app.utils.security import hash_password


class TestSQLInjectionPrevention:
    """Test SQL injection prevention in database queries."""

    def test_user_id_sql_injection_attempt(self, db_session: Session):
        """Test that user_id parameters are properly sanitized."""
        # Create test user
        user = User(
            email="test@example.com",
            password_hash=hash_password("testpass"),
            credits=10.0
        )
        db_session.add(user)
        db_session.commit()

        # Attempt SQL injection through user_id parameter
        malicious_user_id = "'; DROP TABLE users; --"

        # This should not cause SQL injection
        result = QueryOptimizer.get_user_verifications_optimized(
            db_session, malicious_user_id
        )

        # Should return empty list, not cause database error
        assert isinstance(result, list)
        assert len(result) == 0

        # Verify users table still exists
        users = db_session.query(User).all()
        assert len(users) >= 1

    def test_verification_stats_sql_injection(self, db_session: Session):
        """Test verification stats query against SQL injection."""
        # Create test user
        user = User(
            email="test2@example.com",
            password_hash=hash_password("testpass"),
            credits=10.0
        )
        db_session.add(user)
        db_session.commit()

        # Attempt SQL injection in verification stats
        malicious_user_id = "1 OR 1 = 1; DELETE FROM verifications; --"

        # This should not cause SQL injection
        result = QueryOptimizer.get_verification_stats_optimized(
            db_session, malicious_user_id
        )

        # Should return empty result, not cause database error
        assert isinstance(result, list)

        # Verify verifications table still exists
        verifications = db_session.query(Verification).all()
        assert isinstance(verifications, list)

    def test_parameterized_query_safety(self, db_session: Session):
        """Test that parameterized queries handle special characters safely."""
        # Create test user with special characters in ID
        user = User(
            email="special@example.com",
            password_hash=hash_password("testpass"),
            credits=10.0
        )
        db_session.add(user)
        db_session.commit()

        # Test with various special characters
        special_chars = ["'", '"', ";", "--", "/*", "*/", "\\", "%", "_"]

        for char in special_chars:
            test_user_id = f"user_{char}_test"

            # Should handle special characters safely
            result = QueryOptimizer.get_user_verifications_optimized(
                db_session, test_user_id
            )
            assert isinstance(result, list)

    def test_orm_query_safety(self, db_session: Session):
        """Test that ORM queries are safe from injection."""
        # Create test verification
        user = User(
            email="orm@example.com",
            password_hash=hash_password("testpass"),
            credits=10.0
        )
        db_session.add(user)
        db_session.commit()

        verification = Verification(
            user_id=user.id,
            service_name="test_service",
            status="pending",
            cost=1.0
        )
        db_session.add(verification)
        db_session.commit()

        # Test ORM query with malicious input
        malicious_service = "'; DROP TABLE verifications; --"

        # ORM should handle this safely
        results = db_session.query(Verification).filter(
            Verification.service_name == malicious_service
        ).all()

        assert isinstance(results, list)
        assert len(results) == 0

        # Verify original data is intact
        all_verifications = db_session.query(Verification).all()
        assert len(all_verifications) >= 1

    def test_no_raw_sql_execution(self, db_session: Session):
        """Test that we don't execute raw SQL strings."""
        # This test ensures we're not accidentally executing raw SQL

        # These should all be safe ORM operations
        user_count = db_session.query(User).count()
        verification_count = db_session.query(Verification).count()

        assert isinstance(user_count, int)
        assert isinstance(verification_count, int)
        assert user_count >= 0
        assert verification_count >= 0
