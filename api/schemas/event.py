from pydantic import BaseModel, Field
from datetime import datetime

class EventBase(BaseModel):
    title: str | None = Field(None, example="ミーティング")
    description: str | None = Field(None, example="詳細情報")
    unit: str | None = Field(None, example="全体")
    user_id: int 
    mail_send: bool = Field(True, description="送信するフラグ")
    start: datetime | None = Field(datetime.now())
    end: datetime | None = Field(datetime.now())

class EventCreate(EventBase):
    pass

class EventCreateResponse(EventCreate):
    id: int

    class Config:
        from_attributes = True

class Event(EventBase):
    id: int

    class Config:
        from_attributes = True

class EventWithUserName(BaseModel):
    id: int
    title: str | None = Field(None, example="ミーティング")
    description: str | None = Field(None, example="詳細情報")
    unit: str | None = Field(None, example="全体")
    user_id: int 
    user_name: str
    mail_send: bool = Field(True, description="送信するフラグ")
    start: datetime | None = Field(datetime.now())
    end: datetime | None = Field(datetime.now())

class EventUpdateBase(BaseModel):
    title: str
    description: str
    unit: str
    user_id: int 
    mail_send: bool
    start: datetime
    end: datetime

class EventUpdate(EventUpdateBase):
    pass

class EventUpdateResponse(EventUpdate):
    id: int

    class Config:
        from_attributes = True


