import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.services.purchase_intelligence import PurchaseIntelligenceService

logger = logging.getLogger(__name__)


class PredictiveRouterScorer:
    """Institutional-grade routing scorer (Phase 12).

    Calculates weights based on Carrier Sentiment, Financial ROI, and Network Resilience.
    """

    def __init__(self, db: Session):
        self.db = db

    async def calculate_provider_score(
        self,
        service: str,
        country: str,
        provider_name: str,
        carrier: Optional[str] = None,
        area_code: Optional[str] = None,
    ) -> float:
        """
        Calculates a real-time 'Institutional Quality Score' (0.0 to 1.0).

        Weighting:
        - Sentiment (45%): Career/AreaCode success history
        - ROI (25%): Profitability vs Margin Leakage
        - Resilience (30%): Recent health status (60 min window)
        """
        try:
            # 1. Resilience (30%) - Async health check
            health_score = await PurchaseIntelligenceService.get_live_health_score(
                service, country, provider_name
            )

            # 2. ROI (25%) - Sync analytics check
            # We fetch ROI for the last 14 days for routing recency
            roi_data = PurchaseIntelligenceService.get_provider_roi(self.db, days=14)
            provider_roi = roi_data.get(provider_name, {})
            # Normalized ROI score (using efficiency_score which accounts for refunds)
            # Scaling: common efficiency is 50-150. We cap at 200 for 1.0 normalization.
            roi_raw = provider_roi.get("efficiency_score", 50.0)
            roi_score = min(roi_raw / 200.0, 1.0)

            # 3. Sentiment (45%) - Service/Carrier specificity
            sentiment_score = 0.5  # Neutral start
            if carrier:
                sentiment_map = PurchaseIntelligenceService.get_carrier_sentiment(
                    self.db, service, days=14
                )
                sentiment_score = sentiment_map.get(carrier, 0.5)
            elif area_code:
                # Fallback to general service health if specific carrier unknown
                sentiment_score = health_score

            # FINAL CALCULATION
            final_score = (
                (sentiment_score * 0.45) + (roi_score * 0.25) + (health_score * 0.30)
            )

            logger.info(
                f"Scored {provider_name} for {service}: {final_score:.2f} "
                f"(Sent={sentiment_score:.2f}, ROI={roi_score:.2f}, Health={health_score:.2f})"
            )

            return round(final_score, 4)

        except Exception as e:
            logger.error(f"Scoring error for {provider_name}: {e}")
            return 0.4  # Safe baseline for 'unknown' state during error
