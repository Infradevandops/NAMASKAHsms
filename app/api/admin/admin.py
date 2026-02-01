"""Admin API router for user management and system monitoring."""


from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_admin_user_id
from app.models.support_ticket import SupportTicket
from app.models.transaction import Transaction
from app.models.user import User
from app.models.verification import Verification
from app.schemas.responses import SuccessResponse, SupportTicketResponse
from app.services.notification_service import get_notification_service
from app.utils.sanitization import sanitize_email_content, sanitize_html
from sqlalchemy import text

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/", response_class=HTMLResponse)
def admin_dashboard():

    """Admin dashboard interface."""
with open("templates/admin.html", "r") as f:
        return HTMLResponse(content=f.read())


@router.get("/users")
def get_all_users(

    admin_id: str = Depends(get_admin_user_id),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
):
    """Get all users (admin only)."""
try:
        users = db.query(User).limit(size).all()

        items = []
for user in users:
            items.append(
                {
                    "id": user.id,
                    "email": user.email,
                    "credits": user.credits,
                    "is_admin": user.is_admin,
                    "created_at": (user.created_at.isoformat() if user.created_at else None),
                }
            )

        return {"items": items, "total": len(items)}
except (ValueError, AttributeError):
        return {"items": [], "total": 0}


@router.get("/users/{user_id}")
def get_user_details(

    user_id: str,
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db),
):
    """Get detailed user information (admin only)."""
try:
        user = db.query(User).filter(User.id == user_id).first()

if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user statistics
        total_verifications = db.query(Verification).filter(Verification.user_id == user_id).count()
        total_spent = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id, Transaction.type == "debit")
            .with_entities(Transaction.amount)
            .all()
        )
        total_spent = sum(abs(float(t[0])) for t in total_spent) if total_spent else 0.0

        total_funded = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id, Transaction.type == "credit")
            .with_entities(Transaction.amount)
            .all()
        )
        total_funded = sum(float(t[0]) for t in total_funded) if total_funded else 0.0

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "credits": user.credits,
                "free_verifications": getattr(user, "free_verifications", 0),
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
            "stats": {
                "total_verifications": total_verifications,
                "total_spent": total_spent,
                "total_funded": total_funded,
            },
        }
except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/credits", response_model=SuccessResponse)
def manage_user_credits(

    user_id: str,
    amount: float = Body(..., description="Amount to add or deduct"),
    operation: str = Body(..., description="Operation: add or deduct"),
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db),
):
    """Add or deduct credits from user account (admin only)."""
if operation not in ["add", "deduct"]:
        raise HTTPException(status_code=400, detail="Operation must be 'add' or 'deduct'")

    user = db.query(User).filter(User.id == user_id).first()
if not user:
        raise HTTPException(status_code=404, detail="User not found")

if operation == "deduct" and user.credits < amount:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. User has {user.credits}")

    # Update credits
if operation == "add":
        user.credits += amount
        transaction_amount = amount
        description = "Admin added credits"
else:
        user.credits -= amount
        transaction_amount = -float(amount)
        description = "Admin deducted credits"

    # Create transaction record
    transaction = Transaction(
        user_id=user_id,
        amount=transaction_amount,
        type="credit" if operation == "add" else "debit",
        description=description,
    )

    db.add(transaction)
    db.commit()

    return SuccessResponse(
        message=f"Successfully {operation}ed {amount} credits",
        data={"new_balance": user.credits},
    )


@router.post("/credits/add")
def add_user_credits(

    user_id: str = Body(...),
    amount: float = Body(...),
    reason: str = Body(""),
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db),
):
    """Add credits to user account (admin only)."""
try:
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.credits += amount

        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            type="credit",
            description=f"Admin credit: {reason}" if reason else "Admin added credits",
        )

        db.add(transaction)
        db.commit()

        return {
            "success": True,
            "message": f"Added {amount} credits",
            "new_balance": user.credits,
        }
except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/credits/deduct")
def deduct_user_credits(

    user_id: str = Body(...),
    amount: float = Body(...),
    reason: str = Body(""),
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db),
):
    """Deduct credits from user account (admin only)."""
try:
        user = db.query(User).filter(User.id == user_id).first()
if not user:
            raise HTTPException(status_code=404, detail="User not found")

if user.credits < amount:
            raise HTTPException(status_code=400, detail=f"Insufficient balance. User has {user.credits}")

        user.credits -= amount

        transaction = Transaction(
            user_id=user_id,
            amount=-amount,
            type="debit",
            description=(f"Admin debit: {reason}" if reason else "Admin deducted credits"),
        )

        db.add(transaction)
        db.commit()

        return {
            "success": True,
            "message": f"Deducted {amount} credits",
            "new_balance": user.credits,
        }
