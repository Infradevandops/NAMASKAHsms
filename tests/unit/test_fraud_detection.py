

from unittest.mock import MagicMock
import pytest
from app.services.fraud_detection_service import FraudDetectionService

@pytest.mark.asyncio
async def test_score_verification_fraud():
    service = FraudDetectionService()
    service.threshold = 0.5

    # Mock calculate_score to return high score
    service._calculate_score = MagicMock(return_value=0.8)

    score, is_fraud = await service.score_verification(
        user_id="user1", country="high_risk", service="any", ip="127.0.0.1"
    )

    assert score == 0.8
    assert is_fraud is True


@pytest.mark.asyncio
async def test_score_verification_safe():
    service = FraudDetectionService()
    service.threshold = 0.5

    # Mock calculate_score to return low score
    service._calculate_score = MagicMock(return_value=0.2)

    score, is_fraud = await service.score_verification(user_id="user1", country="safe", service="any", ip="127.0.0.1")

    assert score == 0.2
    assert is_fraud is False


def test_calculate_score_logic():

    service = FraudDetectionService()

    # Test high risk country logic
    features = {"country": "high_risk_country", "service": "safe", "ip": "1.1.1.1"}
    score = service._calculate_score(features)
    assert score >= 0.3

    # Test high risk service logic
    features = {"country": "safe", "service": "high_risk_service", "ip": "1.1.1.1"}
    score = service._calculate_score(features)
    assert score >= 0.2


@pytest.mark.asyncio
async def test_get_model_metrics():
    service = FraudDetectionService()
    metrics = await service.get_model_metrics()
    assert "accuracy" in metrics
    assert metrics["accuracy"] > 0