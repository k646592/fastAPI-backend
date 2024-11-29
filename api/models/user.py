from sqlalchemy import Column, Integer, String, LargeBinary, Boolean
from sqlalchemy.orm import relationship
from api.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(1024))
    grade = Column(String(256))
    group = Column(String(256))
    name = Column(String(1024))
    status = Column(String(256))
    firebase_user_id = Column(String(1024))
    file_name = Column(String(256))
    bytes_data = Column(LargeBinary(length=(2**32)-1))
    now_location = Column(String(256))
    location_flag = Column(Boolean)

    events = relationship("Event", back_populates="user")
    attendances = relationship("Attendance", back_populates="user")
    private_messages = relationship("PrivateMessage", back_populates="user")
    private_chat_rooms_users = relationship("PrivateChatRoomUser", back_populates="user")
    group_messages = relationship("GroupMessage", back_populates="user")
    group_chat_rooms_users = relationship("GroupChatRoomUser", back_populates="user")
    meetings = relationship("Meeting", back_populates="user")
    boards = relationship("Board", back_populates="user")