from pydantic import BaseModel

class DoorStatus(BaseModel):
    status: str