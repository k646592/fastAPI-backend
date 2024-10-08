from pydantic import BaseModel, Field
from datetime import datetime


class UserBase(BaseModel):
   email: str | None = Field(None, example="example@email.com")
   grade: str | None = Field(None, example="B4")
   group: str | None = Field(None, example="Web班")
   name: str | None = Field(None, example="アルゴリズム")
   status: str | None = Field(None, example="出席")
   firebase_user_id: str
   file_name: str
   bytes_data: bytes
   now_location: str | None = Field(None, example="キャンパス外")


class UserCreate(UserBase):
   pass


class UserCreateResponse(UserCreate):
   id: int


   class Config:
       from_attributes = True

class UserUpdateBase(BaseModel):
   grade: str | None = Field(None, example="B4")
   group: str | None = Field(None, example="Web班")
   name: str | None = Field(None, example="アルゴリズム")

class UserUpdate(UserUpdateBase):
   pass

class UserUpdateResponse(UserUpdate):
   id: int

   class Config:
      from_attributes = True

class UserUpdateImageBase(BaseModel):
   file_name: str
   bytes_data: bytes

class UserUpdateImage(UserUpdateImageBase):
   pass

class UserUpdateImageResponse(UserUpdateImage):
   id: int

   class Config:
      from_attributes = True

class UserUpdateEmailBase(BaseModel):
   email: str | None = Field(None, example="example@email.com")

class UserUpdateEmail(UserUpdateEmailBase):
   pass

class UserUpdateEmailResponse(UserUpdateEmail):
   id: int

   class Config:
      from_attributes = True

class User(UserBase):
   id: int

   class Config:
       from_attributes = True

class UserInGroupChat(BaseModel):
   id: int
   email: str
   grade: str
   group: str
   name: str
   status: str
   firebase_user_id: str
   file_name: str
   bytes_data: bytes
   joined_date: datetime | None
   leave_date: datetime | None
   join: bool

   class Config:
      from_attributes = True

class UserGetBase(BaseModel):
   id: int 
   email: str | None = Field(None, example="example@email.com")
   grade: str | None = Field(None, example="B4")
   group: str | None = Field(None, example="Web班")
   name: str | None = Field(None, example="アルゴリズム")
   status: str | None = Field(None, example="出席")
   file_name: str
   now_location: str
   bytes_data: bytes


class UserGet(UserGetBase):
   firebase_user_id: str


   class Config:
       from_attributes = True

class UserGetIdBase(BaseModel):
   id: int

class UserGetId(UserGetIdBase):
   firebase_user_id: str

   class Config:
      from_attributes = True

class UserGetNameIdBase(BaseModel):
   id: int
   name: str

class UserGetNameId(UserGetNameIdBase):
   firebase_user_id: str

   class Config:
      from_attributes = True

class UserGetNameBase(BaseModel):
   name:str

class UserGetName(UserGetNameBase):
   id: int

   class Config:
      from_attributes = True

class UserUpdateLocationBase(BaseModel):
   now_location: str

class UserUpdateLocation(UserUpdateLocationBase):
   pass

class UserUpdateLocationResponse(UserUpdateLocation):
   firebase_user_id: str

   class Config:
      from_attributes = True