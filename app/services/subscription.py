"""
구독 자동 갱신 서비스

구독 관리 및 자동 갱신 로직을 처리합니다:
- 자동 갱신 대상 조회
- 갱신 결제 처리 (토스페이먼츠 빌링키 사용)
- 갱신 실패 처리
- 만료 임박 알림
"""

import os
import base64
import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from loguru import logger

from app.models.subscription import Subscription, Payment
from app.models.user import User


# 토스페이먼츠 설정
TOSS_CLIENT_KEY = os.getenv("TOSS_PAYMENTS_CLIENT_KEY", os.getenv("TOSS_CLIENT_KEY", "test_ck_D5GePWvyJnrK0W0k6q8gLzN97Eoq"))
TOSS_SECRET_KEY = os.getenv("TOSS_PAYMENTS_SECRET_KEY", os.getenv("TOSS_SECRET_KEY", "test_sk_zXLkKEypNArWmo50nX3lmeaxYG5R"))
TOSS_BASE_URL = "https://api.tosspayments.com"

# 플랜별 금액 (원 단위)
PLAN_PRICES = {
    "basic": 29000,
    "pro": 99000,
    "business": 299000
}

# 플랜별 크레딧
PLAN_CREDITS = {
    "basic": 20,
    "pro": 100,
    "business": -1  # 무제한
}


def get_expiring_subscriptions(db: Session, days_before: int = 3) -> list[Subscription]:
    """
    만료 임박 구독 조회

    Args:
        db: 데이터베이스 세션
        days_before: 만료 며칠 전부터 알림할지 (기본: 3일)

    Returns:
        list[Subscription]: 만료 임박 구독 목록
    """
    cutoff_date = datetime.now() + timedelta(days=days_before)

    expiring_subscriptions = db.query(Subscription).filter(
        and_(
            Subscription.is_active == 1,
            Subscription.end_date <= cutoff_date,
            Subscription.end_date > datetime.now()
        )
    ).all()

    return expiring_subscriptions


def get_renewable_subscriptions(db: Session) -> list[Subscription]:
    """
    자동 갱신 대상 구독 조회

    조건:
    - is_active = 1 (활성화)
    - auto_renew = 1 (자동 갱신 활성화)
    - billing_key 존재 (빌링키 등록됨)
    - end_date <= 현재시각 + 1일 (만료 1일 이내)

    Returns:
        list[Subscription]: 자동 갱신 대상 구독 목록
    """
    cutoff_date = datetime.now() + timedelta(days=1)

    renewable_subscriptions = db.query(Subscription).filter(
        and_(
            Subscription.is_active == 1,
            Subscription.auto_renew == 1,
            Subscription.billing_key.isnot(None),
            Subscription.end_date <= cutoff_date
        )
    ).all()

    logger.info(f"🔄 Found {len(renewable_subscriptions)} subscriptions to renew")
    return renewable_subscriptions


def renew_subscription_with_billing_key(db: Session, subscription: Subscription) -> dict:
    """
    빌링키를 사용한 자동 결제 및 구독 갱신

    Args:
        db: 데이터베이스 세션
        subscription: 갱신할 구독

    Returns:
        dict: {
            "status": "success" | "error",
            "message": "메시지",
            "payment_key": "결제키" (성공 시)
        }
    """
    try:
        user = subscription.user
        plan = subscription.plan
        amount = PLAN_PRICES.get(plan, 0)

        if amount == 0:
            logger.error(f"❌ Invalid plan: {plan}")
            return {"status": "error", "message": f"Invalid plan: {plan}"}

        # 빌링키로 자동 결제 요청
        auth_header = base64.b64encode(f"{TOSS_SECRET_KEY}:".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json"
        }

        # 주문 ID 생성 (갱신 표시)
        timestamp = int(datetime.now().timestamp())
        order_id = f"owl_{user.id}_{timestamp}_{plan}_renew"

        # 토스페이먼츠 자동결제 API 호출
        url = f"{TOSS_BASE_URL}/v1/billing/{subscription.billing_key}"
        payload = {
            "customerKey": str(user.id),
            "amount": amount,
            "orderId": order_id,
            "orderName": f"올빼미 AI 영상 스튜디오 - {plan.capitalize()} Plan (자동갱신)",
            "customerEmail": user.email,
            "customerName": user.full_name or user.email.split("@")[0]
        }

        logger.info(f"🔄 Renewing subscription: User={user.email}, Plan={plan}, Amount={amount}")

        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        payment_data = response.json()

        # 결제 성공 시 구독 갱신
        if payment_data.get("status") == "DONE":
            # 구독 기간 연장
            new_end_date = subscription.end_date + timedelta(days=30)
            subscription.end_date = new_end_date
            subscription.last_renewed_at = datetime.now()
            subscription.next_billing_date = new_end_date

            # 크레딧 갱신
            credits = PLAN_CREDITS.get(plan, 0)
            if credits == -1:
                user.credits = -1  # 무제한
            else:
                user.credits = credits

            # 결제 기록 생성
            payment = Payment(
                user_id=user.id,
                subscription_id=subscription.id,
                amount=amount,
                currency="KRW",
                status="succeeded",
                payment_gateway_charge_id=order_id,
                payment_key=payment_data.get("paymentKey")
            )
            db.add(payment)
            db.commit()

            logger.info(f"✅ Subscription renewed successfully: {user.email} until {new_end_date}")

            return {
                "status": "success",
                "message": "Subscription renewed",
                "payment_key": payment_data.get("paymentKey"),
                "new_end_date": new_end_date.isoformat()
            }
        else:
            logger.warning(f"⚠️ Payment not completed: {payment_data.get('status')}")
            return {"status": "error", "message": f"Payment status: {payment_data.get('status')}"}

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Payment request failed: {e}")

        # 자동 갱신 실패 처리
        _handle_renewal_failure(db, subscription, str(e))

        return {"status": "error", "message": f"Payment failed: {e}"}

    except Exception as e:
        logger.error(f"❌ Renewal failed: {e}", exc_info=True)
        db.rollback()
        return {"status": "error", "message": str(e)}


