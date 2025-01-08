from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from api.db import Base

class Board(Base):
    __tablename__ = "boards"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    created_at = Column(DateTime)
    group = Column(String(128))
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    
    user = relationship("User", back_populates="boards")
    acknowledgements = relationship("Acknowledgement", back_populates="board")


# 了解機能の中間テーブル
class Acknowledgement(Base):
    __tablename__ = "acknowledgements"
    
    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("boards.id"), nullable=False)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False)

    board = relationship("Board", back_populates="acknowledgements")
    user = relationship("User", back_populates="acknowledgements")
