from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, File, UploadFile, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

import api.cruds.private_chat as chat_crud
from api.db import get_db
from datetime import datetime
import json
from minio import Minio

import api.schemas.private_chat as chat_schema
import api.schemas.user as user_schema

import api.routers.chat as total_chat

# MinIO client configuration
MINIO_URL = "minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "private-messages"
minio_client = Minio(
    MINIO_URL,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,
)

# Ensure the bucket exists
if not minio_client.bucket_exists(MINIO_BUCKET):
    minio_client.make_bucket(MINIO_BUCKET)


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
        websocket.close()
        self.active_connections[chat_room_id].remove(websocket)
        if not self.active_connections[chat_room_id]:
            del self.active_connections[chat_room_id]
    
    async def broadcast(self, data: dict, chat_room_id: int):
        private_message = json.dumps(data) 
        for connection in self.active_connections.get(chat_room_id, []):
            await connection.send_text(private_message)

# WebSocket接続を管理するクラス
class ConnectionChatUserManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        websocket.close()
        self.active_connections[user_id].remove(websocket)
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]
    
    async def broadcast(self, data: dict, user_id: str):
        private_message = json.dumps(data) 
        for connection in self.active_connections.get(user_id, []):
            await connection.send_text(private_message)

manager = ConnectionManager()

chat_user_manager = ConnectionChatUserManager()

@router.websocket("/ws_private_message/{chat_room_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    chat_room_id: int, 
):
    await manager.connect(websocket, chat_room_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)  # テキストデータをJSONにパース
            await manager.broadcast({"type": "broadcast", "message": message}, chat_room_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_room_id)
    except json.JSONDecodeError:
        print("Invalid JSON format")
    except Exception as e:
        await websocket.close(code=1001)  # エラー時に接続を閉じる
        print(f"Unexpected error: {e}")

@router.websocket("/ws_private_userlist/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: str, 
):
    await chat_user_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)  # テキストデータをJSONにパース
            await chat_user_manager.broadcast({"type": "broadcast", "message": message}, user_id)

    except WebSocketDisconnect:
        chat_user_manager.disconnect(websocket, user_id)
    except json.JSONDecodeError:
        print("Invalid JSON format")
    except Exception as e:
        await websocket.close(code=1001)  # エラー時に接続を閉じる
        print(f"Unexpected error: {e}")


@router.get("/get_private_unread_count/{user_id}", response_model=int)
async def get_private_unread_count(user_id: str, db: AsyncSession = Depends(get_db)):
    chat_room_ids = await chat_crud.get_private_chat_room_ids(db=db, user_id=user_id)
    if not chat_room_ids:
        return 0  # チャットルームが存在しない場合は未読メッセージ数は0
    # 未読メッセージ数を取得
    unread_count = await chat_crud.get_unread_message_count(db=db, user_id=user_id, chat_room_ids=chat_room_ids)
    return unread_count

@router.get("/chat_users/{id}", response_model=list[chat_schema.PrivateChatUser])
async def list_chat_users(id: str, db: AsyncSession = Depends(get_db)):
    chat_room_ids = await chat_crud.get_private_chat_room_ids(db=db, user_id=id)
    private_chat_infos = await chat_crud.get_private_chat_users_with_updated_at(db=db,chat_room_ids=chat_room_ids,user_id=id)
    private_chat_users = await chat_crud.get_private_chat_users_with_details(db=db,chat_room_infos=private_chat_infos)
    private_chat_non_users = await chat_crud.get_users_not_in_chat_room_infos(db=db,chat_room_infos=private_chat_infos, user_id=id)
    return private_chat_users + private_chat_non_users

@router.get("/private_chat_room/{user1_id}/{user2_id}", response_model=chat_schema.PrivateChatRoom)
async def get_private_chat_room(user1_id: str, user2_id: str, db: AsyncSession = Depends(get_db)):
    private_chat_room = await chat_crud.get_or_create_private_chat_room(db, user1_id, user2_id) 
    return private_chat_room

@router.patch("/private_message_unread_update/{private_chat_room_id}/{user_id}", response_model=list[chat_schema.PrivateMessageUnreadUpdate])
async def private_message_unread_update(private_chat_room_id: int, user_id: str, db: AsyncSession = Depends(get_db)):
    update_unread_messages = await chat_crud.unread_private_messages_update(db=db,private_chat_room_id=private_chat_room_id,user_id=user_id)
    # 更新が成功した後、WebSocketを通じてユーザーにメッセージを送信
    # 更新内容を JSON に変換してブロードキャスト
    message = {
        "type": "unread_update",
        "message": [message.dict() for message in update_unread_messages]
    }
    await manager.broadcast(message, private_chat_room_id)
    return update_unread_messages

