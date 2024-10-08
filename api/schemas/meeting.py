from pydantic import BaseModel, Field
from datetime import datetime

class MeetingBase(BaseModel):
    title: str | None = Field(None, example="テスト")
    created_at: datetime | None = Field(datetime.now())
    team: str | None = Field(None, example="All")
    main_text: str 
    user_id: int
    kinds: str | None = Field(None, example="ミーティング")

class MeetingCreate(MeetingBase):
    pass

class MeetingCreateResponse(MeetingCreate):
    id: int

    class Config:
        from_attributes = True

class Meeting(MeetingBase):
    id: int

    class Config:
        from_attributes = True

class MeetingWithUserName(BaseModel):
    id: int
    title: str
    created_at: datetime
    team: str
    main_text: str
    user_id: int
    user_name: str
    kinds: str

class MeetingUpdateBase(BaseModel):
    title: str
    team: str
    kinds: str

class MeetingUpdate(MeetingUpdateBase):
    pass

class MeetingUpdateResponse(MeetingUpdate):
    id: int

    class Config:
        from_attributes = True

class MeetingUpdateMainTextBase(BaseModel):
    main_text: str

class MeetingUpdateMainText(MeetingUpdateMainTextBase):
    pass

class MeetingUpdateMainTextResponse(MeetingUpdateMainText):
    id: int
    
    class Config:
        from_attributes = True