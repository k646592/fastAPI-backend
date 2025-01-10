from sqlalchemy import Column, String, Integer
from api.db import Base

class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True) # 座席番号
    status = Column(String(256), nullable=False) # Occupied/Enpty
