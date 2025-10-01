
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 상용화 관련 필드
    subscription_plan = Column(String, default="free")
    credits = Column(Integer, default=3) # 무료 사용자는 3개 크레딧

    # 관계 설정
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    video_history = relationship("VideoHistory", back_populates="user", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="user", cascade="all, delete-orphan")
    branding = relationship("Branding", back_populates="user", uselist=False, cascade="all, delete-orphan")
    owned_teams = relationship("Team", back_populates="owner", cascade="all, delete-orphan")
    teams = relationship("Team", secondary="team_member_association", back_populates="members")

