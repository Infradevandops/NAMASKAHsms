"""Pricing Template Service"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import List, Optional
from app.models.pricing_template import (
    PricingTemplate,
    TierPricing,
    PricingHistory,
    UserPricingAssignment,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class PricingTemplateService:
    """Service for managing pricing templates"""

    def __init__(self, db: Session):
        self.db = db

    def get_active_template(
        self, region: str = "US", user_id: int = None
    ) -> Optional[PricingTemplate]:
        """
        Get active pricing template for region
        If user has specific assignment (A/B test), return that instead
        """
        # Check if user has specific template assignment
        if user_id:
            assignment = (
                self.db.query(UserPricingAssignment)
                .filter(UserPricingAssignment.user_id == user_id)
                .first()
            )

            if assignment:
                return (
                    self.db.query(PricingTemplate)
                    .filter(PricingTemplate.id == assignment.template_id)
                    .first()
                )

        # Return active template for region
        return (
            self.db.query(PricingTemplate)
            .filter(and_(PricingTemplate.is_active == True, PricingTemplate.region == region))
            .first()
        )

    def list_templates(self, region: str = None) -> List[PricingTemplate]:
        """List all pricing templates, optionally filtered by region"""
        query = self.db.query(PricingTemplate)

        if region:
            query = query.filter(PricingTemplate.region == region)

        return query.order_by(
            PricingTemplate.is_active.desc(), PricingTemplate.created_at.desc()
        ).all()

    def get_template(self, template_id: int) -> Optional[PricingTemplate]:
        """Get specific template by ID"""
        return self.db.query(PricingTemplate).filter(PricingTemplate.id == template_id).first()

    def activate_template(
        self, template_id: int, admin_user_id: int, notes: str = None
    ) -> PricingTemplate:
        """
        Activate a pricing template (deactivates others in same region)
        """
        template = self.get_template(template_id)

        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Deactivate current active template in same region
        current_active = self.get_active_template(template.region)

        if current_active and current_active.id != template_id:
            current_active.is_active = False

            # Log deactivation
            self._log_history(
                template_id=current_active.id,
                action="deactivated",
                changed_by=admin_user_id,
                notes=f"Deactivated to activate template '{template.name}'",
            )

        # Activate new template
        template.is_active = True
        self.db.commit()

        # Log activation
        self._log_history(
            template_id=template_id,
            action="activated",
            previous_template_id=current_active.id if current_active else None,
            changed_by=admin_user_id,
            notes=notes or f"Activated template '{template.name}'",
        )

        logger.info(
            f"Activated pricing template '{template.name}' (ID: {template_id}) by user {admin_user_id}"
        )
        return template

    def create_template(
        self,
        name: str,
        description: str,
        region: str,
        currency: str,
        tiers: List[dict],
        admin_user_id: int,
        **kwargs,
    ) -> PricingTemplate:
        """Create new pricing template"""

        # Check if name already exists
        existing = self.db.query(PricingTemplate).filter(PricingTemplate.name == name).first()

        if existing:
            raise ValueError(f"Template with name '{name}' already exists")

        # Create template
        template = PricingTemplate(
            name=name,
            description=description,
            region=region,
            currency=currency,
            created_by=admin_user_id,
            is_active=False,
            **kwargs,
        )
        self.db.add(template)
        self.db.flush()

        # Add tier pricing
        for tier_data in tiers:
            tier = TierPricing(template_id=template.id, **tier_data)
            self.db.add(tier)

        self.db.commit()

        # Log creation
        self._log_history(
            template_id=template.id,
            action="created",
            changed_by=admin_user_id,
            notes=f"Created template '{name}' with {len(tiers)} tiers",
        )

        logger.info(f"Created pricing template '{name}' (ID: {template.id})")
        return template

    def update_template(self, template_id: int, admin_user_id: int, **updates) -> PricingTemplate:
        """Update template metadata (not tiers)"""
        template = self.get_template(template_id)

        if not template:
            raise ValueError(f"Template {template_id} not found")

        if template.is_active:
            raise ValueError("Cannot update active template. Deactivate first.")

        # Update fields
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)

        self.db.commit()

        # Log update
        self._log_history(
            template_id=template_id,
            action="updated",
            changed_by=admin_user_id,
            notes=f"Updated template fields: {', '.join(updates.keys())}",
        )

        return template

    def clone_template(
        self, template_id: int, new_name: str, admin_user_id: int
    ) -> PricingTemplate:
        """Clone existing template with new name"""
        original = self.get_template(template_id)

        if not original:
            raise ValueError(f"Template {template_id} not found")

        # Create new template
        new_template = PricingTemplate(
            name=new_name,
            description=f"Cloned from '{original.name}'",
            region=original.region,
            currency=original.currency,
            created_by=admin_user_id,
            is_active=False,
            metadata=original.metadata,
        )
        self.db.add(new_template)
        self.db.flush()

        # Clone tiers
        for tier in original.tiers:
            new_tier = TierPricing(
                template_id=new_template.id,
                tier_name=tier.tier_name,
                monthly_price=tier.monthly_price,
                included_quota=tier.included_quota,
                overage_rate=tier.overage_rate,
                features=tier.features,
                api_keys_limit=tier.api_keys_limit,
                display_order=tier.display_order,
            )
            self.db.add(new_tier)

        self.db.commit()

        # Log creation
        self._log_history(
            template_id=new_template.id,
            action="created",
            changed_by=admin_user_id,
            notes=f"Cloned from template '{original.name}' (ID: {template_id})",
        )

        logger.info(
            f"Cloned template {template_id} to new template '{new_name}' (ID: {new_template.id})"
        )
        return new_template

    def delete_template(self, template_id: int, admin_user_id: int) -> bool:
        """Delete template (only if inactive and no users assigned)"""
        template = self.get_template(template_id)

        if not template:
            raise ValueError(f"Template {template_id} not found")

        if template.is_active:
            raise ValueError("Cannot delete active template. Deactivate first.")

        # Check if any users are assigned
        assigned_users = (
            self.db.query(UserPricingAssignment)
            .filter(UserPricingAssignment.template_id == template_id)
            .count()
        )

        if assigned_users > 0:
            raise ValueError(f"Cannot delete template with {assigned_users} assigned users")

        # Log deletion before deleting
        self._log_history(
            template_id=template_id,
            action="deleted",
            changed_by=admin_user_id,
            notes=f"Deleted template '{template.name}'",
        )

        # Delete template (cascades to tiers)
        self.db.delete(template)
        self.db.commit()

        logger.info(f"Deleted pricing template '{template.name}' (ID: {template_id})")
        return True

    def rollback_to_previous(self, admin_user_id: int, region: str = "US") -> PricingTemplate:
        """Rollback to previous active pricing template"""

        # Get last deactivation in this region
        last_deactivation = (
            self.db.query(PricingHistory)
            .join(PricingTemplate, PricingHistory.template_id == PricingTemplate.id)
            .filter(and_(PricingHistory.action == "deactivated", PricingTemplate.region == region))
            .order_by(PricingHistory.changed_at.desc())
            .first()
        )

        if not last_deactivation or not last_deactivation.template_id:
            raise ValueError("No previous template to rollback to")

        return self.activate_template(
            template_id=last_deactivation.template_id,
            admin_user_id=admin_user_id,
            notes="Rollback to previous pricing",
        )

    def assign_user_to_template(self, user_id: int, template_id: int, assigned_by: str = "admin"):
        """Assign specific template to user (for A/B testing)"""

        # Check if template exists
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Create or update assignment
        assignment = (
            self.db.query(UserPricingAssignment)
            .filter(UserPricingAssignment.user_id == user_id)
            .first()
        )

        if assignment:
            assignment.template_id = template_id
            assignment.assigned_by = assigned_by
            assignment.assigned_at = datetime.utcnow()
        else:
            assignment = UserPricingAssignment(
                user_id=user_id, template_id=template_id, assigned_by=assigned_by
            )
            self.db.add(assignment)

        self.db.commit()
        logger.info(f"Assigned user {user_id} to template {template_id} by {assigned_by}")
        return assignment

    def get_pricing_history(self, template_id: int = None, limit: int = 50) -> List[PricingHistory]:
        """Get pricing change history"""
        query = self.db.query(PricingHistory)

        if template_id:
            query = query.filter(PricingHistory.template_id == template_id)

        return query.order_by(PricingHistory.changed_at.desc()).limit(limit).all()

    def _log_history(
        self,
        template_id: int,
        action: str,
        changed_by: int,
        previous_template_id: int = None,
        notes: str = None,
    ):
        """Log pricing change to history"""
        history = PricingHistory(
            template_id=template_id,
            action=action,
            previous_template_id=previous_template_id,
            changed_by=changed_by,
            notes=notes,
        )
        self.db.add(history)
        self.db.commit()
