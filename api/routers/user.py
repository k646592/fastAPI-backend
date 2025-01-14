from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
import json 

from minio import Minio

import api.cruds.user as user_crud
from api.db import get_db

import api.schemas.user as user_schema
import api.routers.attendance as attendance_router

# MinIO client configuration
MINIO_URL = "minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "user-images"
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

# idは、firebase_user_idでstr

class ConnectionManager:
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
connection_manager = ConnectionManager()

@router.websocket("/ws_user_location")
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

# 一覧取得のエンドポインt
@router.get("/users", response_model=list[user_schema.User])
async def list_users(db: AsyncSession = Depends(get_db)):
    return await user_crud.get_users(db)

# firebase_user_idのuserを取得するエンドポイント
@router.get("/users/{id}", response_model=user_schema.UserGet)
async def get_user(
    id: str, 
    db: AsyncSession = Depends(get_db)
):
    return await user_crud.get_user(db=db, id=id)

# 新規登録のエンドポイント
@router.post("/users", response_model=user_schema.UserCreateResponse)
async def create_user(
    firebase_user_id: str = Form(...),
    email: str = Form(...),
    grade: str = Form(...),
    group: str = Form(...),
    name: str = Form(...),
    status: str = Form(...),
    now_location: str = Form(...),
    location_flag: bool = Form(...),
    image: UploadFile = None,
    db: AsyncSession = Depends(get_db),
):
    

    # Upload image to MinIO if provided
    if image:
        image_name = f"{firebase_user_id}/{image.filename}"
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
    user_create_data = {
       "id": firebase_user_id,
       "email": email,
       "grade": grade,
       "group": group,
       "name": name,
       "status": status,
       "now_location": now_location,
       "location_flag": location_flag,
       "image_name": image_name,
       "image_url": image_url,
   }
    
    
    return await user_crud.create_user(db, user_create_data=user_create_data)

# ユーザ情報（image以外）のエンドポイント
@router.patch("/users/{id}", response_model=user_schema.UserUpdateResponse)
async def update_user(
    id: str, 
    user_body: user_schema.UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = await user_crud.get_user(db, id=id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return await user_crud.update_user(db, user_body, original=user)

@router.patch("/users/image/{user_id}", response_model=user_schema.UserUpdateImageResponse)
async def update_user_image(
    user_id: str,
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    user = await user_crud.get_user(db, id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Upload image to MinIO if provided
    if image:
        image_name = f"{user_id}/{image.filename}"
        minio_client.put_object(
            MINIO_BUCKET,
            image_name,
            image.file,
            length=-1,  # Calculate automatically
            part_size=10 * 1024 * 1024,  # 10 MB
            content_type=image.content_type,
        )
        image_url = f"http://localhost:9000/{MINIO_BUCKET}/{image_name}"
        
        if user.image_url == "" or user.image_name == "" :
            try:
                # MinIOから画像を削除
                await delete_user_image(image_name=user.image_name)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")
    else:
        image_name = ""
        image_url = ""

    # Create the user instance
    user_update_data = {
       "image_name": image_name,
       "image_url": image_url,
   }
    
    user_body = user_schema.UserUpdateImage(**user_update_data)
    return await user_crud.update_user_image(db, user_body, original=user)

@router.patch("/update_user_location/{firebase_user_id}", response_model=user_schema.UserUpdateLocationResponse)
async def update_user_location(
    firebase_user_id: str,
    user_body: user_schema.UserUpdateLocation,
    db: AsyncSession = Depends(get_db),
):
    user = await user_crud.get_user(db, id=firebase_user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    status = "未出席"

    if user.location_flag == True :
        if user.status == "授業中" :
            update_user_location = await user_crud.update_user_location(db, user_body, original=user)
            status = "授業中"
        else :
            if user_body.now_location == "研究室内" or user_body.now_location == "第２研究室内" or user_body.now_location == "榎原先生の自室":
                update_user_location = await user_crud.update_user_location_status(db, user_body, original=user, status="出席")
                message_status = {"user_id": user.id, "status": update_user_location.status}
                status = update_user_location.status
                await attendance_router.connection_manager.broadcast(message_status)
            elif user_body.now_location == "キャンパス外" :
                update_user_location = await user_crud.update_user_location_status(db, user_body, original=user, status="帰宅")
                message_status = {"user_id": user.id, "status": update_user_location.status}
                status = update_user_location.status
                await attendance_router.connection_manager.broadcast(message_status)
            else :
                update_user_location = await user_crud.update_user_location_status(db, user_body, original=user, status="一時退席")
                message_status = {"user_id": user.id, "status": update_user_location.status}
                status = update_user_location.status
                await attendance_router.connection_manager.broadcast(message_status)
    else :
        if user_body.now_location == "研究室内" or user_body.now_location == "榎原先生の自室":
            update_user_location = await user_crud.update_user_location_status_flag(db, user_body, original=user)
            message_status = {"user_id": user.id, "status": update_user_location.status}
            status = update_user_location.status
            await attendance_router.connection_manager.broadcast(message_status)
        else :
            if user.status == "授業中" :
                status = "授業中"
            update_user_location = await user_crud.update_user_location(db, user_body, original=user)
    # 更新が成功した後、WebSocketを通じてユーザーにメッセージを送信
    message = {"user_id": user.id, "now_location": update_user_location.now_location, "status": status}
    await connection_manager.broadcast(message)
    return update_user_location

@router.get("/get_user_name/{id}", response_model=user_schema.UserGetName)
async def get_user_name(
    id:str, db: AsyncSession = Depends(get_db)
):
    return await user_crud.get_user_name(db, id=id)

@router.patch("/users/email/{user_id}", response_model=user_schema.UserUpdateEmailResponse)
async def update_user_email(
    user_id: str, 
    user_body: user_schema.UserUpdateEmail,
    db: AsyncSession = Depends(get_db),
):
    user = await user_crud.get_user(db, id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return await user_crud.update_user_email(db, user_body, original=user)    

@router.delete("/users/{user_id}", response_model=None)
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await user_crud.get_user(db, id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return await user_crud.delete_user(db, original=user)


# 画像削除用の関数
async def delete_user_image(image_name: str):
    try:
        # MinIOから画像を削除
        minio_client.remove_object(MINIO_BUCKET, f"{image_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")