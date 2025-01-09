from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, File, UploadFile, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from api.db import get_db
from datetime import datetime
import json
from minio import Minio

import api.cruds.group_chat as chat_crud

import api.schemas.group_chat as chat_schema
import api.schemas.user as user_schema

import api.routers.chat as total_chat

# MinIO client configuration
MINIO_URL = "minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "group-chat"
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
class GroupConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, group_chat_room_id: int):
        await websocket.accept()
        if group_chat_room_id not in self.active_connections:
            self.active_connections[group_chat_room_id] = []
        self.active_connections[group_chat_room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, group_chat_room_id: int):
        websocket.close()
        self.active_connections[group_chat_room_id].remove(websocket)
        if not self.active_connections[group_chat_room_id]:
            del self.active_connections[group_chat_room_id]
    
    async def broadcast(self, data: dict, group_chat_room_id: int):
        private_message = json.dumps(data) 
        for connection in self.active_connections.get(group_chat_room_id, []):
            await connection.send_text(private_message)

group_manager = GroupConnectionManager()

# WebSocket接続を管理するクラス
class ConnectionGroupChatUserManager:
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

chat_user_manager = ConnectionGroupChatUserManager()

@router.websocket("/ws_group_message/{group_chat_room_id}/{user_id}")
async def websocket_group_endpoint(websocket: WebSocket, group_chat_room_id: int, user_id: str, db: AsyncSession = Depends(get_db)):
    await group_manager.connect(websocket, group_chat_room_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)  # テキストデータをJSONにパース
            await group_manager.broadcast({"type": "broadcast", "message": message}, group_chat_room_id)

    except WebSocketDisconnect:
        group_manager.disconnect(websocket, group_chat_room_id)
    except json.JSONDecodeError:
        print("Invalid JSON format")
    except Exception as e:
        await websocket.close(code=1001)  # エラー時に接続を閉じる
        print(f"Unexpected error: {e}")

@router.websocket("/ws_group_chat_list/{user_id}")
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

