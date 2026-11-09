"""
Email system hardening tests — EMAIL-040.

Covers:
- Message classification (EMAIL-010)
- Preference policy (EMAIL-011)
- Contact form durability (EMAIL-012)
- Footer/unsubscribe semantics (EMAIL-013)
- Canonical sender config (EMAIL-021)
- Template rendering safety (EMAIL-022)
- Outbox idempotency (EMAIL-030)
- Provider adapter behavior (EMAIL-020)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.email_classes import (
    EmailClass,
    get_template_class,
    is_suppressible_by_opt_out,
)


# ── EMAIL-010: Message classification ────────────────────────────────────────

class TestEmailClassification:
    def test_password_reset_is_account_security(self):
        assert get_template_class("send_password_reset") == EmailClass.ACCOUNT_SECURITY

    def test_verification_email_is_account_security(self):
        assert get_template_class("send_verification_email") == EmailClass.ACCOUNT_SECURITY

    def test_payment_receipt_is_transactional_essential(self):
        assert get_template_class("send_payment_receipt") == EmailClass.TRANSACTIONAL_ESSENTIAL

    def test_refund_is_transactional_essential(self):
        assert get_template_class("send_refund_notification") == EmailClass.TRANSACTIONAL_ESSENTIAL

    def test_digest_is_optional_product(self):
        assert get_template_class("send_daily_digest_email") == EmailClass.OPTIONAL_PRODUCT

    def test_low_balance_is_optional_product(self):
        assert get_template_class("send_low_balance_alert_email") == EmailClass.OPTIONAL_PRODUCT

    def test_unknown_template_defaults_to_optional(self):
        assert get_template_class("unknown_template_xyz") == EmailClass.OPTIONAL_PRODUCT

    def test_account_security_not_suppressible(self):
        assert not is_suppressible_by_opt_out(EmailClass.ACCOUNT_SECURITY)

    def test_transactional_not_suppressible(self):
        assert not is_suppressible_by_opt_out(EmailClass.TRANSACTIONAL_ESSENTIAL)

    def test_optional_product_is_suppressible(self):
        assert is_suppressible_by_opt_out(EmailClass.OPTIONAL_PRODUCT)

    def test_forwarding_is_suppressible(self):
        assert is_suppressible_by_opt_out(EmailClass.USER_CONFIGURED_FORWARDING)

    def test_operational_admin_not_suppressible(self):
        assert not is_suppressible_by_opt_out(EmailClass.OPERATIONAL_ADMIN)

    def test_all_template_keys_have_valid_class(self):
        from app.services.email_classes import TEMPLATE_CLASS_MAP
        for key, cls in TEMPLATE_CLASS_MAP.items():
            assert isinstance(cls, EmailClass), f"{key} has invalid class"


# ── EMAIL-011: Preference policy ─────────────────────────────────────────────

class TestEmailPreferencePolicy:
    def _make_db(self, pref=None, user=None, ns=None):
        db = MagicMock()
        mock_user = user or MagicMock(is_active=True, is_suspended=False, is_banned=False)
        mock_pref = pref  # None means no row

        def query_side_effect(model):
            from app.models.notification_preference import NotificationPreference
            from app.models.user import NotificationSettings, User
            q = MagicMock()
            if model is User:
                q.filter.return_value.first.return_value = mock_user
            elif model is NotificationPreference:
                q.filter.return_value.first.return_value = mock_pref
            elif model is NotificationSettings:
                q.filter.return_value.first.return_value = ns
            return q

        db.query.side_effect = query_side_effect
        return db

    def test_non_optional_always_allowed(self):
        from app.services.email_preference_policy import EmailPreferencePolicy
        db = self._make_db()
        policy = EmailPreferencePolicy(db)
        allowed, reason = policy.can_send("u1", "any", EmailClass.ACCOUNT_SECURITY)
        assert allowed is True
        assert reason == "not_optional"

    def test_category_disabled_blocks_send(self):
        from app.services.email_preference_policy import EmailPreferencePolicy
        pref = MagicMock(enabled=False, delivery_methods="email", frequency="instant")
        db = self._make_db(pref=pref)
        policy = EmailPreferencePolicy(db)
        allowed, reason = policy.can_send("u1", "low_balance", EmailClass.OPTIONAL_PRODUCT)
        assert allowed is False
        assert reason == "category_disabled"

    def test_email_not_in_delivery_methods_blocks(self):
        from app.services.email_preference_policy import EmailPreferencePolicy
        pref = MagicMock(enabled=True, delivery_methods="toast,push", frequency="instant")
        db = self._make_db(pref=pref)
        policy = EmailPreferencePolicy(db)
        allowed, reason = policy.can_send("u1", "low_balance", EmailClass.OPTIONAL_PRODUCT)
        assert allowed is False
        assert reason == "email_not_in_delivery_methods"

    def test_frequency_never_blocks(self):
        from app.services.email_preference_policy import EmailPreferencePolicy
        pref = MagicMock(enabled=True, delivery_methods="email", frequency="never")
        db = self._make_db(pref=pref)
        policy = EmailPreferencePolicy(db)
        allowed, reason = policy.can_send("u1", "digest", EmailClass.OPTIONAL_PRODUCT)
        assert allowed is False
        assert reason == "frequency_never"

    def test_all_conditions_met_allows(self):
        from app.services.email_preference_policy import EmailPreferencePolicy
        pref = MagicMock(enabled=True, delivery_methods="toast,email", frequency="instant")
        db = self._make_db(pref=pref)
        policy = EmailPreferencePolicy(db)
        allowed, reason = policy.can_send("u1", "low_balance", EmailClass.OPTIONAL_PRODUCT)
        assert allowed is True
        assert reason == "allowed"

    def test_no_pref_row_defaults_to_allow(self):
        from app.services.email_preference_policy import EmailPreferencePolicy
        db = self._make_db(pref=None)
        policy = EmailPreferencePolicy(db)
        allowed, reason = policy.can_send("u1", "some_category", EmailClass.OPTIONAL_PRODUCT)
        assert allowed is True
        assert reason == "default_allow"

    def test_inactive_user_blocked(self):
        from app.services.email_preference_policy import EmailPreferencePolicy
        user = MagicMock(is_active=False, is_suspended=False, is_banned=False)
        db = self._make_db(user=user)
        policy = EmailPreferencePolicy(db)
        allowed, reason = policy.can_send("u1", "digest", EmailClass.OPTIONAL_PRODUCT)
        assert allowed is False
        assert reason == "account_inactive"

    def test_get_effective_preferences_derives_enabled_from_data(self):
        from app.models.notification_preference import NotificationPreference
        from app.services.email_preference_policy import EmailPreferencePolicy

        pref = MagicMock(spec=NotificationPreference)
        pref.notification_type = "low_balance"
        pref.enabled = True
        pref.delivery_methods = "email,toast"
        pref.frequency = "instant"

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [pref]
        policy = EmailPreferencePolicy(db)
        result = policy.get_effective_preferences("u1")

        assert result["email_notifications_enabled"] is True
        assert result["notification_types"]["low_balance"]["email_enabled"] is True

    def test_get_effective_preferences_false_when_no_email_method(self):
        from app.models.notification_preference import NotificationPreference
        from app.services.email_preference_policy import EmailPreferencePolicy

        pref = MagicMock(spec=NotificationPreference)
        pref.notification_type = "low_balance"
        pref.enabled = True
        pref.delivery_methods = "toast"
        pref.frequency = "instant"

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [pref]
        policy = EmailPreferencePolicy(db)
        result = policy.get_effective_preferences("u1")

        # email_notifications_enabled must NOT be hardcoded True
        assert result["email_notifications_enabled"] is False


# ── EMAIL-012: Contact form durability ───────────────────────────────────────

class TestContactFormDurability:
    @pytest.mark.asyncio
    async def test_submission_persisted_before_response(self):
        """DB add+commit must be called before returning success."""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        from app.api.core.contact import ContactRequest, send_contact_message

        req = ContactRequest(
            name="Test User",
            email="test@example.com",
            subject="Help",
            category="support",
            message="I need help with something.",
        )

        with patch("app.api.core.contact.ContactSubmission") as MockSub, \
             patch("app.services.email_service.email_service") as mock_svc:
            mock_instance = MagicMock()
            mock_instance.id = "sub-123"
            MockSub.return_value = mock_instance
            mock_svc._send = AsyncMock(return_value=True)

            result = await send_contact_message(req, db=db)

        assert db.add.called
        assert db.commit.called
        assert result["status"] == "success"
        assert "submission_id" in result

    @pytest.mark.asyncio
    async def test_success_returned_even_if_forwarding_fails(self):
        """API must return success after DB persist even if email fails."""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        from app.api.core.contact import ContactRequest, send_contact_message

        req = ContactRequest(
            name="Test",
            email="t@example.com",
            subject="Sub",
            category="support",
            message="Message body here.",
        )

        with patch("app.api.core.contact.ContactSubmission") as MockSub, \
             patch("app.services.email_service.email_service") as mock_svc:
            mock_instance = MagicMock()
            mock_instance.id = "sub-456"
            MockSub.return_value = mock_instance
            mock_svc._send = AsyncMock(side_effect=RuntimeError("SMTP down"))

            result = await send_contact_message(req, db=db)

        assert result["status"] == "success"
        assert db.add.called  # submission was persisted


# ── EMAIL-013: Footer/unsubscribe semantics ───────────────────────────────────

class TestFooterSemantics:
    def test_password_reset_has_no_unsubscribe_footer(self):
        from app.services.email_service import EmailService
        with patch("app.services.email_service.get_settings") as ms:
            ms.return_value.smtp_host = "localhost"
            ms.return_value.smtp_port = 587
            ms.return_value.smtp_username = "u"
            ms.return_value.smtp_password = "p"
            ms.return_value.resend_api_key = None
            ms.return_value.from_email_address = None
            svc = EmailService()

        # Build the reset HTML and check no unsubscribe link appears
        import asyncio
        html_parts = []
        original_send = svc._send

        async def capture(to, subj, html):
            html_parts.append(html)
            return True

        svc._send = capture
        asyncio.run(svc.send_password_reset("u@example.com", "tok123"))
        assert html_parts, "send_password_reset did not call _send"
        html = html_parts[0]
        assert "unsubscribe" not in html.lower(), \
            "password_reset must not contain unsubscribe language"

    def test_verification_email_has_no_unsubscribe_footer(self):
        from app.services.email_service import EmailService
        with patch("app.services.email_service.get_settings") as ms:
            ms.return_value.smtp_host = "localhost"
            ms.return_value.smtp_port = 587
            ms.return_value.smtp_username = "u"
            ms.return_value.smtp_password = "p"
            ms.return_value.resend_api_key = None
            ms.return_value.from_email_address = None
            svc = EmailService()

        import asyncio
        html_parts = []

        async def capture(to, subj, html):
            html_parts.append(html)
            return True

        svc._send = capture
        asyncio.run(svc.send_verification_email("u@example.com", "tok456"))
        assert html_parts
        assert "unsubscribe" not in html_parts[0].lower()


# ── EMAIL-021: Canonical sender config ───────────────────────────────────────

class TestCanonicalSenderConfig:
    def test_from_email_uses_from_email_address_setting(self):
        from app.services.email_service import EmailService
        with patch("app.services.email_service.get_settings") as ms:
            ms.return_value.smtp_host = "localhost"
            ms.return_value.smtp_port = 587
            ms.return_value.smtp_username = "smtp@example.com"
            ms.return_value.smtp_password = "pass"
            ms.return_value.resend_api_key = None
            ms.return_value.from_email_address = "hello@vrenum.app"
            svc = EmailService()
        assert svc.from_email == "hello@vrenum.app"

    def test_from_email_falls_back_to_smtp_username(self):
        from app.services.email_service import EmailService
        with patch("app.services.email_service.get_settings") as ms:
            ms.return_value.smtp_host = "localhost"
            ms.return_value.smtp_port = 587
            ms.return_value.smtp_username = "smtp@example.com"
            ms.return_value.smtp_password = "pass"
            ms.return_value.resend_api_key = None
            ms.return_value.from_email_address = None
            svc = EmailService()
        assert svc.from_email == "smtp@example.com"

    def test_disabled_when_no_credentials(self):
        from app.services.email_service import EmailService
        with patch("app.services.email_service.get_settings") as ms:
            ms.return_value.smtp_host = None
            ms.return_value.smtp_username = None
            ms.return_value.smtp_password = None
            ms.return_value.resend_api_key = None
            ms.return_value.from_email_address = None
            svc = EmailService()
        assert svc.enabled is False


# ── EMAIL-022: Template rendering safety ─────────────────────────────────────

class TestTemplateRenderingSafety:
    def _make_service(self):
        from app.services.email_template_service import EmailTemplateService
        return EmailTemplateService()

    def test_html_to_text_strips_tags(self):
        svc = self._make_service()
        result = svc._html_to_text("<h1>Hello</h1><p>World</p>")
        assert "<" not in result
        assert "Hello" in result
        assert "World" in result

    def test_html_to_text_ignores_style_blocks(self):
        svc = self._make_service()
        result = svc._html_to_text("<style>body{color:red}</style><p>Content</p>")
        assert "color" not in result
        assert "Content" in result

    def test_safe_url_rejects_http(self):
        from app.services.email_template_service import _safe_url
        assert _safe_url("http://vrenum.app/wallet") == "#"

    def test_safe_url_rejects_javascript(self):
        from app.services.email_template_service import _safe_url
        assert _safe_url("javascript:alert(1)") == "#"

    def test_safe_url_rejects_untrusted_host(self):
        from app.services.email_template_service import _safe_url
        assert _safe_url("https://evil.com/steal") == "#"

    def test_safe_url_accepts_trusted_https(self):
        from app.services.email_template_service import _safe_url
        url = "https://vrenum.app/wallet"
        assert _safe_url(url) == url

    def test_validate_template_variables_rejects_unknown(self):
        svc = self._make_service()
        with pytest.raises(ValueError, match="Invalid variables"):
            svc._validate_template_variables("welcome", "{{ evil_var }}")

    def test_validate_template_variables_accepts_allowed(self):
        svc = self._make_service()
        # Should not raise
        svc._validate_template_variables("welcome", "{{ user_name }} {{ company_name }}")

    def test_sanitize_url_variables_cleans_unsafe_url(self):
        svc = self._make_service()
        result = svc._sanitize_url_variables({"top_up_url": "http://evil.com"})
        assert result["top_up_url"] == "#"

    def test_sanitize_url_variables_keeps_safe_url(self):
        svc = self._make_service()
        url = "https://vrenum.app/wallet"
        result = svc._sanitize_url_variables({"top_up_url": url})
        assert result["top_up_url"] == url


# ── EMAIL-030: Outbox idempotency ─────────────────────────────────────────────

class TestOutboxIdempotency:
    def test_email_outbox_model_has_idempotency_key(self):
        from app.models.email_outbox import EmailOutbox
        cols = {c.name for c in EmailOutbox.__table__.columns}
        assert "idempotency_key" in cols
        assert "status" in cols
        assert "attempt_count" in cols
        assert "max_attempts" in cols
        assert "lease_owner" in cols

    def test_contact_submission_model_has_forwarding_status(self):
        from app.models.contact_submission import ContactSubmission
        cols = {c.name for c in ContactSubmission.__table__.columns}
        assert "forwarding_status" in cols
        assert "email" in cols
        assert "message" in cols


# ── EMAIL-020: Provider adapter ───────────────────────────────────────────────

class TestProviderAdapter:
    @pytest.mark.asyncio
    async def test_smtp_send_called_with_correct_args(self):
        from app.services.email_service import EmailService
        smtp_mock = MagicMock()
        smtp_mock.__enter__ = MagicMock(return_value=smtp_mock)
        smtp_mock.__exit__ = MagicMock(return_value=None)

        with patch("app.services.email_service.get_settings") as ms, \
             patch("smtplib.SMTP", return_value=smtp_mock):
            ms.return_value.smtp_host = "localhost"
            ms.return_value.smtp_port = 587
            ms.return_value.smtp_username = "u"
            ms.return_value.smtp_password = "p"
            ms.return_value.resend_api_key = None
            ms.return_value.from_email_address = None
            svc = EmailService()
            result = await svc._send("to@example.com", "Subject", "<p>Body</p>")

        assert result is True
        assert smtp_mock.login.called
        assert smtp_mock.sendmail.called

    @pytest.mark.asyncio
    async def test_disabled_service_returns_false(self):
        from app.services.email_service import EmailService
        with patch("app.services.email_service.get_settings") as ms:
            ms.return_value.smtp_host = None
            ms.return_value.smtp_username = None
            ms.return_value.smtp_password = None
            ms.return_value.resend_api_key = None
            ms.return_value.from_email_address = None
            svc = EmailService()
        result = await svc._send("to@example.com", "Sub", "<p>Body</p>")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_email_compat_alias_works(self):
        """send_email() public alias must delegate to _send."""
        from app.services.email_service import EmailService
        with patch("app.services.email_service.get_settings") as ms:
            ms.return_value.smtp_host = None
            ms.return_value.smtp_username = None
            ms.return_value.smtp_password = None
            ms.return_value.resend_api_key = None
            ms.return_value.from_email_address = None
            svc = EmailService()

        svc._send = AsyncMock(return_value=True)
        result = await svc.send_email("to@example.com", "Sub", html_content="<p>Hi</p>")
        assert result is True
        svc._send.assert_called_once_with("to@example.com", "Sub", "<p>Hi</p>")
