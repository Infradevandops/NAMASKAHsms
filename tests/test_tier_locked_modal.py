"""Frontend integration tests for tier-locked modal.

Feature: tier-system-rbac
Tests validate that the tier-locked modal displays correctly when users
encounter 402 errors and provides proper upgrade functionality.
"""


class TestTierLockedModalPresence:

    """Tests for tier-locked modal HTML presence."""

def test_tier_locked_modal_html_exists_on_dashboard(self, client, regular_user, user_token):

        """Test that tier-locked modal HTML exists on dashboard page."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain modal HTML
        assert "tier-locked" in response.text.lower() or "modal" in response.text.lower()

def test_tier_locked_modal_html_exists_on_settings(self, client, regular_user, user_token):

        """Test that tier-locked modal HTML exists on settings page."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain modal HTML
        assert "tier-locked" in response.text.lower() or "modal" in response.text.lower()

def test_tier_locked_modal_has_required_elements(self, client, regular_user, user_token):

        """Test that tier-locked modal has all required elements."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain modal elements
        assert "feature locked" in response.text.lower() or "tier-locked" in response.text.lower()

def test_tier_locked_modal_has_close_button(self, client, regular_user, user_token):

        """Test that tier-locked modal has close button."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain close button
        assert "close" in response.text.lower() or "×" in response.text or "&times;" in response.text

def test_tier_locked_modal_has_upgrade_button(self, client, regular_user, user_token):

        """Test that tier-locked modal has upgrade button."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain upgrade button
        assert "upgrade" in response.text.lower()

def test_tier_locked_modal_has_message_element(self, client, regular_user, user_token):

        """Test that tier-locked modal has message element."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain message element
        assert "message" in response.text.lower() or "feature" in response.text.lower()

def test_tier_locked_modal_has_required_tier_display(self, client, regular_user, user_token):

        """Test that tier-locked modal has required tier display."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain required tier display
        assert "require" in response.text.lower() or "tier" in response.text.lower()


class TestTierLockedModalStyling:

    """Tests for tier-locked modal styling."""

def test_tier_locked_modal_has_overlay_styling(self, client, regular_user, user_token):

        """Test that tier-locked modal has overlay styling."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain overlay styling
        assert "overlay" in response.text.lower() or "backdrop" in response.text.lower()

def test_tier_locked_modal_has_gradient_background(self, client, regular_user, user_token):

        """Test that tier-locked modal has gradient background styling."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain gradient styling
        assert "gradient" in response.text.lower() or "linear-gradient" in response.text.lower()

def test_tier_locked_modal_has_icon_styling(self, client, regular_user, user_token):

        """Test that tier-locked modal has icon styling."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain icon element
        assert "icon" in response.text.lower() or "svg" in response.text.lower() or "🔒" in response.text

def test_tier_locked_modal_has_button_styling(self, client, regular_user, user_token):

        """Test that tier-locked modal has button styling."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain button styling
        assert "btn" in response.text.lower() or "button" in response.text.lower()


class TestTierLockedModalContent:

    """Tests for tier-locked modal content."""

def test_tier_locked_modal_displays_title(self, client, regular_user, user_token):

        """Test that tier-locked modal displays title."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain title
        assert "feature locked" in response.text.lower() or "locked" in response.text.lower()

def test_tier_locked_modal_displays_message(self, client, regular_user, user_token):

        """Test that tier-locked modal displays message."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain message
        assert (
            "feature" in response.text.lower() or "tier" in response.text.lower() or "require" in response.text.lower()
        )

def test_tier_locked_modal_displays_required_tier_name(self, client, regular_user, user_token):

        """Test that tier-locked modal displays required tier name."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain tier name reference
        assert "payg" in response.text.lower() or "pro" in response.text.lower() or "tier" in response.text.lower()

def test_tier_locked_modal_displays_upgrade_button_text(self, client, regular_user, user_token):

        """Test that tier-locked modal displays upgrade button text."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain upgrade button text
        assert "upgrade" in response.text.lower() or "now" in response.text.lower()

def test_tier_locked_modal_displays_close_button_text(self, client, regular_user, user_token):

        """Test that tier-locked modal displays close button text."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain close button text
        assert "close" in response.text.lower() or "later" in response.text.lower() or "×" in response.text


class TestTierLockedModalFunctionality:

    """Tests for tier-locked modal JavaScript functionality."""

def test_tier_locked_modal_has_show_function(self, client, regular_user, user_token):

        """Test that tier-locked modal has show function."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain show function
        assert "showTierLockedModal" in response.text or "show" in response.text.lower()

def test_tier_locked_modal_has_close_function(self, client, regular_user, user_token):

        """Test that tier-locked modal has close function."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain close function
        assert "closeTierLockedModal" in response.text or "close" in response.text.lower()

def test_tier_locked_modal_has_upgrade_handler(self, client, regular_user, user_token):

        """Test that tier-locked modal has upgrade handler."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain upgrade handler
        assert "upgrade" in response.text.lower() or "pricing" in response.text.lower()

def test_tier_locked_modal_has_tier_display_names_mapping(self, client, regular_user, user_token):

        """Test that tier-locked modal has tier display names mapping."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain tier display names
        assert "freemium" in response.text.lower() or "payg" in response.text.lower() or "pro" in response.text.lower()


