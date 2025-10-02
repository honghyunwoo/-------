from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.models.schema import VideoHistory as VideoHistorySchema
from app.services import auth as auth_service
from app.services import history as history_service

router = APIRouter()

@router.get("/", response_model=List[VideoHistorySchema])
def read_user_video_history(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Retrieve the video generation history for the current user.
    """
    history = history_service.get_video_history_by_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return history