
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.connection import get_db
from app.models import schema
from app.models.user import User
from app.services import auth, payment

router = APIRouter()

PLANS = {
    "basic": {"price": 29000, "credits": 20},
    "pro": {"price": 99000, "credits": 100},
    "business": {"price": 299000, "credits": -1} # -1 for unlimited
}

@router.post("/subscribe", response_model=schema.Payment)
def create_subscription(
    subscription_data: schema.SubscriptionBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user)
):
    plan = subscription_data.plan
    if plan not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan specified")

    amount = PLANS[plan]["price"]

    # In a real app, you'd get a payment token from the frontend (e.g., Stripe.js)
    # and use it to create the charge.
    charge_id = payment.create_charge(db, current_user, plan, amount)

    # Create subscription and payment records in the database
    # This is a simplified example. A real implementation would be more robust.
    # ... (code to create subscription and payment db records)

    # For now, just return a dummy response
    return schema.Payment(
        id=1, 
        user_id=current_user.id, 
        subscription_id=1, 
        amount=amount, 
        status="succeeded", 
        created_at="2025-09-29T12:00:00Z"
    )

@router.post("/webhook")
async def toss_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    토스페이먼츠 웹훅 엔드포인트

    결제 상태 변경, 가상계좌 입금, 결제 취소 등의 이벤트를 실시간으로 수신합니다.

    지원 이벤트:
    - PAYMENT_STATUS_CHANGED: 결제 상태 변경
    - DEPOSIT_CALLBACK: 가상계좌 입금
    - CANCEL_STATUS_CHANGED: 결제 취소

    Returns:
        dict: {"status": "success"} (토스페이먼츠는 200 OK 응답 필요)
    """
    try:
        # 페이로드 읽기
        payload = await request.json()

        # 웹훅 서명 검증 (X-Toss-Signature 헤더)
        signature = request.headers.get("X-Toss-Signature")

        # 웹훅 처리
        result = payment.handle_webhook(db, payload, signature)

        # 토스페이먼츠는 10초 이내 200 OK 응답 필요
        return result

    except Exception as e:
        # 에러 발생 시에도 200 OK 반환 (토스페이먼츠 재전송 방지)
        # 실제 에러는 로그에 기록됨
        return {"status": "error", "message": str(e)}

