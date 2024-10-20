from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession

import api.cruds.chat as chat_crud
from api.db import get_db
from datetime import datetime
import json
import base64
import pytz

import api.schemas.chat as chat_schema
import api.schemas.user as user_schema

router = APIRouter()

# WebSocket接続を管理するクラス
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, chat_room_id: int):
        await websocket.accept()
        if chat_room_id not in self.active_connections:
            self.active_connections[chat_room_id] = []
        self.active_connections[chat_room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, chat_room_id: int):
        self.active_connections[chat_room_id].remove(websocket)
        if not self.active_connections[chat_room_id]:
            del self.active_connections[chat_room_id]
    
    async def broadcast(self, data: dict, chat_room_id: int):
        private_message = json.dumps(data) 
        for connection in self.active_connections.get(chat_room_id, []):
            await connection.send_text(private_message)

manager = ConnectionManager()

# WebSocket接続を管理するクラス
class GroupConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, group_chat_room_id: int):
        await websocket.accept()
        if group_chat_room_id not in self.active_connections:
            self.active_connections[group_chat_room_id] = []
        self.active_connections[group_chat_room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, group_chat_room_id: int):
        self.active_connections[group_chat_room_id].remove(websocket)
        if not self.active_connections[group_chat_room_id]:
            del self.active_connections[group_chat_room_id]
    
    async def broadcast(self, data: dict, group_chat_room_id: int):
        private_message = json.dumps(data) 
        for connection in self.active_connections.get(group_chat_room_id, []):
            await connection.send_text(private_message)

group_manager = GroupConnectionManager()

@router.websocket("/ws_private_message/{chat_room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, chat_room_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    await manager.connect(websocket, chat_room_id)
    try:
        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)  # テキストデータをJSONにパース

            # PrivateMessageCreateオブジェクトを作成
            new_message = {
                "user_id": user_id,
                "private_chat_room_id": chat_room_id,
                "content": data_json["content"],
                "sent_at": datetime.now(pytz.timezone('Asia/Tokyo')),
                "is_read": False,
                "image_data": base64.b64decode(data_json["image_data"]),
                "file_data": base64.b64decode(data_json["file_data"]),
                "file_name": data_json["file_name"]
            }
            new_message_body = chat_schema.PrivateMessageCreate(**new_message)
            await chat_crud.post_private_message(db, new_message_body)

            broadcast_message = json.dumps({
                "user_id": new_message_body.user_id,
                "content": new_message_body.content,
                "sent_at": new_message_body.sent_at.isoformat(),  # ISOフォーマットに変換
                "is_read": new_message_body.is_read,
                "image_data": base64.b64encode(new_message_body.image_data).decode("utf-8"),
                "file_data": base64.b64encode(new_message_body.file_data).decode("utf-8"),
                "file_name": new_message_body.file_name,
            })
            
            await manager.broadcast({"type": "broadcast", "message": broadcast_message}, chat_room_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_room_id)
    except Exception as e:
        await websocket.close(code=1001)  # エラー時に接続を閉じる
        print(f"Unexpected error: {e}")

@router.websocket("/ws_group_message/{group_chat_room_id}/{user_id}")
async def websocket_group_endpoint(websocket: WebSocket, group_chat_room_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    await group_manager.connect(websocket, group_chat_room_id)
    try:
        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)  # テキストデータをJSONにパース

            # GroupMessageCreateオブジェクトを作成
            new_message = {
                "user_id": user_id,
                "group_chat_room_id": group_chat_room_id,
                "content": data_json["content"],
                "sent_at": datetime.now(pytz.timezone('Asia/Tokyo')),
                "is_read": False,
                "image_data": base64.b64decode(data_json["image_data"]),
                "file_data": base64.b64decode(data_json["file_data"]),
                "file_name": data_json["file_name"]
            }
            new_message_body = chat_schema.GroupMessageCreate(**new_message)
            await chat_crud.post_group_message(db, new_message_body)

            broadcast_message = json.dumps({
                "user_id": new_message_body.user_id,
                "content": new_message_body.content,
                "sent_at": new_message_body.sent_at.isoformat(),  # ISOフォーマットに変換
                "is_read": new_message_body.is_read,
                "image_data": base64.b64encode(new_message_body.image_data).decode("utf-8"),
                "file_data": base64.b64encode(new_message_body.file_data).decode("utf-8"),
                "file_name": new_message_body.file_name,
            })
            
            await group_manager.broadcast({"type": "broadcast", "message": broadcast_message}, group_chat_room_id)

    except WebSocketDisconnect:
        group_manager.disconnect(websocket, group_chat_room_id)

