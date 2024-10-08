from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship

from api.db import Base

class PrivateMessage(Base):
    __tablename__ = "private_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    private_chat_room_id = Column(Integer, ForeignKey("private_chat_rooms.id"), nullable=False)
    content = Column(Text)
    sent_at = Column(DateTime)
    is_read = Column(Boolean)
    image_data = Column(LargeBinary(length=(2**32)-1))
    file_data = Column(LargeBinary(length=(2**32)-1))
    file_name = Column(String(4096))
    
    user = relationship("User", back_populates="private_messages")
    private_chat_room = relationship("PrivateChatRoom", back_populates="private_messages")

class PrivateChatRoom(Base):
    __tablename__ = "private_chat_rooms"
    id = Column(Integer, primary_key=True, index=True)
    
    private_messages = relationship("PrivateMessage", back_populates="private_chat_room")
    private_chat_rooms_users = relationship("PrivateChatRoomUser", back_populates="private_chat_room")

class PrivateChatRoomUser(Base):
    __tablename__ = "private_chat_rooms_users"
    id = Column(Integer, primary_key=True, index=True)
    private_chat_room_id = Column(Integer, ForeignKey("private_chat_rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    private_chat_room = relationship("PrivateChatRoom", back_populates="private_chat_rooms_users")
    user = relationship("User", back_populates="private_chat_rooms_users")

class GroupMessage(Base):
    __tablename__ = "group_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_chat_room_id = Column(Integer, ForeignKey("group_chat_rooms.id"), nullable=False)
    content = Column(Text)
    sent_at = Column(DateTime)
    is_read = Column(Boolean)
    image_data = Column(LargeBinary(length=(2**32)-1))
    file_data = Column(LargeBinary(length=(2**32)-1))
    file_name = Column(String(4096))
    
    user = relationship("User", back_populates="group_messages")
    group_chat_room = relationship("GroupChatRoom", back_populates="group_messages")

class GroupChatRoom(Base):
    __tablename__ = "group_chat_rooms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(1024), nullable=False)
    image = Column(LargeBinary(length=(2**32)-1))
    created_at = Column(DateTime)

    group_messages = relationship("GroupMessage", back_populates="group_chat_room", cascade="all, delete-orphan")
    group_chat_rooms_users = relationship("GroupChatRoomUser", back_populates="group_chat_room", cascade="all, delete-orphan")

class GroupChatRoomUser(Base):
    __tablename__ = "group_chat_rooms_users"
    id = Column(Integer, primary_key=True, index=True)
    group_chat_room_id = Column(Integer, ForeignKey("group_chat_rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_date = Column(DateTime, nullable=True)
    leave_date = Column(DateTime, nullable=True)
    join = Column(Boolean)

    group_chat_room = relationship("GroupChatRoom", back_populates="group_chat_rooms_users")
    user = relationship("User", back_populates="group_chat_rooms_users")

