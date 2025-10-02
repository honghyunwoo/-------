from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.services import auth as auth_service
from app.services import payment as payment_service
from app.models.exception import HttpException

router = APIRouter()


@router.get("/success")
async def payment_success(
    paymentKey: str,
    orderId: str,
    amount: int,
    db: Session = Depends(get_db),
    # In a real app, you'd get the user from the session/token after they are redirected back
    # For this example, we'll assume the user is identifiable from the orderId or a session
    # current_user: User = Depends(auth_service.get_current_user)
):
    """
    Handle the success callback from Toss Payments.
    """
    try:
        # For demo purposes, we extract user_id from orderId.
        # A more robust solution would use a secure session.
        user_id = int(orderId.split("_")[1])
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HttpException(status_code=404, message="User not found")
        payment_result = payment_service.confirm_payment(
            db, user, paymentKey, orderId, amount
        )
        # Redirect to a success page in the frontend
        return RedirectResponse(url=f"/payment-result?status=success&orderId={orderId}")

    except HttpException as e:
        return RedirectResponse(url=f"/payment-result?status=fail&message={e.message}")
    except Exception as e:
        return RedirectResponse(
            url=f"/payment-result?status=fail&message=An_unexpected_error_occurred"
        )


@router.post("/webhook")
async def payment_webhook(request: Request):
    payload = await request.json()
    # Process webhook for recurring payments, refunds, etc.
    return payment_service.handle_webhook(payload)