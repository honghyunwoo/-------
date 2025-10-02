from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.services import auth as auth_service
from app.services import admin as admin_service

router = APIRouter()


def get_current_admin_user(
    current_user: User = Depends(auth_service.get_current_user),
) -> User:
    """
    Dependency to check if the current user is a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user

@router.get("/stats", dependencies=[Depends(get_current_admin_user)])
def get_admin_dashboard_stats(db: Session = Depends(get_db)):
    """
    Retrieve statistics for the admin dashboard.
    """
    stats = admin_service.get_dashboard_stats(db)
    return stats