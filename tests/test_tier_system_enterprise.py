from app.core.tier_helpers import has_tier_access


def test_tier_hierarchy():
    assert has_tier_access("custom", "freemium") == True
    assert has_tier_access("pro", "custom") == False
    assert has_tier_access("payg", "payg") == True


def test_tier_display_names():
    from app.core.tier_helpers import get_tier_display_name

    assert get_tier_display_name("freemium") == "Freemium"
    assert get_tier_display_name("payg") == "Pay-As-You-Go"
    assert get_tier_display_name("pro") == "Pro"
    assert get_tier_display_name("custom") == "Custom"
    assert get_tier_display_name("invalid") == "Unknown"


def test_is_subscribed():
    from app.core.tier_helpers import is_subscribed

    assert is_subscribed("freemium") == False
    assert is_subscribed("payg") == True
    assert is_subscribed("pro") == True
    assert is_subscribed("custom") == True


def test_tier_hierarchy_edge_cases():
    assert has_tier_access("freemium", "freemium") == True
    assert has_tier_access("custom", "custom") == True
    assert has_tier_access("freemium", "custom") == False


def test_get_user_tier_with_db():
    from app.core.tier_helpers import TIER_HIERARCHY

    # Test TIER_HIERARCHY constant
    assert TIER_HIERARCHY["freemium"] == 0
    assert TIER_HIERARCHY["payg"] == 1
    assert TIER_HIERARCHY["pro"] == 2
    assert TIER_HIERARCHY["custom"] == 3
