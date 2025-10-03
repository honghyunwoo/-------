from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database.connection import get_db
from app.models.user import User
from app.services import auth as auth_service
from app.services import email as email_service
from app.models.schema import UserCreate, UserLogin, Token, UserResponse
from app.utils import utils
from app.middleware.security import limiter

router = APIRouter()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/hour")  # 시간당 5회 회원가입 제한
def register_user(request: Request, user_create: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    db_user = auth_service.get_user_by_email(db, email=user_create.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = auth_service.create_user(db=db, user=user_create)

    # Send verification email
    token = email_service.generate_verification_token(email=user.email)
    email_service.send_verification_email(email=user.email, token=token)

    return user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")  # 분당 10회 로그인 시도 제한 (Brute Force 방지)
def login_for_access_token(request: Request, form_data: UserLogin, db: Session = Depends(get_db)):
    """
    Log in a user and return an access token.
    """
    user = auth_service.authenticate_user(
        db, email=form_data.email, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified. Please check your inbox.",
        )

    access_token_expires = timedelta(minutes=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/verify-email")
def verify_user_email(token: str, db: Session = Depends(get_db)):
    """
    Verify user's email address with the provided token.
    """
    email = email_service.verify_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    user = auth_service.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.is_verified:
        return {"message": "Email already verified."}

    user.is_verified = True
    db.commit()

    return {"message": "Email verified successfully. You can now log in."}


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    """
    Get the current logged-in user's information.
    """
    return current_user