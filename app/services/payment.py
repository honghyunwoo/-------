
import base64
import json
import os
import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.subscription import Payment, Subscription
from app.models.user import User
from app.models.exception import HttpException

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
            raise HttpException(status_code=400, message=f"Payment not completed: {payment_data.get('status')}")

    except requests.exceptions.RequestException as e:
        # Handle API request errors
        raise HttpException(status_code=500, message=f"Toss Payments API error: {e}")

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
