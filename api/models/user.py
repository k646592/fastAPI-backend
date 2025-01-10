from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship
from api.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(32), primary_key=True, index=True)  # firebaseのuid
    email = Column(String(1024))
    grade = Column(String(256))
    group = Column(String(256))
    name = Column(String(1024))
    status = Column(String(256))
    image_name = Column(Text)
    image_url = Column(Text)
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
    acknowledgements = relationship("Acknowledgement", back_populates="user")
    unread_messages = relationship("UnreadMessage", back_populates="user", cascade="all, delete-orphan")
    device_info = relationship("DeviceInfo", back_populates="user", uselist=False)