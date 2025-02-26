from pydantic import BaseModel

class DeviceInfoBase(BaseModel):
    user_id: str
    mac_address: str

class DeviceInfoCreate(DeviceInfoBase):
    pass

class DeviceInfoCreateResponse(DeviceInfoCreate):
    id: int

    class Config:
        from_attributes = True

class DeviceInfoUpdateBase(BaseModel):
    user_id: str
    mac_address: str

class DeviceInfoUpdate(DeviceInfoUpdateBase):
    pass

class DeviceInfoUpdateResponse(DeviceInfoUpdate):
    id: int

    class Config:
        from_attributes = True