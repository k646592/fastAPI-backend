from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

from api.db import Base

class PrivateMessage(Base):
    __tablename__ = "private_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False)
    private_chat_room_id = Column(Integer, ForeignKey("private_chat_rooms.id"), nullable=False)
    content = Column(Text)
    sent_at = Column(DateTime)
    is_read = Column(Boolean)
    image_url = Column(Text, nullable=True)
    image_name = Column(Text, nullable=True)
    file_url = Column(Text, nullable=True)
    file_name = Column(Text, nullable=True)
    message_type = Column(String(16), nullable=False)
    
    user = relationship("User", back_populates="private_messages")
    private_chat_room = relationship("PrivateChatRoom", back_populates="private_messages")

class PrivateChatRoom(Base):
    __tablename__ = "private_chat_rooms"

    id = Column(Integer, primary_key=True, index=True)
    updated_at = Column(DateTime)
    
    private_messages = relationship("PrivateMessage", back_populates="private_chat_room")
    private_chat_rooms_users = relationship("PrivateChatRoomUser", back_populates="private_chat_room")

class PrivateChatRoomUser(Base):
    __tablename__ = "private_chat_rooms_users"

    id = Column(Integer, primary_key=True, index=True)
    private_chat_room_id = Column(Integer, ForeignKey("private_chat_rooms.id"), nullable=False)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False)

    private_chat_room = relationship("PrivateChatRoom", back_populates="private_chat_rooms_users")
    user = relationship("User", back_populates="private_chat_rooms_users")

