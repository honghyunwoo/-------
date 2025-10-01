
import base64
import json
import os
import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import schema
from app.models.subscription import Payment, Subscription
from app.models.user import User

# 토스페이먼츠 설정
TOSS_CLIENT_KEY = os.getenv("TOSS_CLIENT_KEY", "test_ck_D5GePWvyJnrK0W0k6q8gLzN97Eoq")
TOSS_SECRET_KEY = os.getenv("TOSS_SECRET_KEY", "test_sk_zXLkKEypNArWmo50nX3lmeaxYG5R")
TOSS_BASE_URL = "https://api.tosspayments.com" 


def create_charge(db: Session, user: User, plan: str, amount: int) -> str:
    """
    토스페이먼츠를 사용하여 결제를 생성합니다.
    """
    # 토스페이먼츠 결제 요청
    auth_header = base64.b64encode(f"{TOSS_SECRET_KEY}:".encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/json"
    }

    # 결제 생성 (실제로는 프론트엔드에서 paymentKey를 받아와야 함)
    # 여기서는 데모용으로 간단히 처리
    order_id = f"ORDER_{user.id}_{plan}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # 실제 구현에서는:
    # 1. 프론트엔드에서 토스페이먼츠 SDK로 결제 승인 요청
    # 2. paymentKey를 백엔드로 전송
    # 3. 백엔드에서 결제 승인 확인 API 호출

    # 데모용 charge ID
    charge_id = f"toss_{order_id}"

    # 구독 정보 업데이트
    if plan == "business":
        user.credits = -1  # 무제한
    elif plan == "pro":
        user.credits = 100
    elif plan == "basic":
        user.credits = 20

    user.subscription_plan = plan

    # 구독 레코드 생성
    end_date = datetime.now() + timedelta(days=30)
    subscription = Subscription(
        user_id=user.id,
        plan=plan,
        end_date=end_date,
        is_active=1
    )
    db.add(subscription)

    # 결제 레코드 생성
    payment = Payment(
        user_id=user.id,
        subscription_id=subscription.id,
        amount=amount,
        currency="KRW",
        status="succeeded",
        payment_gateway_charge_id=charge_id
    )
    db.add(payment)

    db.commit()

    return charge_id

def handle_webhook(payload: dict):
    """
    Handles webhooks from the payment gateway.
    This would update the user's subscription status based on the event type.
    """
    # event = stripe.Event.construct_from(payload, stripe.api_key)

    # Handle the event
    # if event.type == 'checkout.session.completed':
    #     session = event.data.object 
    #     # Fulfill the purchase...
    #     pass
    # elif event.type == 'invoice.payment_succeeded':
    #     # ...   
    #     pass

    print(f"Webhook received: {payload}")
    # In a real app, you'd parse the payload and update the DB accordingly.
    return {"status": "success"}

