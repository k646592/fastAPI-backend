from pydantic import BaseModel

class DeviceInfoBase(BaseModel):
    user_id: str
    host_name: str

class DeviceInfoCreate(DeviceInfoBase):
    pass

class DeviceInfoCreateResponse(DeviceInfoCreate):
    id: int

    class Config:
        from_attributes = True

class DeviceInfoUpdateBase(BaseModel):
    user_id: str
    host_name: str

class DeviceInfoUpdate(DeviceInfoUpdateBase):
    pass

class DeviceInfoUpdateResponse(DeviceInfoUpdate):
    id: int

    class Config:
        from_attributes = True