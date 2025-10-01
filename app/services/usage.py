
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User

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

def use_credits(db: Session, user: User, required_credits: int = 1):
    """Decrement user's credits after an action."""
    # Don't decrement for unlimited plans
    if user.subscription_plan == "business" or user.is_superuser:
        return

    if user.credits < required_credits:
        # This should be caught by check_credits first, but as a safeguard:
        raise HTTPException(status_code=402, detail="Not enough credits.")

    user.credits -= required_credits
    db.commit()
    db.refresh(user)

