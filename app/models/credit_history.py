"""
크레딧 히스토리 모델: 사용자의 크레딧 사용 내역 추적
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.models import Base


class CreditHistory(Base):
    """크레딧 사용 내역 테이블"""

    __tablename__ = "credit_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 크레딧 변동
    amount = Column(Integer, nullable=False)  # 양수: 충전, 음수: 사용
    balance_after = Column(Integer, nullable=False)  # 변동 후 잔액

    # 사용 유형
    action_type = Column(String, nullable=False, index=True)  # video_generation, subscription_purchase, admin_grant, refund
    description = Column(Text, nullable=True)  # 상세 설명

    # 관련 정보
    related_id = Column(String, nullable=True)  # task_id, subscription_id 등

    # 시간 정보
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 관계
    user = relationship("User", back_populates="credit_history")


    def __repr__(self):
        return f"<CreditHistory(user_id={self.user_id}, amount={self.amount}, type={self.action_type})>"
