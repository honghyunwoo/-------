
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.connection import get_db
from app.models import schema
from app.models.user import User
from app.services import auth, payment, subscription as subscription_service

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
        payload_body = await request.body()
        payload = await request.json()

        # 웹훅 서명 검증 (X-Toss-Signature 헤더)
        signature = request.headers.get("X-Toss-Signature")

        # 서명 검증 실패 시 403 Forbidden 반환 (보안)
        if not payment.verify_webhook_signature(payload_body.decode('utf-8'), signature):
            raise HTTPException(status_code=403, detail="Invalid webhook signature")

        # 웹훅 처리
        result = payment.handle_webhook(db, payload, signature)

        # 토스페이먼츠는 10초 이내 200 OK 응답 필요
        return result

    except HTTPException:
        # HTTPException은 그대로 전달 (403 포함)
        raise
    except Exception as e:
        # 기타 에러 발생 시에도 200 OK 반환 (토스페이먼츠 재전송 방지)
        # 실제 에러는 로그에 기록됨
        return {"status": "error", "message": str(e)}


@router.post("/subscription/auto-renew/toggle")
def toggle_auto_renew(
    subscription_id: int,
    enable: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user)
):
    """
    자동 갱신 설정 토글

    Args:
        subscription_id: 구독 ID
        enable: True (활성화) / False (비활성화)

    Returns:
        dict: {"status": "success" | "error", "message": "메시지"}
    """
    # 본인 구독인지 확인
    from app.models.subscription import Subscription
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if subscription.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = subscription_service.toggle_auto_renew(db, subscription_id, enable)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/subscription/cancel")
def cancel_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user)
):
    """
    구독 취소

    Args:
        subscription_id: 구독 ID

    Returns:
        dict: {"status": "success" | "error", "message": "메시지"}
    """
    # 본인 구독인지 확인
    from app.models.subscription import Subscription
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if subscription.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = subscription_service.cancel_subscription(db, subscription_id)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/subscription/status")
def get_subscription_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_user)
):
    """
    현재 사용자의 구독 상태 조회

    Returns:
        dict: 구독 정보
    """
    from app.models.subscription import Subscription

    active_subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.is_active == 1
    ).first()

    if not active_subscription:
        return {
            "has_subscription": False,
            "plan": current_user.subscription_plan,
            "credits": current_user.credits
        }

    return {
        "has_subscription": True,
        "subscription_id": active_subscription.id,
        "plan": active_subscription.plan,
        "start_date": active_subscription.start_date.isoformat(),
        "end_date": active_subscription.end_date.isoformat(),
        "auto_renew": bool(active_subscription.auto_renew),
        "next_billing_date": active_subscription.next_billing_date.isoformat() if active_subscription.next_billing_date else None,
        "credits": current_user.credits,
        "days_left": (active_subscription.end_date - datetime.now()).days
    }

