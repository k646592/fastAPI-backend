from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from api.db import Base

class Board(Base):
    __tablename__ = "boards"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    created_at = Column(DateTime)
    group = Column(String(128))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    user = relationship("User", back_populates="boards")
