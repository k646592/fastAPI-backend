from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from api.db import Base

class DeviceInfo(Base):
    __tablename__ = "device_info"

    id = Column(Integer, primary_key=True, index=True)  # firebaseのuid
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    mac_address = Column(Text, nullable=False)

    user = relationship("User", back_populates="device_info")