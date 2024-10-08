from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship

from api.db import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(4096), nullable=False)
    created_at = Column(DateTime)
    team = Column(String(4096))
    main_text = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kinds = Column(String(1024))

    user = relationship("User", back_populates="meetings")
    