from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import json

import api.cruds.event as event_crud
from api.db import get_db

import api.schemas.event as event_schema

router = APIRouter()

class ConnectionEventManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))

# インスタンスを作成
connection_event_manager = ConnectionEventManager()

@router.websocket("/ws_event_list")
async def websocket_event_endpoint(websocket: WebSocket):
    await connection_event_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await connection_event_manager.broadcast(message)
    except WebSocketDisconnect:
        connection_event_manager.disconnect(websocket)
    except json.JSONDecodeError:
        print("Invalid JSON format")
    except Exception as e:
        connection_event_manager.disconnect(websocket)
        print(f"WebSocket Error: {e}")  # ログにエラー出力

@router.get("/events", response_model=list[event_schema.EventWithUserName])
async def list_events(db: AsyncSession = Depends(get_db)):
    return await event_crud.get_events(db)

@router.post("/events", response_model=event_schema.EventCreateResponse)
async def create_event(
    event_body: event_schema.EventCreate, db: AsyncSession = Depends(get_db)
):
    try:
        new_event = await event_crud.create_event(db, event_body)
        user = await event_crud.get_user(db, new_event.user_id)

        # 更新が成功した後、WebSocketを通じてユーザーにメッセージを送信
        message = {
                "action": "create",
                "id": new_event.id, 
                "title": new_event.title, 
                "description": new_event.description, 
                "unit": new_event.unit,
                "user_id": new_event.user_id, 
                "user_name": user.name, 
                "mail_send": new_event.mail_send, 
                "start": event_body.start.isoformat(), 
                "end": event_body.end.isoformat(), 
        }
        await connection_event_manager.broadcast(message)
        return new_event
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.patch("/events/{id}", response_model=event_schema.EventUpdateResponse)
async def update_event(
    id: int, 
    event_body: event_schema.EventUpdate, 
    db: AsyncSession = Depends(get_db)
):
    event = await event_crud.get_event(db, id=id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    
    updated_event = await event_crud.update_event(db, event_body, original=event)
    message = {
                "action": "update",  # 追加: アクションの種類を指定
                "id": updated_event.id, 
                "title": updated_event.title,
                "description": updated_event.description, 
                "mail_send": updated_event.mail_send,
                "start": event_body.start.isoformat(), 
                "end": event_body.end.isoformat(), 
                "unit": updated_event.unit,
    }
    await connection_event_manager.broadcast(message)
    return updated_event

@router.delete("/events/{id}", response_model=None)
async def delete_event(id: int, db: AsyncSession = Depends(get_db)):
    event = await event_crud.get_event(db, id=id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    await event_crud.delete_event(db, original=event)

    # 更新が成功した後、WebSocketを通じてユーザーにメッセージを送信
    message = {
        "action": "delete",  # 追加: アクションの種類を指定
        "id": id,
    }
    await connection_event_manager.broadcast(message)

    return {"detail": "Event deleted successfully"}