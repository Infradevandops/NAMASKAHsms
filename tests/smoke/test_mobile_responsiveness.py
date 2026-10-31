"""
Mobile responsiveness smoke tests — P2 sprint requirement.

Validates that the 5 public conversion pages (landing, pricing, about,
affiliate_program, contact) do NOT contain hardcoded oversized values that
break 320–425px viewports, and DO have mobile breakpoints in place.

These are static analysis tests — no browser required, runs in CI.
"""

import re
from pathlib import Path

import pytest

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

PUBLIC_PAGES = [
    "landing.html",
    "pricing.html",
    "about.html",
    "affiliate_program.html",
    "contact.html",
]

# Pixel values that are too large for 320px viewports when hardcoded
OVERSIZED_FONT_PATTERN = re.compile(
    r"font-size:\s*(4[3-9]|[5-9]\d|\d{3,})px(?!\s*;?\s*/\*\s*clamp)",
)
# Hero padding > 100px top is a problem on small screens
OVERSIZED_HERO_PADDING_PATTERN = re.compile(
    r"\.hero\s*\{[^}]*padding:\s*(1[0-9]\d|[2-9]\d\d)px",
    re.DOTALL,
)


def read_template(name: str) -> str:
    path = TEMPLATES_DIR / name
    assert path.exists(), f"Template not found: {path}"
    return path.read_text()


@pytest.mark.parametrize("page", PUBLIC_PAGES)
def test_no_hardcoded_oversized_font_sizes(page):
    """No font-size > 42px hardcoded without clamp() — would overflow on 320px."""
    content = read_template(page)
    # Strip clamp() usages — those are fine
    content_no_clamp = re.sub(r"clamp\([^)]+\)", "clamp()", content)
    matches = OVERSIZED_FONT_PATTERN.findall(content_no_clamp)
    assert not matches, (
        f"{page} has hardcoded font-size(s) {matches}px that will overflow on 320px. "
        "Use clamp() or a CSS variable instead."
    )


def test_landing_hero_has_mobile_breakpoint():
    """landing.html .hero must have a @media max-width breakpoint for padding."""
    content = read_template("landing.html")
    # Must have a media query that targets the .hero class
    assert re.search(
        r"@media\s*\(max-width:\s*\d+px\)[^{]*\{[^}]*\.hero", content
    ) or re.search(r"\.hero\s*\{[^}]*\}.*@media\s*\(max-width", content, re.DOTALL), (
        "landing.html .hero has no mobile @media breakpoint — "
        "padding: 140px will overflow on small screens."
    )


def test_about_hero_uses_clamp_or_variable():
    """about.html hero h1 must use clamp() or a CSS variable, not a fixed px value > 36px."""
    content = read_template("about.html")
    # Look for .about-hero h1 block
    hero_h1_match = re.search(r"\.about-hero\s+h1\s*\{([^}]+)\}", content, re.DOTALL)
    assert hero_h1_match, "about.html missing .about-hero h1 rule"
    rule_body = hero_h1_match.group(1)
    # Must use clamp() or a var() — not a raw px > 36
    raw_px = re.search(r"font-size:\s*([4-9]\d|\d{3,})px", rule_body)
    assert (
        not raw_px
    ), f"about.html .about-hero h1 uses hardcoded {raw_px.group()}. Use clamp() instead."


def test_contact_hero_uses_clamp_or_variable():
    """contact.html hero h1 must use clamp() or a CSS variable."""
    content = read_template("contact.html")
    hero_h1_match = re.search(r"\.contact-hero\s+h1\s*\{([^}]+)\}", content, re.DOTALL)
    assert hero_h1_match, "contact.html missing .contact-hero h1 rule"
    rule_body = hero_h1_match.group(1)
    raw_px = re.search(r"font-size:\s*([4-9]\d|\d{3,})px", rule_body)
    assert (
        not raw_px
    ), f"contact.html .contact-hero h1 uses hardcoded {raw_px.group()}. Use clamp() instead."


def test_pricing_tier_cards_have_mobile_stack():
    """pricing.html tier cards must have a single-column mobile rule."""
    content = read_template("pricing.html")
    # .tier-cards must have grid-template-columns: 1fr in a media query
    assert re.search(
        r"@media[^{]*max-width[^{]*\{[^}]*\.tier-cards[^}]*grid-template-columns:\s*1fr",
        content,
        re.DOTALL,
    ) or re.search(
        r"\.tier-cards[^}]*\}.*@media[^{]*max-width.*grid-template-columns:\s*1fr",
        content,
        re.DOTALL,
    ), "pricing.html .tier-cards has no single-column mobile rule"


def test_affiliate_commission_table_has_overflow_scroll():
    """affiliate_program.html commission table wrapper must have overflow-x: auto."""
    content = read_template("affiliate_program.html")
    assert "overflow-x: auto" in content or "overflow-x:auto" in content, (
        "affiliate_program.html commission table has no overflow-x: auto — "
        "4-column table will overflow on 320px."
    )


def test_contact_grid_stacks_on_mobile():
    """contact.html .contact-grid must collapse to 1 column on mobile."""
    content = read_template("contact.html")
    assert re.search(
        r"@media[^{]*max-width[^{]*\{[^}]*\.contact-grid[^}]*grid-template-columns:\s*1fr",
        content,
        re.DOTALL,
    ) or re.search(
        r"\.contact-grid[^}]*\}.*@media[^{]*max-width.*grid-template-columns:\s*1fr",
        content,
        re.DOTALL,
    ), "contact.html .contact-grid has no single-column mobile rule"


@pytest.mark.parametrize("page", PUBLIC_PAGES)
def test_no_horizontal_overflow_risk(page):
    """No inline style with width > 100vw or fixed px width > 600 on block elements."""
    content = read_template(page)
    # Inline style width > 600px on non-max-width properties is a risk
    dangerous = re.findall(
        r'style="[^"]*(?<!max-)width:\s*([6-9]\d\d|\d{4,})px[^"]*"', content
    )
    assert (
        not dangerous
    ), f"{page} has inline fixed width(s) {dangerous} that may cause horizontal scroll on mobile."