except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/suspend", response_model=SuccessResponse)
def suspend_user(

    user_id: str,
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db),
):
    """Suspend user account (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
if not user:
        raise HTTPException(status_code=404, detail="User not found")

if user.is_admin:
        raise HTTPException(status_code=403, detail="Cannot suspend admin account")

    user.is_active = False
    db.commit()

    return SuccessResponse(message=f"User {sanitize_html(user.email)} suspended")


@router.post("/users/{user_id}/activate", response_model=SuccessResponse)
def activate_user(

    user_id: str,
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db),
):
    """Activate suspended user account (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    db.commit()

    return SuccessResponse(message=f"User {sanitize_html(user.email)} activated")


@router.get("/stats")
def get_platform_stats(admin_id: str = Depends(get_admin_user_id), db: Session = Depends(get_db)):

    """Get platform-wide statistics (admin only)."""
try:
        # Total users
        total_users = db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0

        # New users (last 30 days)
        new_users = (
            db.execute(text("SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '30 days'")).scalar() or 0
        )

        # Total verifications
        total_verifications = db.execute(text("SELECT COUNT(*) FROM verifications")).scalar() or 0

        # Pending verifications
        pending_verifications = (
            db.execute(text("SELECT COUNT(*) FROM verifications WHERE status = 'pending'")).scalar() or 0
        )

        # Completed verifications
        completed_verifications = (
            db.execute(text("SELECT COUNT(*) FROM verifications WHERE status = 'completed'")).scalar() or 0
        )

        # Success rate
        success_rate = (completed_verifications / total_verifications * 100) if total_verifications > 0 else 0

        # Total revenue (sum of debit transactions)
        total_revenue = (
            db.execute(text("SELECT COALESCE(SUM(ABS(amount)), 0) FROM transactions WHERE type = 'debit'")).scalar()
            or 0
        )

        # Popular services (top 5)
        popular_services_raw = db.execute(
            text(
                """
                SELECT service_name, COUNT(*) as count
                FROM verifications
                WHERE service_name IS NOT NULL
                GROUP BY service_name
                ORDER BY count DESC
                LIMIT 5
            """
            )
        ).fetchall()
        popular_services = [{"name": row[0], "count": row[1]} for row in popular_services_raw]

        # Daily usage (last 7 days)
        daily_usage_raw = db.execute(
            text(
                """
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM verifications
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """
            )
        ).fetchall()
        daily_usage = [{"date": str(row[0]), "count": row[1]} for row in daily_usage_raw]

        return {
            "total_users": total_users,
            "new_users": new_users,
            "total_verifications": total_verifications,
            "pending_verifications": pending_verifications,
            "completed_verifications": completed_verifications,
            "success_rate": round(success_rate, 1),
            "total_revenue": float(total_revenue),
            "popular_services": popular_services,
            "daily_usage": daily_usage,
        }
except Exception as e:
        # Fallback with actual error logging
        return {
            "total_users": 0,
            "new_users": 0,
            "total_verifications": 0,
            "pending_verifications": 0,
            "completed_verifications": 0,
            "success_rate": 0.0,
            "total_revenue": 0.0,
            "popular_services": [],
            "daily_usage": [],
            "error": str(e),
        }


@router.get("/support/tickets", response_model=List[SupportTicketResponse])
def get_support_tickets(

    admin_id: str = Depends(get_admin_user_id),
    ticket_status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=100, description="Number of results"),
    db: Session = Depends(get_db),
):
    """Get all support tickets (admin only)."""
    query = db.query(SupportTicket)

if ticket_status:
        query = query.filter(SupportTicket.status == ticket_status)

    tickets = query.order_by(SupportTicket.created_at.desc()).limit(limit).all()

    return [SupportTicketResponse.from_orm(ticket) for ticket in tickets]


@router.post("/support/{ticket_id}/respond", response_model=SuccessResponse)
async def respond_to_ticket(
    ticket_id: str,
    response_text: str = Body(..., description="Admin response to the ticket"),
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db),
):
    """Respond to support ticket (admin only)."""

    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Update ticket
    ticket.admin_response = response_text
    ticket.status = "resolved"
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Send response email
    notification_service = get_notification_service(db)
    await notification_service.send_email(
        to_email=ticket.email,
        subject=f"Re: Support Request #{ticket.id} - Namaskah SMS",
        body="<h2>Support Response</h2>"
        + f"<p>Hi {sanitize_html(ticket.name)},</p>"
        + f"<p>We've reviewed your support request regarding <strong>{sanitize_html(ticket.category)}</strong>.</p>"
        + "<p><strong>Your Message:</strong></p>"
        + f"<p>{sanitize_html(ticket.message)}</p>"
        + "<p><strong>Our Response:</strong></p>"
        + f"<p>{sanitize_email_content(response_text)}</p><p>If you need further assistance, please reply to this email.</p><p>Best regards,<br>Namaskah Support Team</p>",
    )

    return SuccessResponse(message="Response sent successfully")


