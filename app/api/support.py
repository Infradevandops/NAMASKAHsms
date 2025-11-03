"""Support API router for customer support and help desk functionality."""
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user_id, get_admin_user_id
from app.models.user import User
from app.models.system import SupportTicket
from app.schemas import SuccessResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/support", tags=["Support"])


class SupportTicketCreate(BaseModel):
    category: str
    priority: str = "medium"
    subject: str
    message: str


class SupportTicketResponse(BaseModel):
    id: str
    category: str
    priority: str
    subject: str
    message: str
    status: str
    admin_response: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.post("/tickets", response_model=SuccessResponse)
async def create_support_ticket(
    ticket_data: SupportTicketCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new support ticket."""
    try:
        # Get user information
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create support ticket
        ticket = SupportTicket(
            user_id=user_id,
            email=user.email,
            name=user.email.split('@')[0],  # Use email prefix as name
            category=ticket_data.category,
            priority=ticket_data.priority,
            subject=ticket_data.subject,
            message=ticket_data.message,
            status="open"
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        # In a real implementation, you might send an email notification here
        logger.info(f"Support ticket created: {ticket.id} for user {user_id}")
        
        return SuccessResponse(
            message="Support ticket created successfully",
            data={
                "ticket_id": ticket.id,
                "status": ticket.status,
                "estimated_response_time": "24 hours"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to create support ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to create support ticket")


@router.get("/tickets", response_model=List[SupportTicketResponse])
async def get_user_tickets(
    user_id: str = Depends(get_current_user_id),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, le=100, description="Number of tickets to return"),
    db: Session = Depends(get_db)
):
    """Get user's support tickets."""
    try:
        query = db.query(SupportTicket).filter(SupportTicket.user_id == user_id)
        
        if status:
            query = query.filter(SupportTicket.status == status)
        
        tickets = query.order_by(SupportTicket.created_at.desc()).limit(limit).all()
        
        return [SupportTicketResponse.from_orm(ticket) for ticket in tickets]
        
    except Exception as e:
        logger.error(f"Failed to get user tickets: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tickets")


@router.get("/tickets/{ticket_id}", response_model=SupportTicketResponse)
async def get_ticket_details(
    ticket_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get specific ticket details."""
    try:
        ticket = db.query(SupportTicket).filter(
            SupportTicket.id == ticket_id,
            SupportTicket.user_id == user_id
        ).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        return SupportTicketResponse.from_orm(ticket)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ticket details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get ticket details")


@router.post("/tickets/{ticket_id}/close", response_model=SuccessResponse)
async def close_ticket(
    ticket_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Close a support ticket."""
    try:
        ticket = db.query(SupportTicket).filter(
            SupportTicket.id == ticket_id,
            SupportTicket.user_id == user_id
        ).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        if ticket.status == "closed":
            raise HTTPException(status_code=400, detail="Ticket is already closed")
        
        ticket.status = "closed"
        ticket.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        return SuccessResponse(
            message="Ticket closed successfully",
            data={"ticket_id": ticket_id, "status": "closed"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to close ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to close ticket")


@router.get("/faq")
async def get_faq():
    """Get frequently asked questions."""
    try:
        faq_items = [
            {
                "id": "1",
                "category": "General",
                "question": "How long does SMS verification take?",
                "answer": (
                    "Most SMS verifications complete within 30-60 seconds. "
                    "Voice verifications may take 1-2 minutes depending on the service and country."
                ),
                "helpful_count": 45
            },
            {
                "id": "2",
                "category": "Troubleshooting",
                "question": "What if I don't receive the verification code?",
                "answer": (
                    "If you don't receive the code within 2 minutes, you can: "
                    "1) Try voice verification instead of SMS, 2) Get a new number, "
                    "or 3) Cancel for a full refund. Our system automatically handles failed verifications."
                ),
                "helpful_count": 38
            },
            {
                "id": "3",
                "category": "Pricing",
                "question": "How much do verifications cost?",
                "answer": (
                    "Verification costs vary by service and country, typically ranging from $0.40 to $1.50. "
                    "Voice verifications cost an additional $0.30. You can see exact pricing when selecting a service."
                ),
                "helpful_count": 52
            },
            {
                "id": "4",
                "category": "Account",
                "question": "How do I add credits to my account?",
                "answer": (
                    "You can add credits through the Wallet section using Paystack payment gateway. "
                    "We accept major credit cards and bank transfers. "
                    "Credits are added instantly after successful payment."
                ),
                "helpful_count": 29
            },
            {
                "id": "5",
                "category": "Technical",
                "question": "Which services are supported?",
                "answer": (
                    "We support 1,800+ services including Telegram, WhatsApp, Google, Facebook, "
                    "Instagram, Discord, Twitter, and many more. Service availability may vary by country."
                ),
                "helpful_count": 41
            },
            {
                "id": "6",
                "category": "Refunds",
                "question": "What is your refund policy?",
                "answer": (
                    "We offer automatic refunds for failed verifications. "
                    "If you don't receive a code within the expected timeframe, "
                    "you can cancel the verification for a full refund. "
                    "Manual refunds are processed within 24 hours."
                ),
                "helpful_count": 33
            }
        ]
        
        return {"faq": faq_items}
        
    except Exception as e:
        logger.error(f"Failed to get FAQ: {e}")
        raise HTTPException(status_code=500, detail="Failed to get FAQ")


@router.post("/faq/{faq_id}/helpful", response_model=SuccessResponse)
async def mark_faq_helpful(
    faq_id: str,
    helpful: bool = Body(..., description="Whether the FAQ was helpful"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Mark FAQ item as helpful or not helpful."""
    try:
        # In a real implementation, you'd track this in the database
        return SuccessResponse(
            message="Feedback recorded",
            data={"faq_id": faq_id, "helpful": helpful}
        )
        
    except Exception as e:
        logger.error(f"Failed to record FAQ feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to record feedback")


@router.get("/categories")
async def get_support_categories():
    """Get available support categories."""
    try:
        categories = [
            {
                "id": "technical",
                "name": "Technical Issue",
                "description": "Problems with verifications, website, or app functionality",
                "icon": "🔧"
            },
            {
                "id": "billing",
                "name": "Billing Question",
                "description": "Payment issues, refunds, or account credits",
                "icon": "💳"
            },
            {
                "id": "verification",
                "name": "Verification Problem",
                "description": "Issues with specific SMS or voice verifications",
                "icon": "📱"
            },
            {
                "id": "account",
                "name": "Account Issue",
                "description": "Login problems, account settings, or security concerns",
                "icon": "👤"
            },
            {
                "id": "feature",
                "name": "Feature Request",
                "description": "Suggestions for new features or improvements",
                "icon": "💡"
            },
            {
                "id": "other",
                "name": "Other",
                "description": "General questions or other topics",
                "icon": "❓"
            }
        ]
        
        return {"categories": categories}
        
    except Exception as e:
        logger.error(f"Failed to get support categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to get categories")


@router.get("/status")
async def get_support_status():
    """Get current support system status."""
    try:
        return {
            "status": "operational",
            "average_response_time": "4 hours",
            "tickets_in_queue": 12,
            "support_hours": "24/7",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get support status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get support status")


# Admin endpoints for support management
@router.get("/admin/tickets", response_model=List[SupportTicketResponse])
async def get_all_tickets(
    admin_id: str = Depends(get_admin_user_id),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, le=200, description="Number of tickets to return"),
    db: Session = Depends(get_db)
):
    """Get all support tickets (admin only)."""
    try:
        query = db.query(SupportTicket)
        
        if status:
            query = query.filter(SupportTicket.status == status)
        if priority:
            query = query.filter(SupportTicket.priority == priority)
        if category:
            query = query.filter(SupportTicket.category == category)
        
        tickets = query.order_by(SupportTicket.created_at.desc()).limit(limit).all()
        
        return [SupportTicketResponse.from_orm(ticket) for ticket in tickets]
        
    except Exception as e:
        logger.error(f"Failed to get all tickets: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tickets")


@router.post("/admin/tickets/{ticket_id}/respond", response_model=SuccessResponse)
async def respond_to_ticket(
    ticket_id: str,
    response: str = Body(..., description="Admin response"),
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db)
):
    """Respond to a support ticket (admin only)."""
    try:
        ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket.admin_response = response
        ticket.status = "resolved"
        ticket.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        # In a real implementation, send email notification to user
        logger.info(f"Admin {admin_id} responded to ticket {ticket_id}")
        
        return SuccessResponse(
            message="Response sent successfully",
            data={"ticket_id": ticket_id, "status": "resolved"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to respond to ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to respond to ticket")


@router.get("/admin/stats")
async def get_support_stats(
    admin_id: str = Depends(get_admin_user_id),
    db: Session = Depends(get_db)
):
    """Get support statistics (admin only)."""
    try:
        total_tickets = db.query(SupportTicket).count()
        open_tickets = db.query(SupportTicket).filter(SupportTicket.status == "open").count()
        resolved_tickets = db.query(SupportTicket).filter(SupportTicket.status == "resolved").count()
        
        # Calculate average response time (mock for now)
        avg_response_time = "4.2 hours"
        
        return {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "resolved_tickets": resolved_tickets,
            "closed_tickets": total_tickets - open_tickets - resolved_tickets,
            "avg_response_time": avg_response_time,
            "resolution_rate": (
                round((resolved_tickets / total_tickets * 100), 1) 
                if total_tickets > 0 else 0
            )
        }
        
    except Exception as e:
        logger.error(f"Failed to get support stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get support stats")