def _handle_renewal_failure(db: Session, subscription: Subscription, error_message: str):
    """
    자동 갱신 실패 처리

    Args:
        db: 데이터베이스 세션
        subscription: 갱신 실패한 구독
        error_message: 오류 메시지
    """
    try:
        user = subscription.user

        # 실패 로그 기록
        logger.warning(f"⚠️ Renewal failed for {user.email}: {error_message}")

        # TODO: 사용자에게 이메일 알림 발송
        # send_renewal_failure_email(user.email, subscription.plan, error_message)

        # 자동 갱신 비활성화 (3회 연속 실패 시)
        # 현재는 1회 실패 시 비활성화 (추후 개선 필요)
        subscription.auto_renew = 0
        db.commit()

        logger.info(f"🔒 Auto-renew disabled for {user.email}")

    except Exception as e:
        logger.error(f"❌ Failed to handle renewal failure: {e}")
        db.rollback()


def process_all_renewals(db: Session) -> dict:
    """
    모든 자동 갱신 대상 구독 처리

    Returns:
        dict: {
            "total": 전체 대상 수,
            "success": 성공 수,
            "failed": 실패 수,
            "details": [처리 결과 목록]
        }
    """
    renewable_subscriptions = get_renewable_subscriptions(db)

    results = {
        "total": len(renewable_subscriptions),
        "success": 0,
        "failed": 0,
        "details": []
    }

    for subscription in renewable_subscriptions:
        result = renew_subscription_with_billing_key(db, subscription)

        if result["status"] == "success":
            results["success"] += 1
        else:
            results["failed"] += 1

        results["details"].append({
            "subscription_id": subscription.id,
            "user_email": subscription.user.email,
            "plan": subscription.plan,
            "result": result
        })

    logger.info(f"📊 Renewal summary: Total={results['total']}, Success={results['success']}, Failed={results['failed']}")

    return results


def toggle_auto_renew(db: Session, subscription_id: int, enable: bool) -> dict:
    """
    자동 갱신 설정 토글

    Args:
        db: 데이터베이스 세션
        subscription_id: 구독 ID
        enable: True (활성화) / False (비활성화)

    Returns:
        dict: {"status": "success" | "error", "message": "메시지"}
    """
    try:
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()

        if not subscription:
            return {"status": "error", "message": "Subscription not found"}

        subscription.auto_renew = 1 if enable else 0
        db.commit()

        action = "enabled" if enable else "disabled"
        logger.info(f"✅ Auto-renew {action} for subscription {subscription_id}")

        return {"status": "success", "message": f"Auto-renew {action}"}

    except Exception as e:
        logger.error(f"❌ Failed to toggle auto-renew: {e}")
        db.rollback()
        return {"status": "error", "message": str(e)}


def cancel_subscription(db: Session, subscription_id: int) -> dict:
    """
    구독 취소

    Args:
        db: 데이터베이스 세션
        subscription_id: 구독 ID

    Returns:
        dict: {"status": "success" | "error", "message": "메시지"}
    """
    try:
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()

        if not subscription:
            return {"status": "error", "message": "Subscription not found"}

        # 자동 갱신 비활성화
        subscription.auto_renew = 0
        subscription.is_active = 0

        # 사용자 플랜을 free로 변경
        user = subscription.user
        user.subscription_plan = "free"
        user.credits = 3  # 무료 플랜 크레딧

        db.commit()

        logger.info(f"✅ Subscription canceled: {subscription_id}")

        return {"status": "success", "message": "Subscription canceled"}

    except Exception as e:
        logger.error(f"❌ Failed to cancel subscription: {e}")
        db.rollback()
        return {"status": "error", "message": str(e)}
