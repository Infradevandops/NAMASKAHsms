"""Tests for email utilities."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.utils.email import (
    EmailTemplate, EmailService, get_email_service,
    WELCOME_TEMPLATE, VERIFICATION_COMPLETE_TEMPLATE,
    PASSWORD_RESET_TEMPLATE, RECEIPT_TEMPLATE
)


def test_email_template_creation():
    """Test email template creation and rendering."""
    template = EmailTemplate(
        subject="Test Subject - $name",
        html_body="<h1>Hello $name</h1><p>Your email is $email</p>"
    )
    
    assert template.subject == "Test Subject - $name"
    assert "<h1>Hello $name</h1>" in template.html_body
    assert template.text_body is not None  # Auto-generated from HTML


def test_email_template_rendering():
    """Test email template rendering with variables."""
    template = EmailTemplate(
        subject="Welcome $name",
        html_body="<p>Hello $name, your email is $email</p>"
    )
    
    rendered = template.render(name="John", email="john@example.com")
    
    assert rendered["subject"] == "Welcome John"
    assert "Hello John" in rendered["html_body"]
    assert "john@example.com" in rendered["html_body"]
    assert "Hello John" in rendered["text_body"]


def test_html_to_text_conversion():
    """Test HTML to text conversion."""
    template = EmailTemplate(
        subject="Test",
        html_body="<h1>Title</h1><p>Paragraph with <strong>bold</strong> text</p>"
    )
    
    # Should strip HTML tags
    assert "<h1>" not in template.text_body
    assert "<p>" not in template.text_body
    assert "Title" in template.text_body
    assert "Paragraph" in template.text_body


@pytest.fixture
def mock_smtp():
    """Mock SMTP server."""
    with patch('app.utils.email.smtplib.SMTP') as mock:
        smtp_instance = MagicMock()
        mock.return_value.__enter__.return_value = smtp_instance
        yield smtp_instance


@pytest.mark.asyncio
async def test_email_service_send_email(mock_smtp):
    """Test email service send functionality."""
    email_service = EmailService()
    
    result = await email_service.send_email(
        to_email="test@example.com",
        subject="Test Subject",
        body="Test body",
        is_html=True
    )
    
    assert result is True
    mock_smtp.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_email_service_send_template_email(mock_smtp):
    """Test sending email with template."""
    email_service = EmailService()
    template = EmailTemplate(
        subject="Hello $name",
        html_body="<p>Welcome $name!</p>"
    )
    
    result = await email_service.send_template_email(
        to_email="test@example.com",
        template=template,
        template_vars={"name": "John"}
    )
    
    assert result is True
    mock_smtp.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_email_service_failure_handling():
    """Test email service failure handling."""
    with patch('app.utils.email.smtplib.SMTP') as mock_smtp:
        mock_smtp.side_effect = Exception("SMTP Error")
        
        email_service = EmailService()
        result = await email_service.send_email(
            to_email="test@example.com",
            subject="Test",
            body="Test"
        )
        
        assert result is False


def test_predefined_templates():
    """Test predefined email templates."""
    # Test welcome template
    welcome_rendered = WELCOME_TEMPLATE.render(
        name="John",
        email="john@example.com",
        credits="100"
    )
    assert "Welcome to Namaskah SMS!" in welcome_rendered["html_body"]
    assert "John" in welcome_rendered["subject"]
    
    # Test verification complete template
    verification_rendered = VERIFICATION_COMPLETE_TEMPLATE.render(
        name="John",
        service_name="Telegram",
        phone_number="+1234567890",
        cost="1.50",
        completed_at="2024-01-01 10:00:00"
    )
    assert "Verification Completed" in verification_rendered["html_body"]
    assert "Telegram" in verification_rendered["subject"]
    
    # Test password reset template
    reset_rendered = PASSWORD_RESET_TEMPLATE.render(
        name="John",
        reset_code="123456"
    )
    assert "Password Reset" in reset_rendered["html_body"]
    assert "123456" in reset_rendered["html_body"]
    
    # Test receipt template
    receipt_rendered = RECEIPT_TEMPLATE.render(
        name="John",
        amount="100.00",
        transaction_id="txn_123",
        date="2024-01-01",
        payment_method="Paystack",
        credits_added="100"
    )
    assert "Payment Receipt" in receipt_rendered["html_body"]
    assert "100.00" in receipt_rendered["html_body"]


def test_get_email_service():
    """Test email service factory function."""
    service = get_email_service()
    assert isinstance(service, EmailService)


if __name__ == "__main__":
    pytest.main([__file__])