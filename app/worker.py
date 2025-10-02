import asyncio
from celery import Celery
from sqlalchemy.orm import Session

from app.config.config import config
from app.database.connection import SessionLocal
from app.models.schema import VideoParams
from app.models.user import User
from app.services import task as tm

_enable_redis = config.app.get("enable_redis", False)
_redis_host = config.app.get("redis_host", "localhost")
_redis_port = config.app.get("redis_port", 6379)
_redis_db = config.app.get("redis_db", 0)
_redis_password = config.app.get("redis_password", None)

redis_url = f"redis://:{_redis_password}@{_redis_host}:{_redis_port}/{_redis_db}" if _redis_password else f"redis://{_redis_host}:{_redis_port}/{_redis_db}"

celery_app = Celery(
    "tasks",
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_track_started=True,
    result_expires=3600,
)

@celery_app.task(name="app.worker.generate_video_task")
def generate_video_task(task_id: str, params_dict: dict, user_id: int, stop_at: str):
    """
    Celery task to generate video.
    We pass serializable data (user_id, params_dict) and reconstruct objects inside the task.
    """
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        params = VideoParams(**params_dict)
        asyncio.run(tm.start(task_id=task_id, params=params, db=db, user=user, stop_at=stop_at))
    finally:
        db.close()