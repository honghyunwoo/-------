
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

    user = relationship("User", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    amount = Column(Float, nullable=False)
    currency = Column(String, default="KRW")
    status = Column(String, nullable=False)
    payment_gateway_charge_id = Column(String, unique=True)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")

