from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from api.db import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(1024))
    description = Column(String(1024))
    unit = Column(String(1024))
    start = Column(DateTime)
    end = Column(DateTime)
    mail_send = Column(Boolean)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    user = relationship("User", back_populates="events")
