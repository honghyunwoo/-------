"""
크레딧 관리 API: 크레딧 히스토리 조회, 관리자 크레딧 부여
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.models.user import User
from app.models.credit_history import CreditHistory
from app.services import auth as auth_service
from app.services import usage
from app.middleware.security import limiter

router = APIRouter()


class CreditHistoryResponse(BaseModel):
    """크레딧 히스토리 응답"""
    id: int
    amount: int
    balance_after: int
    action_type: str
    description: str
    related_id: str = None
    created_at: str

    class Config:
        from_attributes = True


class AddCreditsRequest(BaseModel):
    """관리자 크레딧 부여 요청"""
    user_id: int
    credits: int
    description: str = None


@router.get("/history", response_model=List[CreditHistoryResponse])
@limiter.limit("30/minute")  # 분당 30회 조회 제한
def get_credit_history(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    현재 사용자의 크레딧 사용 내역 조회
    """
    history = usage.get_credit_history(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )

    return [
        CreditHistoryResponse(
            id=h.id,
            amount=h.amount,
            balance_after=h.balance_after,
            action_type=h.action_type,
            description=h.description,
            related_id=h.related_id,
            created_at=h.created_at.isoformat(),
        )
        for h in history
    ]


@router.post("/admin/add", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")  # 분당 10회 제한
def admin_add_credits(
    request: Request,
    data: AddCreditsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    관리자 전용: 사용자에게 크레딧 부여
    """
    # 관리자 권한 확인
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can add credits to users.",
        )

    # 대상 사용자 조회
    target_user = db.query(User).filter(User.id == data.user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    # 크레딧 부여
    usage.add_credits(
        db=db,
        user=target_user,
        credits=data.credits,
        action_type="admin_grant",
        description=data.description or f"Admin granted {data.credits} credits",
        related_id=f"admin:{current_user.id}",
    )

    return {
        "message": f"Successfully added {data.credits} credits to user {target_user.email}",
        "new_balance": target_user.credits,
    }


@router.get("/balance")
@limiter.limit("60/minute")  # 분당 60회 조회 제한
def get_credit_balance(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    현재 사용자의 크레딧 잔액 조회
    """
    # 무제한 플랜 확인
    is_unlimited = (
        current_user.subscription_plan == "business" or current_user.is_superuser
    )

    return {
        "credits": current_user.credits,
        "subscription_plan": current_user.subscription_plan,
        "is_unlimited": is_unlimited,
    }
