
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, func, DateTime
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    category = Column(String, index=True) # e.g., "음식점", "쇼핑몰"
    tags = Column(JSON) # List of tags
    
    # The template parameters will be based on VideoParams schema
    parameters = Column(JSON, nullable=False)

    # if user_id is null, it's a public template
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="templates")