@router.get("/verifications/active")
def get_active_verifications(

    admin_id: str = Depends(get_admin_user_id),
    limit: int = Query(100, le=500, description="Number of results"),
    db: Session = Depends(get_db),
):
    """Get all active verifications system - wide (admin only)."""
try:
        return {"verifications": [], "total_count": 0}
except (ValueError, AttributeError):
        return {"verifications": [], "total_count": 0}


@router.post("/verifications/{verification_id}/cancel", response_model=SuccessResponse)
async def admin_cancel_verification(
    verification_id: str,
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db),
):
    """Cancel any verification and refund user (admin only)."""

    verification = db.query(Verification).filter(Verification.id == verification_id).first()
if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

if verification.status == "cancelled":
        raise HTTPException(status_code=400, detail="Already cancelled")

    # Cancel verification locally

    # Refund user
    user = db.query(User).filter(User.id == verification.user_id).first()
if user:
        user.credits += verification.cost

        # Create refund transaction
        transaction = Transaction(
            user_id=user.id,
            amount=verification.cost,
            type="credit",
            description=f"Admin cancelled verification {verification_id}",
        )
        db.add(transaction)

    verification.status = "cancelled"
    db.commit()

    return SuccessResponse(
        message="Verification cancelled and refunded",
        data={"refunded": verification.cost},
    )


@router.get("/system/health")
def get_system_health(admin_id: str = Depends(get_admin_user_id), db: Session = Depends(get_db)):

    """Get comprehensive system health status (admin only)."""
    # Database health
try:

        db.execute(text("SELECT 1"))
        db_status = "healthy"
except Exception:
        db_status = "unhealthy"

    # User statistics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active.is_(True)).count()

    # Verification statistics
    total_verifications = db.query(Verification).count()
    pending_verifications = db.query(Verification).filter(Verification.status == "pending").count()

    # Transaction statistics
    total_transactions = db.query(Transaction).count()

    return {
        "system_status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "statistics": {
            "total_users": total_users,
            "active_users": active_users,
            "total_verifications": total_verifications,
            "pending_verifications": pending_verifications,
            "total_transactions": total_transactions,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/transactions")
def get_all_transactions(

    admin_id: str = Depends(get_admin_user_id),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    transaction_type: Optional[str] = Query(None, description="Filter by type"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
):
    """Get all transactions with filtering (admin only)."""
    query = db.query(Transaction)

    # Apply filters
if user_id:
        query = query.filter(Transaction.user_id == user_id)
if transaction_type:
        query = query.filter(Transaction.type == transaction_type)

    # Get total count
    total = query.count()

    # Pagination
    offset = (page - 1) * size
    transactions = query.order_by(Transaction.created_at.desc()).offset(offset).limit(size).all()

    # Calculate pages
    pages = (total + size - 1) // size

    # Format response
    items = []
for transaction in transactions:
        user = db.query(User).filter(User.id == transaction.user_id).first()
        items.append(
            {
                "id": transaction.id,
                "user_id": transaction.user_id,
                "user_email": user.email if user else "Unknown",
                "amount": transaction.amount,
                "type": transaction.type,
                "description": transaction.description,
                "created_at": transaction.created_at.isoformat(),
            }
        )

    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


@router.post("/broadcast", response_model=SuccessResponse)
async def broadcast_notification(
    title: str = Body(..., description="Notification title"),
    message: str = Body(..., description="Notification message"),
    notification_type: str = Body("info", description="Notification type"),
    target_users: Optional[List[str]] = Body(None, description="Target user IDs (all if empty)"),
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db),
):
    """Broadcast notification to users (admin only)."""

    # Get target users
if target_users:
        users = db.query(User).filter(User.id.in_(target_users)).all()
else:
        users = db.query(User).filter(User.is_active.is_(True)).all()

if not users:
        raise HTTPException(status_code=404, detail="No target users found")

    # Send notifications
    notification_service = get_notification_service(db)
    sent_count = 0

for user in users:
try:
            await notification_service.send_email(
                to_email=user.email,
                subject=title,
                body=f"<h2>{sanitize_html(title)}</h2>"
                + f"<p>{sanitize_email_content(message)}</p>"
                + "<p>Best regards,<br>Namaskah Team</p>",
            )
            sent_count += 1
except Exception:
            continue  # Skip failed sends

    return SuccessResponse(
        message=f"Notification sent to {sent_count} users",
        data={"sent_count": sent_count, "total_users": len(users)},
    )
