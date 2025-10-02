from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class VideoHistory(Base):
    __tablename__ = "video_histories"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_path = Column(String, nullable=False)
    video_subject = Column(String)
    parameters = Column(JSON)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User")