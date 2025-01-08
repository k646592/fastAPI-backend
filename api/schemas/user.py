from pydantic import BaseModel, Field
from datetime import datetime


class UserBase(BaseModel):
   email: str | None = Field(None, example="example@email.com")
   grade: str | None = Field(None, example="B4")
   group: str | None = Field(None, example="Web班")
   name: str | None = Field(None, example="アルゴリズム")
   status: str | None = Field(None, example="出席")
   now_location: str | None = Field(None, example="キャンパス外")
   location_flag: bool
   image_name: str
   image_url: str


class UserCreate(UserBase):
   pass


class UserCreateResponse(UserCreate):
   id: str


   class Config:
       from_attributes = True

class UserUpdateBase(BaseModel):
   grade: str | None = Field(None, example="B4")
   group: str | None = Field(None, example="Web班")
   name: str | None = Field(None, example="アルゴリズム")

class UserUpdate(UserUpdateBase):
   pass

class UserUpdateResponse(UserUpdate):
   id: str

   class Config:
      from_attributes = True

class UserUpdateImageBase(BaseModel):
   image_name: str
   image_url: str

class UserUpdateImage(UserUpdateImageBase):
   pass

class UserUpdateImageResponse(UserUpdateImage):
   id: str

   class Config:
      from_attributes = True

class UserUpdateEmailBase(BaseModel):
   email: str | None = Field(None, example="example@email.com")

class UserUpdateEmail(UserUpdateEmailBase):
   pass

class UserUpdateEmailResponse(UserUpdateEmail):
   id: str

   class Config:
      from_attributes = True

class User(UserBase):
   id: str

   class Config:
       from_attributes = True

class UserInGroupChat(BaseModel):
   id: str
   email: str
   grade: str
   group: str
   name: str
   status: str
   image_name: str
   image_url: str
   joined_date: datetime | None
   leave_date: datetime | None
   join: bool

   class Config:
      from_attributes = True

class UserGetBase(BaseModel):
   email: str | None = Field(None, example="example@email.com")
   grade: str | None = Field(None, example="B4")
   group: str | None = Field(None, example="Web班")
   name: str | None = Field(None, example="アルゴリズム")
   status: str | None = Field(None, example="出席")
   image_name: str
   image_url: str
   now_location: str
   location_flag: bool

class UserGet(UserGetBase):
   id: str

class UserGetNameBase(BaseModel):
   name:str

   class Config:
      from_attributes = True

class UserGetName(UserGetNameBase):
   id: str

   class Config:
      from_attributes = True

class UserUpdateLocationBase(BaseModel):
   now_location: str

class UserUpdateLocation(UserUpdateLocationBase):
   pass

class UserUpdateLocationResponse(UserUpdateLocation):
   id: str

   class Config:
      from_attributes = True