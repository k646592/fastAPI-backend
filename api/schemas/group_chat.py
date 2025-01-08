from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class GetChatMemberCreateBase(BaseModel):
    id: str
    group: str
    grade: str
    name: str

class UpdateGroupChatRoomTime(BaseModel):
    id: int
    updated_at: datetime

class GroupMessageBase(BaseModel):
    group_chat_room_id: int
    user_id: str
    sent_at: datetime
    message_type: str
    content: str
    image_url: str
    image_name: str
    file_url: str
    file_name: str

class GroupMessageCreate(GroupMessageBase):
    pass

class GroupMessageCreateResponse(GroupMessageCreate):
    id: int

    class Config:
        from_attributes = True

class GroupMessage(BaseModel):
    id: int
    group_chat_room_id: int
    user_id: str
    sent_at: datetime
    message_type: str
    content: str
    image_url: str
    image_name: str
    file_url: str
    file_name: str
    unread_count: int

    class Config:
        orm_mode = True

class GroupChatRoomBase(BaseModel):
    name: str
    created_at: datetime
    updated_at: datetime
    image_url: str
    image_name: str

class GroupChatRoomCreate(GroupChatRoomBase):
    pass

class GroupChatRoomCreateResponse(GroupChatRoomCreate):
    id: int

    class Config:
        from_attributes = True

class GetGroupChatRoom(GroupChatRoomBase):
    id: int

    class Config:
        orm_mode = True

class GroupChatRoom(BaseModel):
    id :int
    name: str
    created_at: datetime
    updated_at: datetime
    image_url: str
    image_name: str
    unread_count: int

    class Config:
        orm_mode = True

class GroupChatRoomUserBase(BaseModel):
    group_chat_room_id: int
    user_id: str
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
    member_ids: list[str]

class UnreadMessageBase(BaseModel):
    group_chat_room_id: int
    user_id: str
    group_message_id: int
    updated_at: datetime

class UnreadMessageCreate(UnreadMessageBase):
    pass

class UnreadMessageCreateResponse(UnreadMessageCreate):
    id: int

    class Config:
        orm_mode = True

class GroupChatRoomUserData(BaseModel):
    id: str
    email: str
    group: str
    grade: str
    name: str
    status: str
    image_url: str
    image_name: str
    joinded_date: datetime | None
    leave_date: datetime | None
    join: bool

class GroupMessageUnreadUpdate(BaseModel):
    group_message_id: int
    

class GroupChatMessage(BaseModel):
    id: int
    group_chat_room_id: int
    user_id: str
    message_type: str
    sent_at: datetime
    content: str
    image_name: str
    image_url: str
    file_name: str
    file_url: str