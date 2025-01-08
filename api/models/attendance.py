from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from api.db import Base

class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(1024))
    description = Column(String(1024))
    start = Column(DateTime)
    end = Column(DateTime)
    mail_send = Column(Boolean)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False)
    undecided = Column(Boolean)
    
    user = relationship("User", back_populates="attendances")

