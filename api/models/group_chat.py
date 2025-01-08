from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

from api.db import Base


class GroupMessage(Base):
    __tablename__ = "group_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False)
    group_chat_room_id = Column(Integer, ForeignKey("group_chat_rooms.id"), nullable=False)
    content = Column(Text)
    sent_at = Column(DateTime)
    image_url = Column(Text, nullable=True)
    image_name = Column(Text, nullable=True)
    file_url = Column(Text, nullable=True)
    file_name = Column(Text, nullable=True)
    message_type = Column(String(16), nullable=False)
    
    user = relationship("User", back_populates="group_messages")
    group_chat_room = relationship("GroupChatRoom", back_populates="group_messages")
    unread_messages = relationship("UnreadMessage", back_populates="group_message", cascade="all, delete-orphan")

class GroupChatRoom(Base):
    __tablename__ = "group_chat_rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(1024), nullable=False)
    image_url = Column(String(2048), nullable=True)
    image_name = Column(String(256), nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    group_messages = relationship("GroupMessage", back_populates="group_chat_room", cascade="all, delete-orphan")
    group_chat_rooms_users = relationship("GroupChatRoomUser", back_populates="group_chat_room", cascade="all, delete-orphan")
    unread_messages = relationship("UnreadMessage", back_populates="group_chat_room", cascade="all, delete-orphan")

class GroupChatRoomUser(Base):
    __tablename__ = "group_chat_rooms_users"

    id = Column(Integer, primary_key=True, index=True)
    group_chat_room_id = Column(Integer, ForeignKey("group_chat_rooms.id"), nullable=False)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False)
    joined_date = Column(DateTime, nullable=True)
    leave_date = Column(DateTime, nullable=True)
    join = Column(Boolean)

    group_chat_room = relationship("GroupChatRoom", back_populates="group_chat_rooms_users")
    user = relationship("User", back_populates="group_chat_rooms_users")

class UnreadMessage(Base):
    __tablename__ = "unread_messages"

    id = Column(Integer, primary_key=True, index=True)
    group_chat_room_id = Column(Integer, ForeignKey("group_chat_rooms.id"), nullable=False)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False)
    group_message_id = Column(Integer, ForeignKey("group_messages.id"), nullable=False)

    group_chat_room = relationship("GroupChatRoom", back_populates="unread_messages")
    group_message = relationship("GroupMessage", back_populates="unread_messages")
    user = relationship("User", back_populates="unread_messages")
