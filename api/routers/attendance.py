from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import json 
import asyncio

import api.cruds.attendance as attendance_crud
from api.db import get_db

import api.schemas.attendance as attendance_schema

router = APIRouter()

class BaseConnectionManager:
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

class ConnectionManager(BaseConnectionManager):
    pass

class ConnectionAttendanceManager(BaseConnectionManager):
    pass

# インスタンスを作成
connection_manager = ConnectionManager()
connection_attendance_manager = ConnectionAttendanceManager()


@router.websocket("/ws_user_status")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await connection_manager.broadcast(message)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        connection_manager.disconnect(websocket)
        print(f"WebSocket Error: {e}")  # エラーログを出力

@router.websocket("/ws_attendance_list")
async def websocket_attendance_endpoint(websocket: WebSocket):
    await connection_attendance_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await connection_attendance_manager.broadcast(message)
    except WebSocketDisconnect:
        connection_attendance_manager.disconnect(websocket)
    except asyncio.TimeoutError:
        connection_attendance_manager.disconnect(websocket)
        print("WebSocket connection timed out.")
    except Exception as e:
        connection_attendance_manager.disconnect(websocket)
        print(f"WebSocket Error: {e}")

@router.get("/users_attendance", response_model=list[attendance_schema.UserAttendance])
async def list_attendance_users(db: AsyncSession = Depends(get_db)):
    users = await attendance_crud.get_users(db)
    result = []
    for user in users:
        result.append(attendance_schema.UserAttendance(
            id=user.id,
            name=user.name,
            group=user.group,
            status=user.status,
        ))
    return result

@router.patch("/update_user_status/{user_id}", response_model=attendance_schema.UserUpdateStatusResponse)
async def update_user_status(
    user_id: str,
    update_status_body: attendance_schema.UserUpdateStatus,
    db: AsyncSession = Depends(get_db)
):
    user = await attendance_crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_user_status = await attendance_crud.update_user_status(db, update_status_body, original=user)

    # 更新が成功した後、WebSocketを通じてユーザーにメッセージを送信
    message = {"user_id": user_id, "status": update_user_status.status}
    await connection_manager.broadcast(message)

    return update_user_status

@router.get("/attendances", response_model=list[attendance_schema.AttendanceWithUserName])
async def list_attendances(db: AsyncSession = Depends(get_db)):
    return await attendance_crud.get_attendances(db)
    
@router.post("/attendances", response_model=attendance_schema.AttendanceCreateResponse)
async def create_attendance(
    attendance_body: attendance_schema.AttendanceCreate, db: AsyncSession = Depends(get_db)
):
    try:
        new_attendance = await attendance_crud.create_attendance(db, attendance_body)
        user = await attendance_crud.get_user(db, new_attendance.user_id)
        # 更新が成功した後、WebSocketを通じてユーザーにメッセージを送信
        message = {
                "action": "create",  # 追加: アクションの種類を指定
                "id": new_attendance.id, 
                "title": new_attendance.title, 
                "description": new_attendance.description, 
                "user_id": new_attendance.user_id, 
                "user_name": user.name, 
                "mail_send": new_attendance.mail_send, 
                "start": attendance_body.start.isoformat(), 
                "end": attendance_body.end.isoformat(), 
                "undecided": new_attendance.undecided,
        }
        await connection_attendance_manager.broadcast(message)
        return new_attendance
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.patch("/attendances/{id}", response_model=attendance_schema.AttendanceUpdateResponse)
async def update_attendance(
    id: int, 
    attendance_body: attendance_schema.AttendanceUpdate, 
    db: AsyncSession = Depends(get_db)
):
    attendance = await attendance_crud.get_attendance(db, id=id)
    if attendance is None:
        raise HTTPException(status_code=404, detail="Attendance not found")
    
    updated_attendance = await attendance_crud.update_attendance(db, attendance_body, original=attendance)

    message = {
                "action": "update",  # 追加: アクションの種類を指定
                "id": updated_attendance.id, 
                "title": updated_attendance.title,
                "description": updated_attendance.description, 
                "mail_send": updated_attendance.mail_send, 
                "start": attendance_body.start.isoformat(), 
                "end": attendance_body.end.isoformat(), 
                "undecided": updated_attendance.undecided,
    }
    await connection_attendance_manager.broadcast(message)
    return updated_attendance

@router.delete("/attendances/{id}", response_model=None)
async def delete_attendance(id: int, db: AsyncSession = Depends(get_db)):
    attendance = await attendance_crud.get_attendance(db, id=id)
    if attendance is None:
        raise HTTPException(status_code=404, detail="Attendance not found")
    
    await attendance_crud.delete_event(db, original=attendance)

    # 更新が成功した後、WebSocketを通じてユーザーにメッセージを送信
    message = {
        "action": "delete",  # 追加: アクションの種類を指定
        "id": id,
    }
    await connection_attendance_manager.broadcast(message)

    return {"detail": "Attendance deleted successfully"}