from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from api.db import Base

class Supervisor(Base):
    __tablename__ = "supervisors"

    id = Column(Integer, primary_key=True, index=True)  # ID
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False)  # 投稿者ID

    # Users テーブルとのリレーション
    user = relationship("User", back_populates="supervisor", uselist=False)