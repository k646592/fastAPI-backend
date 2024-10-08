from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PrivateMessageBase(BaseModel):
    private_chat_room_id: int
    user_id: int
    sent_at: datetime
    is_read: bool
    content: str
    image_data: bytes
    file_data: bytes
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
    pass

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
    user_id: int

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


class GroupMessageBase(BaseModel):
    group_chat_room_id: int
    user_id: int
    sent_at: datetime
    is_read: bool
    content: str
    image_data: bytes
    file_data: bytes
    file_name: str

class GroupMessageCreate(GroupMessageBase):
    pass

class GroupMessageCreateResponse(GroupMessageCreate):
    id: int

    class Config:
        from_attributes = True

class GroupMessage(GroupMessageBase):
    id: int

    class Config:
        orm_mode = True

class GroupChatRoomBase(BaseModel):
    name: str
    image: bytes
    created_at: datetime

class GroupChatRoomCreate(GroupChatRoomBase):
    pass

class GroupChatRoomCreateResponse(GroupChatRoomCreate):
    id: int

    class Config:
        from_attributes = True

class GroupChatRoom(GroupChatRoomBase):
    id :int

    class Config:
        orm_mode = True

class GroupChatRoomUserBase(BaseModel):
    group_chat_room_id: int
    user_id: int
    joined_date: Optional[datetime] = None
    leave_date: Optional[datetime] = None
    join: bool

class GroupChatRoomUserCreate(GroupChatRoomUserBase):
    pass

class GroupChatRoomUserCreateResponse(GroupChatRoomUserCreate):
    id: int

    class Config:
        orm_mode = True

class GroupChatRoomUser(GroupChatRoomUserBase):
    id :int

    class Config:
        orm_mode = True

class GroupMemberIds(BaseModel):
    member_ids: list[int]