
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
async def stripe_webhook(request: Request):
    payload = await request.json()
    payment.handle_webhook(payload)
    return {"status": "success"}

