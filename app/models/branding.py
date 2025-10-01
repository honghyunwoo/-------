
from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Branding(Base):
    __tablename__ = "branding"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True) # Each user has one branding profile
    
    logo_image_path = Column(String, nullable=True)
    brand_colors = Column(JSON, nullable=True) # e.g., {"primary": "#FFFFFF", "secondary": "#000000"}
    default_font = Column(String, nullable=True)

    user = relationship("User", back_populates="branding")