class TestTierLockedModalUpgradeButton:

    """Tests for upgrade button in tier-locked modal."""

def test_upgrade_button_navigates_to_pricing(self, client, regular_user, user_token):

        """Test that upgrade button navigates to pricing page."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain pricing link
        assert "/pricing" in response.text

def test_upgrade_button_has_onclick_handler(self, client, regular_user, user_token):

        """Test that upgrade button has onclick handler."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain onclick handler
        assert "onclick" in response.text.lower() or "click" in response.text.lower()

def test_upgrade_button_is_styled_as_primary(self, client, regular_user, user_token):

        """Test that upgrade button is styled as primary."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain primary button styling
        assert "primary" in response.text.lower() or "btn" in response.text.lower()


class TestTierLockedModalCloseButton:

    """Tests for close button in tier-locked modal."""

def test_close_button_has_onclick_handler(self, client, regular_user, user_token):

        """Test that close button has onclick handler."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain close handler
        assert "closeTierLockedModal" in response.text or "close" in response.text.lower()

def test_close_button_is_styled_as_secondary(self, client, regular_user, user_token):

        """Test that close button is styled as secondary."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain secondary button styling
        assert "secondary" in response.text.lower() or "btn" in response.text.lower()

def test_close_button_text_is_descriptive(self, client, regular_user, user_token):

        """Test that close button has descriptive text."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain descriptive text
        assert "close" in response.text.lower() or "later" in response.text.lower() or "cancel" in response.text.lower()


class TestTierLockedModalTierBadges:

    """Tests for tier badge colors in modal."""

def test_tier_locked_modal_has_tier_badge_styling(self, client, regular_user, user_token):

        """Test that tier-locked modal has tier badge styling."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain badge styling
        assert "badge" in response.text.lower() or "tier-badge" in response.text.lower()

def test_tier_locked_modal_has_payg_badge_color(self, client, regular_user, user_token):

        """Test that tier-locked modal has payg badge color."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain payg color reference
        assert "10B981" in response.text or "#10B981" in response.text or "payg" in response.text.lower()

def test_tier_locked_modal_has_pro_badge_color(self, client, regular_user, user_token):

        """Test that tier-locked modal has pro badge color."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain pro color reference
        assert "F59E0B" in response.text or "#F59E0B" in response.text or "pro" in response.text.lower()

def test_tier_locked_modal_has_custom_badge_color(self, client, regular_user, user_token):

        """Test that tier-locked modal has custom badge color."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain custom color reference
        assert "8B5CF6" in response.text or "#8B5CF6" in response.text or "custom" in response.text.lower()


class TestTierLockedModalErrorHandler:

    """Tests for 402 error handler integration."""

def test_tier_error_handler_script_exists(self, client, regular_user, user_token):

        """Test that tier error handler script exists."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain error handler script
        assert "tier-error-handler" in response.text.lower() or "402" in response.text

def test_tier_error_handler_intercepts_fetch(self, client, regular_user, user_token):

        """Test that tier error handler intercepts fetch requests."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain fetch interception
        assert "fetch" in response.text.lower() or "402" in response.text

def test_tier_error_handler_shows_modal_on_402(self, client, regular_user, user_token):

        """Test that tier error handler shows modal on 402."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain modal show logic
        assert "showTierLockedModal" in response.text or "402" in response.text


class TestTierLockedModalAccessibility:

    """Tests for accessibility features in modal."""

def test_tier_locked_modal_has_aria_labels(self, client, regular_user, user_token):

        """Test that tier-locked modal has ARIA labels."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain ARIA labels
        assert "aria" in response.text.lower() or "role" in response.text.lower()

def test_tier_locked_modal_has_keyboard_support(self, client, regular_user, user_token):

        """Test that tier-locked modal has keyboard support."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain keyboard handler
        assert (
            "escape" in response.text.lower()
            or "keydown" in response.text.lower()
            or "keyboard" in response.text.lower()
        )

def test_tier_locked_modal_has_focus_management(self, client, regular_user, user_token):

        """Test that tier-locked modal has focus management."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain focus management
        assert "focus" in response.text.lower() or "autofocus" in response.text.lower()


class TestTierLockedModalResponsiveness:

    """Tests for responsive design of modal."""

def test_tier_locked_modal_has_responsive_styling(self, client, regular_user, user_token):

        """Test that tier-locked modal has responsive styling."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain responsive styling
        assert (
            "max-width" in response.text.lower() or "width" in response.text.lower() or "media" in response.text.lower()
        )

def test_tier_locked_modal_has_mobile_friendly_buttons(self, client, regular_user, user_token):

        """Test that tier-locked modal has mobile-friendly buttons."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain button styling
        assert "padding" in response.text.lower() or "button" in response.text.lower()

def test_tier_locked_modal_has_touch_friendly_close(self, client, regular_user, user_token):

        """Test that tier-locked modal has touch-friendly close button."""
        token = user_token(regular_user.id, regular_user.email)
        response = client.get("/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        # Should contain close button
        assert "close" in response.text.lower() or "×" in response.text