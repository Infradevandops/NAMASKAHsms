"""Credit system endpoints for managing user credits and transactions."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.exceptions import InsufficientCreditsError
from app.core.logging import get_logger
from app.models.user import User
from app.services.credit_service import CreditService

logger = get_logger(__name__)
router = APIRouter(prefix="/user", tags=["Credits"])


class CreditBalanceResponse:
    """Response model for credit balance."""


class TransactionResponse:
    """Response model for transaction."""


class TransactionHistoryResponse:
    """Response model for transaction history."""


@router.get("/balance")
async def get_user_balance(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get current credit balance for user.

    Returns:
        - credits: Current credit balance
        - free_verifications: Free verifications remaining
        - currency: Currency code (USD)
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"Retrieved balance for user {user_id}: {user.credits}")

        return {
            "credits": float(user.credits or 0.0),
            "free_verifications": float(user.free_verifications or 0.0),
            "currency": "USD",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get balance for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve balance",
        )


@router.get("/credits/history")
async def get_credit_history(
    user_id: str = Depends(get_current_user_id),
    transaction_type: Optional[str] = Query(
        None,
        description="Filter by type: credit, debit, bonus, refund, transfer, admin_reset",
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db),
):
    """Get credit transaction history for user.

    Query Parameters:
        - transaction_type: Filter by transaction type
        - skip: Number of records to skip (pagination)
        - limit: Number of records to return (max 100)

    Returns:
        - total: Total number of transactions
        - skip: Number of records skipped
        - limit: Number of records returned
        - transactions: List of transactions with details
    """
    try:
        credit_service = CreditService(db)
        history = credit_service.get_transaction_history(
            user_id=user_id, transaction_type=transaction_type, skip=skip, limit=limit
        )

        logger.info(
            f"Retrieved credit history for user {user_id}: "
            f"{len(history['transactions'])} transactions"
        )

        return history

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get credit history for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve credit history",
        )


@router.get("/credits/summary")
async def get_credit_summary(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Get credit transaction summary for user.

    Returns:
        - current_balance: Current credit balance
        - total_credits_added: Total credits added
        - total_credits_deducted: Total credits deducted
        - total_bonuses: Total bonuses received
        - total_refunds: Total refunds received
        - transaction_count: Total number of transactions
    """
    try:
        credit_service = CreditService(db)
        summary = credit_service.get_transaction_summary(user_id)

        logger.info(f"Generated credit summary for user {user_id}")

        return summary

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get credit summary for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve credit summary",
        )


@router.post("/credits/add")
async def add_credits(
    amount: float = Query(..., gt=0, description="Amount to add"),
    description: str = Query(
        "Manual credit addition", description="Transaction description"
    ),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Add credits to user account (admin endpoint).

    Query Parameters:
        - amount: Amount to add (must be positive)
        - description: Transaction description

    Returns:
        - amount_added: Amount added
        - old_balance: Previous balance
        - new_balance: New balance
        - timestamp: Transaction timestamp
    """
    try:
        # Check if user is admin
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_admin:
            logger.warning(f"Non-admin user {user_id} attempted to add credits")
            raise HTTPException(status_code=403, detail="Admin access required")

        credit_service = CreditService(db)
        result = credit_service.add_credits(
            user_id=user_id,
            amount=amount,
            description=description,
            transaction_type="credit",
        )

        logger.info(f"Added {amount} credits for user {user_id}")

        return result

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add credits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add credits",
        )


@router.post("/credits/deduct")
async def deduct_credits(
    amount: float = Query(..., gt=0, description="Amount to deduct"),
    description: str = Query("Service charge", description="Transaction description"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Deduct credits from user account (admin endpoint).

    Query Parameters:
        - amount: Amount to deduct (must be positive)
        - description: Transaction description

    Returns:
        - amount_deducted: Amount deducted
        - old_balance: Previous balance
        - new_balance: New balance
        - timestamp: Transaction timestamp
    """
    try:
        # Check if user is admin
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_admin:
            logger.warning(f"Non-admin user {user_id} attempted to deduct credits")
            raise HTTPException(status_code=403, detail="Admin access required")

        credit_service = CreditService(db)
        result = credit_service.deduct_credits(
            user_id=user_id,
            amount=amount,
            description=description,
            transaction_type="debit",
        )

        logger.info(f"Deducted {amount} credits from user {user_id}")

        return result

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except InsufficientCreditsError as e:
        logger.warning(f"Insufficient credits: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to deduct credits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deduct credits",
        )


@router.post("/credits/transfer")
async def transfer_credits(
    to_user_id: str = Query(..., description="Destination user ID"),
    amount: float = Query(..., gt=0, description="Amount to transfer"),
    description: str = Query("Credit transfer", description="Transfer description"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Transfer credits from one user to another (admin endpoint).

    Query Parameters:
        - to_user_id: Destination user ID
        - amount: Amount to transfer (must be positive)
        - description: Transfer description

    Returns:
        - from_user_id: Source user ID
        - to_user_id: Destination user ID
        - amount: Amount transferred
        - from_user_new_balance: Source user new balance
        - to_user_new_balance: Destination user new balance
        - timestamp: Transfer timestamp
    """
    try:
        # Check if user is admin
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_admin:
            logger.warning(f"Non-admin user {user_id} attempted to transfer credits")
            raise HTTPException(status_code=403, detail="Admin access required")

        # Prevent self-transfer
        if user_id == to_user_id:
            raise ValueError("Cannot transfer credits to yourself")

        credit_service = CreditService(db)
        result = credit_service.transfer_credits(
            from_user_id=user_id,
            to_user_id=to_user_id,
            amount=amount,
            description=description,
        )

        logger.info(f"Transferred {amount} credits from {user_id} to {to_user_id}")

        return result

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except InsufficientCreditsError as e:
        logger.warning(f"Insufficient credits: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to transfer credits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transfer credits",
        )


@router.post("/credits/reset")
async def reset_credits(
    new_amount: float = Query(0.0, ge=0, description="New credit amount"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Reset user credits (admin only).

    Query Parameters:
        - new_amount: New credit amount (default 0)

    Returns:
        - user_id: User ID
        - old_balance: Previous balance
        - new_balance: New balance
        - timestamp: Reset timestamp
    """
    try:
        # Check if user is admin
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_admin:
            logger.warning(f"Non-admin user {user_id} attempted to reset credits")
            raise HTTPException(status_code=403, detail="Admin access required")

        credit_service = CreditService(db)
        result = credit_service.reset_credits(user_id=user_id, new_amount=new_amount)

        logger.warning(f"Reset credits for user {user_id} to {new_amount}")

        return result

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to reset credits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset credits",
        )
