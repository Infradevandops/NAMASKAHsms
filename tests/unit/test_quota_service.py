

from app.services.quota_service import QuotaService

class TestQuotaService:

    def test_get_monthly_usage_empty(self, db_session, regular_user):

        usage = QuotaService.get_monthly_usage(db_session, regular_user.id)
        assert usage["quota_used"] == 0.0
        assert usage["quota_limit"] == 0.0  # Freemium default

    def test_add_quota_usage(self, db_session, regular_user):

        QuotaService.add_quota_usage(db_session, regular_user.id, 10.0)
        usage = QuotaService.get_monthly_usage(db_session, regular_user.id)
        assert usage["quota_used"] == 10.0

    def test_calculate_overage_pro(self, db_session, regular_user):

        regular_user.subscription_tier = "pro"
        db_session.commit()

        # Pro has 15.0 USD quota, 0.30 overage rate
        # Usage 10.0, adding 10.0 -> 5.0 overage @ 0.30 = 1.50
        QuotaService.add_quota_usage(db_session, regular_user.id, 10.0)
        overage = QuotaService.calculate_overage(db_session, regular_user.id, 10.0)
        assert overage == 1.50  # (20 - 15) * 0.3

    def test_reset_monthly_quota(self, db_session, regular_user):

        regular_user.monthly_quota_used = 100.0
        db_session.commit()

        QuotaService.reset_monthly_quota(db_session, regular_user.id)
        assert regular_user.monthly_quota_used == 0.0

    def test_get_overage_rate(self, db_session, regular_user):

        regular_user.subscription_tier = "pro"
        assert QuotaService.get_overage_rate(db_session, regular_user.id) == 0.30