@router.get("/get_create_chat_users/{user_id}", response_model=list[chat_schema.GetChatMemberCreateBase])
async def get_cteate_chat_users(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    return await chat_crud.get_create_chat_users(db=db,user_id=user_id)

@router.post("/group_chat_room", response_model=chat_schema.GroupChatRoomCreateResponse)
async def create_group_chat(
    image: UploadFile = None,
    name: str = Form(...),
    created_at: datetime = Form(...),
    member_ids: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # カンマ区切りの文字列をリストに変換
    member_ids_list = [str(id) for id in member_ids.split(',')]
    
    # Upload image to MinIO if provided
    if image:
        image_name = f"room/{name}/{image.filename}"
        minio_client.put_object(
            MINIO_BUCKET,
            image_name,
            image.file,
            length=-1,  # Calculate automatically
            part_size=10 * 1024 * 1024,  # 10 MB
            content_type=image.content_type,
        )
        image_url = f"http://localhost:9000/{MINIO_BUCKET}/{image_name}"
    else:
        image_name = ""
        image_url = ""

    # Create the user instance
    group_create_data = {
       "name": name,
       "image_name": image_name,
       "image_url": image_url,
       "created_at": created_at,
       "updated_at": created_at,
   }
    
    group_chat_create = chat_schema.GroupChatRoomCreate(**group_create_data)
    return await chat_crud.create_group_chat(db, group_chat_create, member_ids_list)

@router.get("/get_entry_group_chat_room/{user_id}", response_model=list[chat_schema.GroupChatRoom])
async def get_join_chat_room(user_id: str, db: AsyncSession = Depends(get_db)):
    return await chat_crud.get_entry_group_chat_room(db,user_id)

@router.get("/get_not_entry_group_chat_room/{user_id}", response_model=list[chat_schema.GroupChatRoom])
async def get_not_join_chat_room(user_id: str, db: AsyncSession = Depends(get_db)):
    return await chat_crud.get_not_entry_group_chat_room(db, user_id)

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
            image_url=user.image_url,
            image_name=user.image_name,
            joined_date=group_chat_user.joined_date,
            leave_date=group_chat_user.leave_date,
            join=group_chat_user.join,
        )
        users_in_group.append(user_data)
    return users_in_group

@router.patch("/group_member_update/{group_chat_room_id}/{user_id}", response_model=None)
async def update_group_chat_member(group_chat_room_id: int, user_id: str, db: AsyncSession = Depends(get_db)):
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

@router.delete("/delete_group_chat_room/{group_chat_room_id}", response_model=None)
async def delete_group_chat_room(group_chat_room_id: int, db: AsyncSession = Depends(get_db)):
    return await chat_crud.delete_group_chat_room_others(db, group_chat_room_id)

@router.post("/group_messages/{group_chat_room_id}", response_model=chat_schema.GroupMessageCreateResponse)
async def create_private_message(
    group_chat_room_id: int,
    user_id: str = Form(...),
    message_type: str = Form(...),
    sent_at: datetime = Form(...),
    content: str = Form(...),
    file: UploadFile = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Create the message instance
        if message_type == 'text' :
            message_create_data = chat_schema.GroupMessageCreate(
                group_chat_room_id=group_chat_room_id,
                user_id=user_id,
                message_type=message_type,
                sent_at=sent_at,
                content=content,
                image_name='',
                image_url='',
                file_name='',
                file_url='',
            )
        elif message_type == 'image' :
            # Upload image to MinIO if provided
            if file:
                image_name = f"messages/{group_chat_room_id}/{message_type}/{file.filename}"
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

            message_create_data = chat_schema.GroupMessageCreate(
                group_chat_room_id=group_chat_room_id,
                user_id=user_id,
                message_type=message_type,
                sent_at=sent_at,
                content='',
                image_name=image_name,
                image_url=image_url,
                file_name='',
                file_url='',
            )

        elif message_type == 'file' :
            # Upload image to MinIO if provided
            if file:
                file_name = f"messages/{group_chat_room_id}/{message_type}/{file.filename}"
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
            
            message_create_data = chat_schema.GroupMessageCreate(
                group_chat_room_id=group_chat_room_id,
                user_id=user_id,
                message_type=message_type,
                sent_at=sent_at,
                content='',
                image_name='',
                image_url='',
                file_name=file_name,
                file_url=file_url,
            )

        new_message = await chat_crud.post_group_message(db, message_create_data)

        other_user_ids = await chat_crud.get_users_in_group_chat_room_excluding_user(db=db,group_chat_room_id=group_chat_room_id,exclude_user_id=user_id)

        user_message = {
            "updated_at": message_create_data.sent_at.isoformat(),
            "group_chat_room_id": new_message.group_chat_room_id,
        }
        for user_id in other_user_ids :
            await chat_user_manager.broadcast({"type": "broadcast", "message": user_message}, user_id)
            await total_chat.chat_user_total_manager.broadcast({"type": "broadcast", "message": user_message}, user_id)
        
        return new_message
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    
@router.post("/websocket_messages", )
async def websocket_messages(
    new_message: chat_schema.GroupChatMessage,
    db: AsyncSession = Depends(get_db)
):
    users_count = await chat_crud.get_group_chat_users_count(db, new_message.group_chat_room_id)
        
    # 更新が成功した後、WebSocketを通じてユーザーにメッセージを送信
    message = json.dumps({
                "id": new_message.id, 
                "group_chat_room_id": new_message.group_chat_room_id,
                "user_id": new_message.user_id,
                "message_type": new_message.message_type,
                "sent_at": new_message.sent_at.isoformat(),
                "content": new_message.content,
                "image_name": new_message.image_name,
                "image_url": new_message.image_url,
                "file_name": new_message.file_name,
                "file_url": new_message.file_url,
                "unread_count": users_count-1,
    })
    await group_manager.broadcast({"type": "broadcast", "message": message}, new_message.group_chat_room_id)
        

@router.post("/create_unread_messages", )
async def create_unread_messages(
    create_unread: chat_schema.UnreadMessageBase,
    db: AsyncSession = Depends(get_db)
):
    try:
        user_ids = await chat_crud.get_users_in_group_chat_room_excluding_user(
            db=db,
            group_chat_room_id=create_unread.group_chat_room_id,
            exclude_user_id=create_unread.user_id
        )
        if not user_ids:
            raise HTTPException(status_code=422, detail="No users found in the group chat room")
        
        await chat_crud.create_unread_messages(
            db=db, 
            user_ids=user_ids, 
            group_chat_room_id=create_unread.group_chat_room_id,
            group_message_id=create_unread.group_message_id
        )
        update_group_chat = chat_schema.UpdateGroupChatRoomTime(
               id=create_unread.group_chat_room_id,
               updated_at=create_unread.updated_at,
        )
        group_chat_room = await chat_crud.get_group_chat_room(db=db,group_chat_room_id=create_unread.group_chat_room_id)
        await chat_crud.update_time_group_chat_room(db=db,update_private_chat_room=update_group_chat,original=group_chat_room)

        return {"status": "success"}
    
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/group_messages/{group_chat_room_id}", response_model=list[chat_schema.GroupMessage])
async def get_group_chat_messages(
    group_chat_room_id: int, 
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db)
):
    return await chat_crud.get_group_messages(db, group_chat_room_id, page=page)

@router.get("/get_users_not_in_group/{group_chat_room_id}", response_model=list[user_schema.User])
async def get_users_not_in_group(group_chat_room_id: int, db: AsyncSession = Depends(get_db)):
    return await chat_crud.get_users_not_in_group_chat(db, group_chat_room_id)

@router.get("/get_group_chat_rooms", response_model=list[chat_schema.GetGroupChatRoom])
async def get_group_chat_rooms(db: AsyncSession = Depends(get_db)):
    return await chat_crud.get_group_chat_rooms(db)

@router.get("/get_group_chat_room_user/{group_chat_room_id}/{user_id}", response_model=chat_schema.GroupChatRoomUserData)
async def get_group_chat_room_user(
    group_chat_room_id: int,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    group_chat_user = await chat_crud.get_group_chat_room_user(db=db,group_chat_room_id=group_chat_room_id,user_id=user_id)
    user = await chat_crud.get_user(db=db, id=user_id)
    return chat_schema.GroupChatRoomUserData(
        id=user_id,
        email=user.email,
        group=user.group,
        grade=user.grade,
        name=user.name,
        status=user.status,
        image_url=user.image_url,
        image_name=user.image_name,
        joinded_date=group_chat_user.joined_date,
        leave_date=group_chat_user.leave_date,
        join=group_chat_user.join
    )

@router.patch("/group_message_unread_update/{group_chat_room_id}/{user_id}", response_model=None)
async def group_message_unread_update(
    group_chat_room_id: int, user_id: str, db: AsyncSession = Depends(get_db)):
    update_unread_messages = await chat_crud.unread_group_messages_update(db=db,group_chat_room_id=group_chat_room_id,user_id=user_id)
    # 更新が成功した後、WebSocketを通じてユーザーにメッセージを送信
    # 更新内容を JSON に変換してブロードキャスト
    message = {
        "type": "unread_update",
        "message": [message.dict() for message in update_unread_messages]
    }
    await group_manager.broadcast(message, group_chat_room_id)
    return None

@router.post("/group_message_unread_update_websocket/{group_chat_room_id}/{group_message_id}/{user_id}", response_model=None)
async def message_unread_update_websocket(
    group_chat_room_id: int,
    group_message_id: int,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    await chat_crud.message_unread_update_websocket(db=db, group_chat_room_id=group_chat_room_id,user_id=user_id,group_message_id=group_message_id)
    # 更新が成功した後、WebSocketを通じてユーザーにメッセージを送信
    message = {
        "id": group_message_id, 
    }
    await group_manager.broadcast({"type": "message_unread_websocket", "message": message}, group_chat_room_id)
    return None

@router.get("/get_group_unread_count/{user_id}", response_model=int)
async def get_group_unread_count(user_id: str, db: AsyncSession = Depends(get_db)):
    chat_room_ids = await chat_crud.get_group_chat_room_ids(db=db, user_id=user_id)
    if not chat_room_ids:
        return 0  # チャットルームが存在しない場合は未読メッセージ数は0
    # 未読メッセージ数を取得
    unread_count = await chat_crud.get_unread_message_count(db=db, user_id=user_id, chat_room_ids=chat_room_ids)
    return unread_count