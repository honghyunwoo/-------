"""
Service for managing video generation history.

This module provides functions to create and retrieve video history records
from the database, allowing users to track their past creations.
"""
from typing import List
from sqlalchemy.orm import Session

from app.models.video_history import VideoHistory
from app.models.user import User
from app.models.schema import VideoParams


def create_video_history(
    db: Session, task_id: str, user: User, video_path: str, params: VideoParams
) -> VideoHistory:
    """
    Create and save a new video history record.

    Args:
        db (Session): The database session.
        task_id (str): The unique ID of the completed task.
        user (User): The user who created the video.
        video_path (str): The file path of the final generated video.
        params (VideoParams): The parameters used for the video generation.

    Returns:
        VideoHistory: The newly created VideoHistory database object.
    """
    db_history = VideoHistory(
        task_id=task_id,
        user_id=user.id,
        video_path=video_path,
        video_subject=params.video_subject,
        parameters=params.model_dump(mode="json"),
    )
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return db_history


def get_video_history_by_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 10
) -> List[VideoHistory]:
    """
    Retrieve a paginated list of video histories for a specific user.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user whose history is to be retrieved.
        skip (int): The number of records to skip for pagination. Defaults to 0.
        limit (int): The maximum number of records to return. Defaults to 10.

    Returns:
        List[VideoHistory]: A list of VideoHistory objects for the user,
        ordered by creation date in descending order.
    """
    return (
        db.query(VideoHistory)
        .filter(VideoHistory.user_id == user_id)
        .order_by(VideoHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )