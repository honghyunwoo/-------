
import base64
import json
import os
import requests
import hmac
import hashlib
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from loguru import logger
from fastapi import HTTPException

from app.models.subscription import Payment, Subscription
from app.models.user import User

# 토스페이먼츠 설정
TOSS_CLIENT_KEY = os.getenv("TOSS_CLIENT_KEY", "test_ck_D5GePWvyJnrK0W0k6q8gLzN97Eoq")
TOSS_SECRET_KEY = os.getenv("TOSS_SECRET_KEY", "test_sk_zXLkKEypNArWmo50nX3lmeaxYG5R")
TOSS_BASE_URL = "https://api.tosspayments.com" 

def confirm_payment(db: Session, user: User, payment_key: str, order_id: str, amount: int):
    """
    Confirms a payment with the Toss Payments API.
    """
    auth_header = base64.b64encode(f"{TOSS_SECRET_KEY}:".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/json"
    }
    
    url = f"{TOSS_BASE_URL}/v1/payments/{payment_key}"
    payload = {
        "orderId": order_id,
        "amount": amount
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        payment_data = response.json()

        if payment_data.get("status") == "DONE":
            # Payment successful, update subscription
            plan = payment_data.get("orderName").split(" - ")[1].lower().replace(" plan", "")
            _update_user_subscription(db, user, plan, amount, order_id)
            return payment_data
        else:
            # Payment failed or is in an unexpected state
            raise HTTPException(status_code=400, detail=f"Payment not completed: {payment_data.get('status')}")

    except requests.exceptions.RequestException as e:
        # Handle API request errors
        raise HTTPException(status_code=500, detail=f"Toss Payments API error: {e}")

def _update_user_subscription(db: Session, user: User, plan: str, amount: int, order_id: str):
    """
    Updates user's subscription plan and credits, and logs the payment.
    """
    # Update user credits and plan
    if plan == "business":
        user.credits = -1  # 무제한
    elif plan == "pro":
        user.credits = 100
    elif plan == "basic":
        user.credits = 20
    user.subscription_plan = plan

    # Deactivate previous active subscriptions
    db.query(Subscription).filter(Subscription.user_id == user.id, Subscription.is_active == 1).update({"is_active": 0})

    # Create new subscription record
    end_date = datetime.now() + timedelta(days=30)
    subscription = Subscription(
        user_id=user.id,
        plan=plan,
        end_date=end_date,
        is_active=1,
    )
    db.add(subscription)
    db.flush() # To get the subscription ID for the payment record

    # Create new payment record
    payment = Payment(
        user_id=user.id,
        subscription_id=subscription.id,
        amount=amount,
        currency="KRW",
        status="succeeded",
        payment_gateway_charge_id=order_id
    )
    db.add(payment)

    db.commit()

def verify_webhook_signature(payload: str, signature: str) -> bool:
    """
    토스페이먼츠 웹훅 서명을 검증합니다.
    HMAC SHA256을 사용하여 페이로드 무결성을 확인합니다.

    Args:
        payload: 웹훅 페이로드 (JSON 문자열)
        signature: 토스페이먼츠가 전송한 서명 (헤더의 X-Toss-Signature)

    Returns:
        bool: 서명이 유효하면 True
    """
    try:
        # HMAC SHA256으로 서명 생성
        computed_signature = hmac.new(
            TOSS_SECRET_KEY.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        # 타이밍 공격 방지를 위한 constant-time 비교
        return hmac.compare_digest(computed_signature, signature)
    except Exception as e:
        logger.error(f"🛡️ Webhook signature verification failed: {e}")
        return False


def handle_webhook(db: Session, payload: dict, signature: str = None) -> dict:
    """
    토스페이먼츠 웹훅을 처리합니다.

    지원하는 이벤트:
    - PAYMENT_STATUS_CHANGED: 결제 상태 변경 (카드, 간편결제, 계좌이체 등)
    - DEPOSIT_CALLBACK: 가상계좌 입금 확인
    - CANCEL_STATUS_CHANGED: 결제 취소 상태 변경

    Args:
        db: 데이터베이스 세션
        payload: 웹훅 페이로드
        signature: 웹훅 서명 (보안 검증용)

    Returns:
        dict: 처리 결과 {"status": "success"} 또는 에러 정보
    """
    try:
        # 1. 서명 검증 (프로덕션 환경에서 필수)
        if signature and not verify_webhook_signature(json.dumps(payload), signature):
            logger.warning("🚨 Webhook signature verification failed - potential security threat")
            return {"status": "error", "message": "Invalid signature"}

        # 2. 이벤트 타입 확인
        event_type = payload.get("eventType")
        logger.info(f"📬 Webhook received: {event_type}")

        # 3. 이벤트별 처리
        if event_type == "PAYMENT_STATUS_CHANGED":
            return _handle_payment_status_changed(db, payload)

        elif event_type == "DEPOSIT_CALLBACK":
            return _handle_deposit_callback(db, payload)

        elif event_type == "CANCEL_STATUS_CHANGED":
            return _handle_cancel_status_changed(db, payload)

        else:
            logger.warning(f"⚠️ Unknown webhook event type: {event_type}")
            return {"status": "ignored", "message": f"Event type {event_type} not handled"}

    except Exception as e:
        logger.error(f"❌ Webhook processing error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


def _handle_payment_status_changed(db: Session, payload: dict) -> dict:
    """
    PAYMENT_STATUS_CHANGED 이벤트 처리
    카드, 간편결제, 계좌이체 등의 결제 상태 변경을 처리합니다.

    결제 상태:
    - READY: 결제 대기 중
    - IN_PROGRESS: 결제 진행 중
    - WAITING_FOR_DEPOSIT: 가상계좌 입금 대기
    - DONE: 결제 완료 ✅
    - CANCELED: 결제 취소
    - PARTIAL_CANCELED: 부분 취소
    - ABORTED: 결제 승인 실패
    - EXPIRED: 결제 만료
    """
    try:
        data = payload.get("data", {})
        payment_key = data.get("paymentKey")
        order_id = data.get("orderId")
        status = data.get("status")
        amount = data.get("totalAmount")

        logger.info(f"💳 Payment status changed - Order: {order_id}, Status: {status}, Amount: {amount}")

        # 멱등성 보장: 이미 처리된 결제인지 확인
        existing_payment = db.query(Payment).filter(
            Payment.payment_gateway_charge_id == order_id
        ).first()

        if status == "DONE":
            # 결제 완료 처리
            if existing_payment and existing_payment.status == "succeeded":
                logger.info(f"✅ Payment already processed: {order_id}")
                return {"status": "success", "message": "Already processed"}

            # 주문 ID에서 사용자 정보 추출 (형식: owl_[user_id]_[timestamp]_[plan])
            try:
                parts = order_id.split("_")
                user_id = int(parts[1])
                plan = parts[3]
            except (IndexError, ValueError):
                logger.error(f"❌ Invalid order_id format: {order_id}")
                return {"status": "error", "message": "Invalid order_id"}

            # 사용자 조회
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"❌ User not found: {user_id}")
                return {"status": "error", "message": "User not found"}

            # 구독 업데이트
            _update_user_subscription(db, user, plan, amount, order_id)
            logger.info(f"✅ Subscription activated - User: {user.email}, Plan: {plan}")

            return {"status": "success", "message": "Payment processed"}

        elif status == "CANCELED":
            # 결제 취소 처리
            if existing_payment:
                existing_payment.status = "canceled"
                db.commit()
                logger.info(f"🔄 Payment canceled: {order_id}")

            return {"status": "success", "message": "Payment canceled"}

        elif status == "ABORTED":
            # 결제 승인 실패
            logger.warning(f"⚠️ Payment aborted: {order_id}")
            return {"status": "success", "message": "Payment aborted"}

        elif status == "EXPIRED":
            # 결제 만료
            logger.warning(f"⏰ Payment expired: {order_id}")
            return {"status": "success", "message": "Payment expired"}

        else:
            # 기타 상태 (READY, IN_PROGRESS 등)
            logger.info(f"ℹ️ Payment status: {status} for {order_id}")
            return {"status": "success", "message": f"Status {status} noted"}

    except Exception as e:
        logger.error(f"❌ Error handling payment status change: {e}", exc_info=True)
        db.rollback()
        raise


def _handle_deposit_callback(db: Session, payload: dict) -> dict:
    """
    DEPOSIT_CALLBACK 이벤트 처리
    가상계좌 입금 확인을 처리합니다.

    가상계좌는 결제 완료 시점을 구매자가 결정하므로,
    웹훅을 통해 입금 완료를 확인해야 합니다.
    """
    try:
        order_id = payload.get("orderId")
        status = payload.get("status")
        transaction_key = payload.get("transactionKey")

        logger.info(f"🏦 Virtual account deposit - Order: {order_id}, Status: {status}")

        if status == "DONE":
            # 입금 완료 - PAYMENT_STATUS_CHANGED와 동일하게 처리
            # 토스페이먼츠 API로 결제 정보 조회
            payment_data = _fetch_payment_info(transaction_key)

            if payment_data:
                return _handle_payment_status_changed(db, {
                    "eventType": "PAYMENT_STATUS_CHANGED",
                    "data": payment_data
                })
            else:
                logger.error(f"❌ Failed to fetch payment info: {transaction_key}")
                return {"status": "error", "message": "Failed to fetch payment info"}

        return {"status": "success", "message": f"Deposit status: {status}"}

    except Exception as e:
        logger.error(f"❌ Error handling deposit callback: {e}", exc_info=True)
        db.rollback()
        raise


def _handle_cancel_status_changed(db: Session, payload: dict) -> dict:
    """
    CANCEL_STATUS_CHANGED 이벤트 처리
    해외 결제 취소 상태 변경을 처리합니다.
    """
    try:
        data = payload.get("data", {})
        payment_key = data.get("paymentKey")
        cancel_amount = data.get("cancelAmount")
        cancel_reason = data.get("cancelReason")

        logger.info(f"🔄 Cancel status changed - Payment: {payment_key}, Amount: {cancel_amount}, Reason: {cancel_reason}")

        # 결제 레코드 찾기
        payment = db.query(Payment).filter(
            Payment.payment_gateway_charge_id == payment_key
        ).first()

        if payment:
            # 구독 비활성화
            subscription = db.query(Subscription).filter(
                Subscription.id == payment.subscription_id
            ).first()

            if subscription:
                subscription.is_active = 0
                db.commit()
                logger.info(f"✅ Subscription deactivated due to cancellation: {payment_key}")

        return {"status": "success", "message": "Cancel processed"}

    except Exception as e:
        logger.error(f"❌ Error handling cancel status change: {e}", exc_info=True)
        db.rollback()
        raise


def _fetch_payment_info(transaction_key: str) -> dict:
    """
    토스페이먼츠 API로부터 결제 정보를 조회합니다.
    가상계좌 웹훅은 전체 결제 정보를 포함하지 않으므로 별도 조회가 필요합니다.
    """
    try:
        auth_header = base64.b64encode(f"{TOSS_SECRET_KEY}:".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json"
        }

        url = f"{TOSS_BASE_URL}/v1/payments/orders/{transaction_key}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        return response.json()

    except Exception as e:
        logger.error(f"❌ Failed to fetch payment info: {e}")
        return None


def retry_failed_payment(db: Session, payment_id: int, max_retries: int = 3) -> dict:
    """
    실패한 결제를 재시도합니다.

    자동 재시도 시나리오:
    1. 일시적 네트워크 오류
    2. 카드사 시스템 점검
    3. 잔액 부족 (사용자가 입금 후 재시도)

    Args:
        db: 데이터베이스 세션
        payment_id: 재시도할 결제 ID
        max_retries: 최대 재시도 횟수 (기본 3회)

    Returns:
        dict: {"status": "success"} 또는 에러 정보
    """
    try:
        # 결제 레코드 조회
        payment_record = db.query(Payment).filter(Payment.id == payment_id).first()

        if not payment_record:
            logger.error(f"❌ Payment record not found: {payment_id}")
            return {"status": "error", "message": "Payment not found"}

        if payment_record.status == "succeeded":
            logger.info(f"✅ Payment already succeeded: {payment_id}")
            return {"status": "success", "message": "Already succeeded"}

        # 주문 ID에서 정보 추출
        order_id = payment_record.payment_gateway_charge_id

        # 토스페이먼츠 API로 결제 상태 확인
        auth_header = base64.b64encode(f"{TOSS_SECRET_KEY}:".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json"
        }

        url = f"{TOSS_BASE_URL}/v1/payments/{order_id}"

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔄 Payment retry attempt {attempt}/{max_retries} - Order: {order_id}")

                response = requests.get(url, headers=headers)
                response.raise_for_status()
                payment_data = response.json()

                if payment_data.get("status") == "DONE":
                    # 결제 성공 - 구독 업데이트
                    user = db.query(User).filter(User.id == payment_record.user_id).first()
                    parts = order_id.split("_")
                    plan = parts[3]

                    _update_user_subscription(db, user, plan, payment_record.amount, order_id)
                    logger.info(f"✅ Payment retry succeeded - Order: {order_id}")

                    return {"status": "success", "message": "Payment retry succeeded"}

                elif payment_data.get("status") in ["CANCELED", "EXPIRED", "ABORTED"]:
                    # 결제 실패 - 재시도 중단
                    logger.warning(f"⚠️ Payment permanently failed: {payment_data.get('status')}")
                    return {"status": "failed", "message": f"Payment {payment_data.get('status')}"}

                # 아직 대기 중인 경우 다음 시도까지 대기
                if attempt < max_retries:
                    import time
                    wait_time = 2 ** attempt  # 지수 백오프: 2초, 4초, 8초
                    logger.info(f"⏳ Waiting {wait_time} seconds before next retry...")
                    time.sleep(wait_time)

            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Retry attempt {attempt} failed: {e}")
                if attempt == max_retries:
                    return {"status": "error", "message": f"All retries failed: {e}"}

        return {"status": "error", "message": "Max retries exceeded"}

    except Exception as e:
        logger.error(f"❌ Payment retry error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


def get_failed_payments(db: Session, hours: int = 24) -> list:
    """
    최근 실패한 결제 목록을 조회합니다.

    Args:
        db: 데이터베이스 세션
        hours: 조회 기간 (기본 24시간)

    Returns:
        list: 실패한 결제 레코드 목록
    """
    cutoff_time = datetime.now() - timedelta(hours=hours)

    failed_payments = db.query(Payment).filter(
        Payment.status.in_(["failed", "pending"]),
        Payment.created_at >= cutoff_time
    ).all()

    return failed_payments
