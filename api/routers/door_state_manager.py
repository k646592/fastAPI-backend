from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

import api.cruds.door_state_manager as door_state_manager_crud
from api.db import get_db

import api.schemas.door_state_manager as door_state_manager_schema

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

# インスタンスを作成
connection_manager = ConnectionManager()

@router.websocket("/ws_door_status")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await connection_manager.broadcast(data)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)

@router.post("/door_status", response_model=None)
async def door_status_post(
    status_body: door_state_manager_schema.DoorStatus,
    db: AsyncSession = Depends(get_db)
):
    await connection_manager.broadcast(status_body.status)
    door_state = await door_state_manager_crud.get_door_state(db, id=1)
    if door_state is None:
        await door_state_manager_crud.create_door_state(db, status_body)
        return JSONResponse(content={"message": "Status send successfully (inital_status)"})
    else :
        if door_state.status == status_body.status:
            return JSONResponse(content={"message": "Status send successfully"})
        else :
            await door_state_manager_crud.update_door_state(db, status_body, original=door_state)
            return JSONResponse(content={"message": "Status send & update successfully"})
    
@router.get("/door_status", response_model=None)
async def door_status_get(
    db: AsyncSession = Depends(get_db)
):
    door_state = await door_state_manager_crud.get_door_state(db, id=1)
    if door_state is None:
        status = "unknown"
        return status
    else :
        return door_state.status
