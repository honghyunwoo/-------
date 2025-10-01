
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, TEXT, JSON
from sqlalchemy.orm import relationship
from app.database.connection import Base

class VideoHistory(Base):
    __tablename__ = "video_generation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    task_id = Column(String, unique=True, index=True)
    video_subject = Column(String)
    video_script = Column(TEXT)
    video_aspect = Column(String)
    status = Column(String, default="pending") # pending, processing, success, failed
    video_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="video_history")

