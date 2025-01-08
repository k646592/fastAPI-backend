from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# 個人チャットのスキーマ

class PrivateChatUser(BaseModel):
    id: str
    email: str
    grade: str
    group: str
    name: str
    status: str
    image_name: str
    image_url: str
    now_location: str
    location_flag: bool
    updated_at: datetime | None
    unread_count: int

class PrivateChatRoomInfo(BaseModel):
    private_chat_room_id: int
    user_id: str
    updated_at: datetime
    unread_count: int

class PrivateMessageUnreadUpdate(BaseModel):
    id: int
    is_read: bool

class PrivateMessageBase(BaseModel):
    private_chat_room_id: int
    user_id: str
    sent_at: datetime
    is_read: bool
    message_type: str
    content: str
    image_url: str
    image_name: str
    file_url: str
    file_name: str

class PrivateMessageCreate(PrivateMessageBase):
    pass

class PrivateMessageCreateResponse(PrivateMessageCreate):
    id: int

    class Config:
        from_attributes = True

class PrivateMessage(PrivateMessageBase):
    id: int

    class Config:
        orm_mode = True

class PrivateChatRoomBase(BaseModel):
    updated_at: datetime

class PrivateChatRoomCreate(PrivateChatRoomBase):
    pass

class PrivateChatRoomCreateResponse(PrivateChatRoomCreate):
    id: int

    class Config:
        from_attributes = True

class PrivateChatRoom(PrivateChatRoomBase):
    id :int

    class Config:
        orm_mode = True

class PrivateChatRoomUserBase(BaseModel):
    private_chat_room_id: int
    user_id: str

class PrivateChatRoomUserCreate(PrivateChatRoomUserBase):
    pass

class PrivateChatRoomUserCreateResponse(PrivateChatRoomUserCreate):
    id: int

    class Config:
        orm_mode = True

class PrivateChatRoomUser(PrivateChatRoomUserBase):
    id :int

    class Config:
        orm_mode = True

class PrivateChatRoomUpdateBase(BaseModel):
    updated_at: datetime

class PrivateChatRoomUpdate(PrivateChatRoomUpdateBase):
    pass

class PrivateChatRoomUpdateResponse(PrivateChatRoomUpdate):
    id: int

    class Config:
        orm_mode = True

