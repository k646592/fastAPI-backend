from sqlalchemy import Column, String, Integer

from api.db import Base

class DoorStateManager(Base):
    __tablename__ = "door_state_managers"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(256), nullable=False)

