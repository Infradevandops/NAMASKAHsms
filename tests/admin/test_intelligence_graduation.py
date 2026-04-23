import pytest
from datetime import date, datetime, timezone
from sqlalchemy import select, func
from app.services.target_tracking_service import TargetTrackingService
from app.services.audit_service import AuditService
from app.models.monthly_target import MonthlyTarget
from app.models.daily_user_snapshot import DailyUserSnapshot
from app.models.audit_log import AuditLog
from app.models.user import User

@pytest.mark.asyncio
async def test_target_tracking_persistence(db):
    """Verify that TargetTrackingService correctly persists and retrieves targets."""
    service = TargetTrackingService(db)
    
    # 1. Test auto-generation of active target
    target = await service.get_active_target()
    assert target.target_count == 350
    assert target.month == datetime.now(timezone.utc).strftime("%Y-%m")
    
    # 2. Test manual target creation
    custom_target = MonthlyTarget(month="2025-12", target_count=500, is_active=True)
    db.add(custom_target)
    db.commit() # Sync commit
    
    fetched = await service.get_active_target("2025-12")
    assert fetched.target_count == 500

@pytest.mark.asyncio
async def test_daily_snapshot_recording(db):
    """Verify that midnight snapshots correctly capture platform state."""
    service = TargetTrackingService(db)
    
    # Ensure some users exist
    user = User(email="test@namaskah.com", subscription_tier="pro", email_verified=True)
    db.add(user)
    db.commit() # Sync commit
    
    snapshot = await service.record_daily_snapshot()
    assert snapshot is not None
    assert snapshot.total_users >= 1
    assert snapshot.pro_count >= 1
    assert snapshot.snapshot_date == date.today()
    
    # Verify duplicates are handled
    double_snapshot = await service.record_daily_snapshot()
    assert double_snapshot is None

@pytest.mark.asyncio
async def test_audit_log_persistence(db):
    """Verify that AuditService correctly writes to the database."""
    service = AuditService(db)
    
    action = "MANAGE_TIER"
    resource = "USER"
    log = await service.log_action(
        user_id="admin_123",
        action=action,
        resource_type=resource,
        resource_id="user_456",
        details={"old_tier": "free", "new_tier": "pro"}
    )
    
    assert log.id is not None
    assert log.action == action
    
    # Retrieve from DB (Sync execution)
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    history = db.execute(query).scalars().all()
    assert len(history) >= 1
    assert history[0].action == action
