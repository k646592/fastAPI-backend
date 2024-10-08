from pydantic import BaseModel, Field
from datetime import datetime

class AttendanceBase(BaseModel):
   title: str | None = Field(None, example="遅刻")
   description: str | None = Field(None, example="詳細情報")
   user_id: int 
   mail_send: bool = Field(True, description="送信するフラグ")
   undecided: bool = Field(False, description="未定フラグ")
   start: datetime | None = Field(datetime.now())
   end: datetime | None = Field(datetime.now())

class AttendanceCreate(AttendanceBase):
   pass

class AttendanceCreateResponse(AttendanceCreate):
    id: int

    class Config:
        from_attributes = True

class Attendance(AttendanceBase):
    id: int

    class Config:
        from_attributes = True

class AttendanceWithUserName(BaseModel):
    id: int
    title: str | None = Field(None, example="ミーティング")
    description: str | None = Field(None, example="詳細情報")
    user_id: int 
    user_name: str
    mail_send: bool = Field(True, description="送信するフラグ")
    start: datetime | None = Field(datetime.now())
    end: datetime | None = Field(datetime.now())
    undecided: bool = Field(False, description="未定フラグ")

class AttendanceUpdateBase(BaseModel):
    title: str
    description: str
    user_id: int 
    mail_send: bool
    start: datetime
    end: datetime
    undecided: bool

class AttendanceUpdate(AttendanceUpdateBase):
    pass

class AttendanceUpdateResponse(AttendanceUpdate):
    id: int

    class Config:
        from_attributes = True

class UserAttendanceBase(BaseModel):
   name: str
   status: str
   group: str

class UserAttendance(UserAttendanceBase):
   id: int

   class Config:
       from_attributes = True

class UserUpdateStatusBase(BaseModel):
   status: str

class UserUpdateStatus(UserUpdateStatusBase):
   pass

class UserUpdateStatusResponse(UserUpdateStatus):
   id: int

   class Config:
      from_attributes = True