@router.post("/message_unread_update_websocket/{private_chat_room_id}/{private_message_id}", response_model=chat_schema.PrivateMessageUnreadUpdate)
async def message_unread_update_websocket(
    private_chat_room_id: int,
    private_message_id: int,
    db: AsyncSession = Depends(get_db)):
    private_message_unread = await chat_crud.message_unread_update_websocket(db=db, private_message_id=private_message_id)
    # 更新が成功した後、WebSocketを通じてユーザーにメッセージを送信
    message = {
        "id": private_message_unread.id, 
        "is_read": private_message_unread.is_read,
    }
    await manager.broadcast({"type": "message_unread_websocket", "message": message}, private_chat_room_id)
    return private_message_unread

@router.get("/private_messages/{private_chat_room_id}", response_model=list[chat_schema.PrivateMessage])
async def get_chat_messages(
    private_chat_room_id: int, 
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db)):
    return await chat_crud.get_private_messages(db, private_chat_room_id, page=page)

@router.post("/private_messages/{private_chat_room_id}", response_model=chat_schema.PrivateMessageCreateResponse)
async def create_private_message(
    private_chat_room_id: int,
    user_id: str = Form(...),
    message_type: str = Form(...),
    sent_at: datetime = Form(...),
    is_read: bool = Form(...),
    content: str = Form(...),
    file: UploadFile = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Create the message instance
        if message_type == 'text' :
            message_create_data = chat_schema.PrivateMessageCreate(
                private_chat_room_id=private_chat_room_id,
                user_id=user_id,
                message_type=message_type,
                sent_at=sent_at,
                is_read=is_read,
                content=content,
                image_name='',
                image_url='',
                file_name='',
                file_url='',
            )
        elif message_type == 'image' :
            # Upload image to MinIO if provided
            if file:
                image_name = f"{private_chat_room_id}/{message_type}/{file.filename}"
                minio_client.put_object(
                    MINIO_BUCKET,
                    image_name,
                    file.file,
                    length=-1,  # Calculate automatically
                    part_size=10 * 1024 * 1024,  # 10 MB
                    content_type=file.content_type,
                )
                image_url = f"http://localhost:9000/{MINIO_BUCKET}/{image_name}"
            else:
                image_name = ""
                image_url = ""

            message_create_data = chat_schema.PrivateMessageCreate(
                private_chat_room_id=private_chat_room_id,
                user_id=user_id,
                message_type=message_type,
                sent_at=sent_at,
                is_read=is_read,
                content='',
                image_name=image_name,
                image_url=image_url,
                file_name='',
                file_url='',
            )

        elif message_type == 'file' :
            # Upload image to MinIO if provided
            if file:
                file_name = f"{private_chat_room_id}/{message_type}/{file.filename}"
                minio_client.put_object(
                    MINIO_BUCKET,
                    file_name,
                    file.file,
                    length=-1,  # Calculate automatically
                    part_size=10 * 1024 * 1024,  # 10 MB
                    content_type=file.content_type,
                )
                file_url = f"http://localhost:9000/{MINIO_BUCKET}/{file_name}"
            else:
                file_name = ""
                file_url = ""
            
            message_create_data = chat_schema.PrivateMessageCreate(
                private_chat_room_id=private_chat_room_id,
                user_id=user_id,
                message_type=message_type,
                sent_at=sent_at,
                is_read=is_read,
                content='',
                image_name='',
                image_url='',
                file_name=file_name,
                file_url=file_url,
            )

        new_message = await chat_crud.post_private_message(db, message_create_data)

        # 更新が成功した後、WebSocketを通じてユーザーにメッセージを送信
        message = json.dumps({
                "id": new_message.id, 
                "private_chat_room_id": new_message.private_chat_room_id,
                "user_id": new_message.user_id,
                "message_type": new_message.message_type,
                "sent_at": message_create_data.sent_at.isoformat(),
                "is_read": new_message.is_read,
                "content": new_message.content,
                "image_name": new_message.image_name,
                "image_url": new_message.image_url,
                "file_name": new_message.file_name,
                "file_url": new_message.file_url,
        })
        await manager.broadcast({"type": "broadcast", "message": message}, private_chat_room_id)

        other_user_id = await chat_crud.get_other_user_id(private_chat_room_id=private_chat_room_id,user_id=user_id,db=db)

        user_message = {
            "updated_at": message_create_data.sent_at.isoformat(),
            "user_id": new_message.user_id,
        }
        await chat_user_manager.broadcast({"type": "broadcast", "message": user_message}, other_user_id)
        await total_chat.chat_user_total_manager.broadcast({"type": "broadcast", "message": user_message}, other_user_id)

        return new_message
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    
@router.patch("/update_datetime_private_chat_room/{private_chat_room_id}", response_model=chat_schema.PrivateChatRoomUpdateResponse)
async def update_datetime_private_chat_room(
    private_chat_room_id: int, 
    update_private_chat_room: chat_schema.PrivateChatRoomUpdate, 
    db: AsyncSession = Depends(get_db)
):
    private_chat_room = await chat_crud.get_private_chat_room(db, id=private_chat_room_id)
    if private_chat_room is None:
        raise HTTPException(status_code=404, detail="PrivateChatRoom not found")
        
    return await chat_crud.update_private_chat_room(db=db, update_private_chat_room=update_private_chat_room, original=private_chat_room)



