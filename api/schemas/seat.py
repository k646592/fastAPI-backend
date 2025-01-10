from pydantic import BaseModel

class SeatUpdate(BaseModel):
    id: int
    status: str

class SeatResponse(BaseModel):
    id: int
    status: str

    class Config:
        orm_mode = True