@router.get("/private_chat_room/{user1_id}/{user2_id}", response_model=chat_schema.PrivateChatRoom)
async def get_private_chat_room(user1_id: int, user2_id: int, db: AsyncSession = Depends(get_db)):
    private_chat_room = await chat_crud.get_or_create_private_chat_room(db, user1_id, user2_id) 
    return private_chat_room

@router.get("/private_messages/{private_chat_room_id}", response_model=list[chat_schema.PrivateMessage])
async def get_chat_messages(private_chat_room_id: int, db: AsyncSession = Depends(get_db)):
    return await chat_crud.get_private_messages(db, private_chat_room_id)

@router.get("/get_entry_group_chat_room/{user_id}", response_model=list[chat_schema.GroupChatRoom])
async def get_join_chat_room(user_id: int, db: AsyncSession = Depends(get_db)):
    return await chat_crud.get_entry_group_chat_room(db,user_id)

@router.get("/get_not_entry_group_chat_room/{user_id}", response_model=list[chat_schema.GroupChatRoom])
async def get_not_join_chat_room(user_id: int, db: AsyncSession = Depends(get_db)):
    return await chat_crud.get_not_entry_group_chat_room(db, user_id)

@router.post("/group_chat_room", response_model=chat_schema.GroupChatRoomCreateResponse)
async def create_group_chat(
    file: UploadFile = File(...),
    name: str = Form(...),
    created_at: datetime = Form(...),
    member_ids: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # カンマ区切りの文字列をリストに変換
    member_ids_list = [int(id) for id in member_ids.split(',')]
    file_contents = await file.read()
    image_data = base64.b64encode(file_contents).decode("utf-8")
    # group_chat_createオブジェクトを作成
    group_create_data = {
        "name": name,
        "created_at": created_at,
        "image": image_data,
    }
    group_chat_create = chat_schema.GroupChatRoomCreate(**group_create_data)
    return await chat_crud.create_group_chat(db, group_chat_create, member_ids_list)

@router.get("/group_chat_room_users/{group_chat_room_id}", response_model=list[user_schema.UserInGroupChat])
async def get_group_chat_room_users(group_chat_room_id: int, db: AsyncSession = Depends(get_db)):
    rows = await chat_crud.get_users_in_group_chat_room(db, group_chat_room_id)
    if not rows:
        raise HTTPException(status_code=404, detail="Group chat room not found or empty")
    
    users_in_group : list[user_schema.UserInGroupChat] = []
    for row in rows:
        user: user_schema.User = row[0]
        group_chat_user: chat_schema.GroupChatRoomUser = row[1]
        user_data = user_schema.UserInGroupChat(
            id=user.id,
            email=user.email,
            grade=user.grade,
            group=user.group,
            name=user.name,
            status=user.status,
            firebase_user_id=user.firebase_user_id,
            file_name=user.file_name,
            bytes_data=user.bytes_data,
            joined_date=group_chat_user.joined_date,
            leave_date=group_chat_user.leave_date,
            join=group_chat_user.join,
        )
        users_in_group.append(user_data)
    return users_in_group

@router.get("/group_messages/{group_chat_room_id}", response_model=list[chat_schema.GroupMessage])
async def get_group_chat_messages(group_chat_room_id: int, db: AsyncSession = Depends(get_db)):
    return await chat_crud.get_group_messages(db, group_chat_room_id)

@router.patch("/group_member_update/{group_chat_room_id}/{user_id}", response_model=None)
async def update_group_chat_member(group_chat_room_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    # メンバーを削除するためのCRUDメソッドを呼び出す
    success = await chat_crud.update_group_chat_member(db, group_chat_room_id,user_id)
    if success is None:
        raise HTTPException(status_code=404, detail="メンバーが見つかりません")
    
    return {"message": "メンバーが削除されました"}

@router.post("/add_members/{group_chat_room_id}", response_model=None)
async def add_group_chat_member(
    group_chat_room_id: int, 
    members: chat_schema.GroupMemberIds,
    db: AsyncSession = Depends(get_db)
    ):
    return await chat_crud.add_or_update_user_in_group_chat(db, group_chat_room_id, members.member_ids)

@router.get("/get_users_not_in_group/{group_chat_room_id}", response_model=list[user_schema.User])
async def get_users_not_in_group(group_chat_room_id: int, db: AsyncSession = Depends(get_db)):
    return await chat_crud.get_users_not_in_group_chat(db, group_chat_room_id)

@router.get("/get_group_chat_rooms", response_model=list[chat_schema.GroupChatRoom])
async def get_group_chat_rooms(db: AsyncSession = Depends(get_db)):
    return await chat_crud.get_group_chat_rooms(db)

@router.delete("/delete_group_chat_room/{group_chat_room_id}", response_model=None)
async def delete_group_chat_room(group_chat_room_id: int, db: AsyncSession = Depends(get_db)):
    return await chat_crud.delete_group_chat_room_others(db, group_chat_room_id)