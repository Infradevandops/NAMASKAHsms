from unittest.mock import MagicMock

import pytest

from app.models.pricing_template import PricingTemplate, UserPricingAssignment
from app.services.pricing_template_service import PricingTemplateService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return PricingTemplateService(mock_db)


def test_get_active_template_no_assignment(service, mock_db):
    # Setup mock
    template = PricingTemplate(id=1, name="Default", is_active=True, region="US")
    # First query (assignment) returns None
    mock_db.query.return_value.filter.return_value.first.side_effect = [None, template]

    result = service.get_active_template(user_id=123)

    assert result == template
    # Verify queries
    # 1. UserAssignment
    # 2. PricingTemplate (filtered by active & region)
    assert mock_db.query.call_count >= 2


def test_get_active_template_with_assignment(service, mock_db):
    assignment = UserPricingAssignment(user_id=123, template_id=99)
    template = PricingTemplate(id=99, name="Test Schema", is_active=False)

    # Mock chain
    # 1. UserAssignment -> returns assignment
    # 2. PricingTemplate (by ID) -> returns template
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        assignment,
        template,
    ]

    result = service.get_active_template(user_id=123)

    assert result == template
    assert result.id == 99


def test_create_template(service, mock_db):
    # Mock existing name check -> None
    mock_db.query.return_value.filter.return_value.first.return_value = None

    tiers_data = [
        {"tier_name": "Free", "monthly_price": 0, "included_quota": 10},
        {"tier_name": "Pro", "monthly_price": 29, "included_quota": 100},
    ]

    result = service.create_template(
        name="New Pricing",
        description="2026 Pricing",
        region="US",
        currency="USD",
        tiers=tiers_data,
        admin_user_id=1,
    )

    assert isinstance(result, PricingTemplate)
    assert result.name == "New Pricing"
    # Check if added to DB
    assert mock_db.add.call_count >= 1 + 2 + 1  # Template + 2 Tiers + History
    assert mock_db.commit.called


def test_create_template_duplicate_name(service, mock_db):
    # Mock existing
    mock_db.query.return_value.filter.return_value.first.return_value = PricingTemplate()

    with pytest.raises(ValueError, match="already exists"):
        service.create_template(
            name="Existing",
            description="desc",
            region="US",
            currency="USD",
            tiers=[],
            admin_user_id=1,
        )


def test_activate_template(service, mock_db):
    # Mock template to activate
    new_template = PricingTemplate(id=2, name="New", region="US", is_active=False)

    # Mock current active
    current_active = PricingTemplate(id=1, name="Old", region="US", is_active=True)

    # get_template(2) -> new_template
    # get_active_template -> current_active
    # get_active_template implementation queries:
    #   db.query(PricingTemplate).filter(...).first()

    # We need to orchestrate the mock returns for multiple calls to query().filter().first()
    # 1. get_template(2)
    # 2. get_active_template(region) -> UserAssignment check (None) -> Active check (current_active)

    # Simplified: Mock get_template and get_active_template directly on the service instance?
    # But methods call self.db directly.

    # Let's rely on side_effect on db query

    # Sequence:
    # 1. get_template(id)
    # 2. get_active_template -> UserAssignment (if user_id provided? No, activate_template calls get_active_template(region))
    #    get_active_template(region) queries PricingTemplate filter(active=True, region=...)

    mock_filter = mock_db.query.return_value.filter.return_value
    mock_filter.first.side_effect = [
        new_template,  # get_template(2)
        current_active,  # get_active_template("US")
    ]

    service.activate_template(template_id=2, admin_user_id=1)

    assert current_active.is_active is False
    assert new_template.is_active is True
    assert mock_db.commit.called


def test_delete_template_success(service, mock_db):
    template = PricingTemplate(id=1, is_active=False)

    # Mock sequence:
    # 1. get_template
    # 2. assigned_users count

    mock_filter = mock_db.query.return_value.filter.return_value
    mock_filter.first.return_value = template
    mock_filter.count.return_value = 0

    result = service.delete_template(1, admin_user_id=1)

    assert result is True
    assert mock_db.delete.called_with(template)


def test_delete_template_active_fails(service, mock_db):
    template = PricingTemplate(id=1, is_active=True)
    mock_db.query.return_value.filter.return_value.first.return_value = template

    with pytest.raises(ValueError, match="Cannot delete active template"):
        service.delete_template(1, admin_user_id=1)


def test_assign_user_to_template(service, mock_db):
    template = PricingTemplate(id=10)
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        template,  # get_template
        None,  # Existing assignment check
    ]

    service.assign_user_to_template(user_id=5, template_id=10)

    # Verify add assignment
    assert mock_db.add.called
    assert mock_db.commit.called
