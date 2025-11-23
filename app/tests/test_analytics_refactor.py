"""Test suite for refactored analytics service."""
import pytest
from unittest.mock import Mock
from datetime import datetime, timezone, timedelta

from app.services.analytics_service import AnalyticsCalculator


class TestAnalyticsCalculator:
    """Test analytics calculator service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock()

    @pytest.fixture
    def calculator(self, mock_db):
        """Create analytics calculator instance."""
        return AnalyticsCalculator(mock_db, "test_user_id")

    def test_get_basic_metrics(self, calculator, mock_db):
        """Test basic metrics calculation."""
        # Mock query results
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 100
        mock_db.query.return_value = mock_query

        # Mock scalar result for total_spent
        mock_query.filter.return_value.scalar.return_value = 50.0

        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        result = calculator.get_basic_metrics(start_date)

        assert "total_verifications" in result
        assert "success_rate" in result
        assert "total_spent" in result

    def test_get_service_analytics(self, calculator, mock_db):
        """Test service analytics calculation."""
        # Mock popular services query
        mock_query = Mock()
        mock_query.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            ("telegram", 50),
            ("whatsapp", 30)
        ]
        mock_db.query.return_value = mock_query

        # Mock individual service queries
        mock_query.filter.return_value.count.return_value = 40
        mock_query.filter.return_value.scalar.return_value = 25.0

        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        result = calculator.get_service_analytics(start_date)

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(service, ServiceUsage) for service in result)

    def test_get_daily_usage(self, calculator, mock_db):
        """Test daily usage calculation."""
        # Mock daily queries
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 5
        mock_query.filter.return_value.scalar.return_value = 2.5
        mock_db.query.return_value = mock_query

        result = calculator.get_daily_usage(7)

        assert isinstance(result, list)
        assert len(result) == 7
        assert all(isinstance(day, DailyUsage) for day in result)

    def test_get_country_analytics(self, calculator, mock_db):
        """Test country analytics calculation."""
        # Mock country stats query
        mock_query = Mock()
        mock_query.filter.return_value.group_by.return_value.all.return_value = [
            ("US", 50, 40, 0.75),
            ("GB", 30, 25, 0.80)
        ]
        mock_db.query.return_value = mock_query

        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        result = calculator.get_country_analytics(start_date)

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(country, CountryAnalytics) for country in result)

    def test_get_cost_trends(self, calculator, mock_db):
        """Test cost trends calculation."""
        # Mock weekly cost queries
        mock_query = Mock()
        mock_query.filter.return_value.scalar.return_value = 15.0
        mock_db.query.return_value = mock_query

        result = calculator.get_cost_trends()

        assert isinstance(result, list)
        assert len(result) == 4
        assert all(isinstance(trend, TrendData) for trend in result)

    def test_calculate_efficiency_score(self, calculator):
        """Test efficiency score calculation."""
        score = calculator.calculate_efficiency_score(85.0, 100.0, 50)

        assert isinstance(score, float)
        assert 0 <= score <= 100

    def test_generate_recommendations_low_success_rate(self, calculator):
        """Test recommendations for low success rate."""
        recommendations = calculator.generate_recommendations(70.0, 50.0, 25, [])

        assert isinstance(recommendations, list)
        assert any("higher - success-rate" in rec for rec in recommendations)

    def test_generate_recommendations_high_cost(self, calculator):
        """Test recommendations for high cost per verification."""
        recommendations = calculator.generate_recommendations(90.0, 150.0, 50, [])

        assert isinstance(recommendations, list)
        assert any("cost - effective" in rec for rec in recommendations)

    def test_generate_recommendations_low_usage(self, calculator):
        """Test recommendations for low usage."""
        recommendations = calculator.generate_recommendations(90.0, 50.0, 5, [])

        assert isinstance(recommendations, list)
        assert any("Increase usage" in rec for rec in recommendations)

    def test_generate_recommendations_best_service(self, calculator):
        """Test recommendations with best service."""
        services = [
            ServiceUsage(service="telegram", count=10,
                         success_rate=95.0, avg_cost=0.75, total_cost=7.5),
            ServiceUsage(service="whatsapp", count=5,
                         success_rate=80.0, avg_cost=0.80, total_cost=4.0)
        ]

        recommendations = calculator.generate_recommendations(85.0, 50.0, 25, services)

        assert isinstance(recommendations, list)
        assert any("telegram" in rec for rec in recommendations)


class TestAnalyticsIntegration:
    """Test analytics integration scenarios."""

    def test_empty_data_handling(self):
        """Test handling of empty data sets."""
        mock_db = Mock()
        calculator = AnalyticsCalculator(mock_db, "empty_user")

        # Mock empty results
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 0
        mock_query.filter.return_value.scalar.return_value = None
        mock_query.filter.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        start_date = datetime.now(timezone.utc) - timedelta(days=30)

        # Should not raise exceptions
        basic_metrics = calculator.get_basic_metrics(start_date)
        assert basic_metrics["total_verifications"] == 0

        services = calculator.get_service_analytics(start_date)
        assert services == []

        countries = calculator.get_country_analytics(start_date)
        assert countries == []

    def test_single_verification_scenario(self):
        """Test analytics with single verification."""
        mock_db = Mock()
        calculator = AnalyticsCalculator(mock_db, "single_user")

        # Mock single verification results
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 1
        mock_query.filter.return_value.scalar.return_value = 0.75
        mock_query.filter.return_value.all.return_value = [("telegram", 1)]
        mock_db.query.return_value = mock_query

        start_date = datetime.now(timezone.utc) - timedelta(days=30)

        basic_metrics = calculator.get_basic_metrics(start_date)
        assert basic_metrics["total_verifications"] == 1

        services = calculator.get_service_analytics(start_date)
        assert len(services) == 1
        assert services[0].service == "telegram"

    def test_prediction_generation(self):
        """Test prediction generation with sufficient data."""
        mock_db = Mock()
        calculator = AnalyticsCalculator(mock_db, "prediction_user")

        # Create mock daily usage data
        daily_usage = []
        for i in range(10):
            daily_usage.append(
                DailyUsage(
                    date=f"2024 - 01-{i + 1:02d}",
                    count=5 + i,
                    cost=2.5 + i * 0.5,
                    success_rate=85.0 + i
                )
            )

        predictions = calculator.get_predictions(daily_usage)

        assert isinstance(predictions, list)
        assert len(predictions) == 2  # daily_usage and weekly_cost predictions
        assert all(pred.confidence > 0 for pred in predictions)

    def test_prediction_insufficient_data(self):
        """Test prediction generation with insufficient data."""
        mock_db = Mock()
        calculator = AnalyticsCalculator(mock_db, "insufficient_user")

        # Create insufficient daily usage data
        daily_usage = [
            DailyUsage(date="2024 - 01-01", count=5, cost=2.5, success_rate=85.0)
        ]

        predictions = calculator.get_predictions(daily_usage)

        assert predictions == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
