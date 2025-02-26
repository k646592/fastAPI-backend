from pydantic import BaseModel, Field
from datetime import datetime

class ReportBase(BaseModel):
    content: str | None = Field(None, example="テストレポート内容")
    created_at: datetime | None = Field(datetime.now(), description="作成日時")
    user_id: str = Field(..., description="投稿者ID")
    user_name: str = Field(..., description="投稿者名")
    recipient_user_id: str = Field(..., description="送信先ユーザーID")
    recipient_user_name: str = Field(..., description="送信先ユーザー名")

class ReportCreate(ReportBase):
    pass

class ReportCreateResponse(ReportCreate):
    id: int

    class Config:
        from_attributes = True

class Report(ReportBase):
    id: int
    roger: bool = Field(False, description="確認済みフラグ")

    class Config:
        from_attributes = True

class ReportWithAdditionalInfo(BaseModel):
    id: int
    content: str | None = Field(None, example="テストレポート内容")
    created_at: datetime | None = Field(datetime.now(), description="作成日時")
    user_id: str = Field(..., description="投稿者ID")
    user_name: str = Field(..., description="投稿者名")
    recipient_user_id: str = Field(..., description="送信先ユーザーID")
    recipient_user_name: str = Field(..., description="送信先ユーザー名")
    roger: bool = Field(False, description="確認済みフラグ")