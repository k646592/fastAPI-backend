from pydantic import BaseModel, Field
from datetime import datetime

class BoardBase(BaseModel):
    content: str | None = Field(None, example="テスト掲示板文章")
    created_at: datetime | None = Field(datetime.now())
    group: str | None = Field(None, example="All")
    user_id: str

class BoardCreate(BoardBase):
    pass

class BoardCreateResponse(BoardCreate):
    id: int

    class Config:
        from_attributes = True

class Board(BoardBase):
    id: int

    class Config:
        from_attributes = True

class BoardWithOtherInfo(BaseModel):
    id: int
    content: str | None = Field(None, example="テスト掲示板文章")
    created_at: datetime | None = Field(datetime.now())
    group: str | None = Field(None, example="All")
    user_id: str
    user_name: str
    acknowledgements: int
    is_acknowledged: bool

class AcknowledgementBase(BaseModel):
    board_id: int
    user_id: str
    created_at: datetime | None = Field(datetime.now())

class AcknowledgementCreate(AcknowledgementBase):
    pass

class AcknowledgementCreateResponse(AcknowledgementCreate):
    id: int

    class Config:
        from_attributes = True

class Acknowledgement(AcknowledgementBase):
    id: int

    class Config:
        from_attributes = True

class AcknowledgementsWithUserInfo(BaseModel):
    created_at: datetime | None = Field(datetime.now())
    user_id: str
    user_name: str
    image_url: str
    image_name: str