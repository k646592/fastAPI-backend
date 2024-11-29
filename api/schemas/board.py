from pydantic import BaseModel, Field
from datetime import datetime

class BoardBase(BaseModel):
    content: str | None = Field(None, example="テスト掲示板文章")
    created_at: datetime | None = Field(datetime.now())
    group: str | None = Field(None, example="All")
    user_id: int

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

class BoardWithUserName(BaseModel):
    id: int
    content: str | None = Field(None, example="テスト掲示板文章")
    created_at: datetime | None = Field(datetime.now())
    group: str | None = Field(None, example="All")
    user_id: int
    user_name: str