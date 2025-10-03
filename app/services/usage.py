
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from app.models.user import User
from app.models.credit_history import CreditHistory


def check_credits(db: Session, user: User, required_credits: int = 1) -> bool:
    """Check if the user has enough credits."""
    # Unlimited credits for business plan or superuser
    if user.subscription_plan == "business" or user.is_superuser:
        return True

    if user.credits < required_credits:
        raise HTTPException(
            status_code=402, # Payment Required
            detail=f"Not enough credits. You have {user.credits}, but need {required_credits}. Please upgrade your plan."
        )
    return True


def use_credits(
    db: Session,
    user: User,
    required_credits: int = 1,
    action_type: str = "video_generation",
    description: str = None,
    related_id: str = None
):
    """
    Decrement user's credits after an action and record history.

    Args:
        db: Database session
        user: User object
        required_credits: Number of credits to use
        action_type: Type of action (video_generation, etc.)
        description: Optional description
        related_id: Optional related ID (task_id, etc.)
    """
    # Don't decrement for unlimited plans
    if user.subscription_plan == "business" or user.is_superuser:
        return

    if user.credits < required_credits:
        # This should be caught by check_credits first, but as a safeguard:
        raise HTTPException(status_code=402, detail="Not enough credits.")

    # 크레딧 차감
    user.credits -= required_credits

    # 히스토리 기록
    history = CreditHistory(
        user_id=user.id,
        amount=-required_credits,  # 음수: 사용
        balance_after=user.credits,
        action_type=action_type,
        description=description or f"{action_type} used {required_credits} credits",
        related_id=related_id,
        created_at=datetime.utcnow()
    )
    db.add(history)
    db.commit()
    db.refresh(user)


def add_credits(
    db: Session,
    user: User,
    credits: int,
    action_type: str = "admin_grant",
    description: str = None,
    related_id: str = None
):
    """
    Add credits to user account and record history.

    Args:
        db: Database session
        user: User object
        credits: Number of credits to add
        action_type: Type of action (subscription_purchase, admin_grant, refund)
        description: Optional description
        related_id: Optional related ID (subscription_id, payment_id, etc.)
    """
    user.credits += credits

    # 히스토리 기록
    history = CreditHistory(
        user_id=user.id,
        amount=credits,  # 양수: 충전
        balance_after=user.credits,
        action_type=action_type,
        description=description or f"{action_type} added {credits} credits",
        related_id=related_id,
        created_at=datetime.utcnow()
    )
    db.add(history)
    db.commit()
    db.refresh(user)


def get_credit_history(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 10
):
    """
    Get credit history for a user.

    Args:
        db: Database session
        user_id: User ID
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of CreditHistory objects
    """
    return (
        db.query(CreditHistory)
        .filter(CreditHistory.user_id == user_id)
        .order_by(CreditHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

