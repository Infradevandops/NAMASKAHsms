"""Test sidebar navigation titles display correctly."""

import pytest
from bs4 import BeautifulSoup


def test_sidebar_titles_not_showing_internal_keys():
    """Verify sidebar shows user-friendly titles, not i18n keys."""
    # Read the sidebar HTML
    with open("templates/components/sidebar.html", "r") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # Find all nav items with data-i18n attributes
    nav_items = soup.find_all("span", attrs={"data-i18n": True})

    # Expected user-friendly titles (fallback text)
    expected_titles = {
        "Dashboard",
        "SMS Verification",
        "Voice Verification",
        "Number Rentals",
        "History",
        "Wallet",
        "API Keys",
        "API Documentation",
        "Webhooks",
        "Whitelabel",
        "Telegram",
        "Push Setup",
        "Insights",
        "Analytics",
        "Support",
        "Profile",
        "Notifications",
        "Settings",
        "Referrals",
        "Logout",
    }

    # Check each nav item has proper fallback text
    for item in nav_items:
        text = item.get_text(strip=True)

        # Should not show internal keys like "common.history", "developer.api_keys"
        assert "." not in text or text in ["12.01"], f"Found internal key: {text}"

        # Should not show underscores like "api_keys", "push_setup"
        assert "_" not in text, f"Found underscore in title: {text}"

    # Verify expected titles are present
    all_text = soup.get_text()
    for title in expected_titles:
        assert title in all_text, f"Missing expected title: {title}"


def test_sidebar_no_duplicate_referrals():
    """Verify 'Referrals' appears only once in sidebar."""
    with open("templates/components/sidebar.html", "r") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # Find all links with "referrals" in href
    referral_links = soup.find_all("a", href="/referrals")

    assert (
        len(referral_links) == 1
    ), f"Found {len(referral_links)} referral links, expected 1"


def test_sidebar_tier_badges_present():
    """Verify tier badges are present for premium features."""
    with open("templates/components/sidebar.html", "r") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # Features that should have tier badges
    premium_features = [
        ("voice-verify", "Premium"),
        ("rentals", "Premium"),
        ("api-keys", "Pro+"),
        ("api-documentation", "Pro+"),
        ("webhooks-management", "PAYG+"),
        ("whitelabel", "Pro+"),
    ]

    for page, expected_badge in premium_features:
        nav_item = soup.find("a", attrs={"data-page": page})
        assert nav_item is not None, f"Missing nav item for {page}"

        badge = nav_item.find("span", class_="tier-badge")
        assert badge is not None, f"Missing tier badge for {page}"
        assert (
            expected_badge in badge.get_text()
        ), f"Wrong badge for {page}: {badge.get_text()}"


def test_sidebar_sections_present():
    """Verify all sidebar sections are present."""
    with open("templates/components/sidebar.html", "r") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # Expected section titles
    sections = ["Services", "Finance", "Developer", "Integrations", "Account"]

    section_titles = soup.find_all("div", class_="nav-section-title")
    section_texts = [s.get_text(strip=True) for s in section_titles]

    for section in sections:
        assert section in section_texts, f"Missing section: {section}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
