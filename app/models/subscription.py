
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan = Column(String, nullable=False)
    start_date = Column(DateTime, default=func.now())
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Integer, default=1)
    auto_renew = Column(Integer, default=1)  # 자동 갱신 여부 (1: 활성화, 0: 비활성화)
    billing_key = Column(String, unique=True, index=True)  # 토스페이먼츠 자동결제용 빌링키 (정기결제용)
    last_renewed_at = Column(DateTime)  # 마지막 갱신 일시
    next_billing_date = Column(DateTime)  # 다음 결제 예정일

    user = relationship("User", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    amount = Column(Integer, nullable=False)  # 금액 (원 단위, Integer로 변경하여 부동소수점 오류 방지)
    currency = Column(String, default="KRW")
    status = Column(String, nullable=False)
    payment_gateway_charge_id = Column(String, unique=True)  # order_id (예: owl_123_1696305600_pro)
    payment_key = Column(String, unique=True, index=True)    # 토스페이먼츠 결제 고유 ID (취소/환불 추적용)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")

