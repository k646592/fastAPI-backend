from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
import base64
import json 

import api.cruds.user as user_crud
from api.db import get_db

import api.schemas.user as user_schema

router = APIRouter()

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

@router.get("/users", response_model=list[user_schema.User])
async def list_users(db: AsyncSession = Depends(get_db)):
    return await user_crud.get_users(db)

@router.get("/chat_users/{firebase_user_id}", response_model=list[user_schema.User])
async def list_chat_users(firebase_user_id: str, db: AsyncSession = Depends(get_db)):
    return await user_crud.get_chat_users(db, firebase_user_id)

@router.post("/users", response_model=user_schema.UserCreateResponse)
async def create_user(
    file: UploadFile = File(...),
    email: str = Form(...),
    grade: str = Form(...),
    group: str = Form(...),
    name: str = Form(...),
    status: str = Form(...),
    firebase_user_id: str = Form(...),
    now_location: str = Form(...),
    location_flag: bool = Form(...),
    db: AsyncSession = Depends(get_db),
):
   file_contents = await file.read()  # ファイルの内容を読み取る
   image_data = base64.b64encode(file_contents).decode("utf-8")
   # UserCreateオブジェクトを作成
   user_create_data = {
       "email": email,
       "grade": grade,
       "group": group,
       "name": name,
       "status": status,
       "firebase_user_id": firebase_user_id,
       "file_name": file.filename,
       "bytes_data": image_data,
       "now_location": now_location,
       "location_flag": location_flag,
   }
   user_body = user_schema.UserCreate(**user_create_data)
   return await user_crud.create_user(db, user_body)

@router.get("/get_user_name/{id}", response_model=user_schema.UserGetName)
async def get_user_name(
    id:int, db: AsyncSession = Depends(get_db)
):
    return await user_crud.get_user_name(db, id=id)

@router.get("/users/{firebase_user_id}", response_model=user_schema.UserGet)
async def read_user(
    firebase_user_id: str, db: AsyncSession = Depends(get_db)
):
    return await user_crud.get_firebase_user(db, firebase_user_id=firebase_user_id)

@router.get("/user_id/{firebase_user_id}", response_model=user_schema.UserGetId)
async def read_user_id(
    firebase_user_id: str, db: AsyncSession = Depends(get_db)
):
    return await user_crud.get_firebase_user(db, firebase_user_id=firebase_user_id)

@router.get("/user_name_id/{firebase_user_id}", response_model=user_schema.UserGetNameId)
async def read_user_name_id(
    firebase_user_id: str, db: AsyncSession = Depends(get_db)
):
    return await user_crud.get_firebase_user_name_id(db, firebase_user_id=firebase_user_id)

@router.patch("/users/{id}", response_model=user_schema.UserUpdateResponse)
async def update_user(
    id: int, 
    user_body: user_schema.UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = await user_crud.get_user(db, id=id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return await user_crud.update_user(db, user_body, original=user)

@router.patch("/users/image/{user_id}", response_model=user_schema.UserUpdateImageResponse)
async def update_user_image(
    user_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    user = await user_crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    file_contents = await file.read()  # ファイルの内容を読み取る
    image_data = base64.b64encode(file_contents).decode("utf-8")
    # UserUpdateオブジェクトを作成
    user_update_data = {
       "file_name": file.filename,
       "bytes_data": image_data,
    }
    user_body = user_schema.UserUpdateImage(**user_update_data)
    return await user_crud.update_user_image(db, user_body, original=user)

@router.patch("/users/email/{user_id}", response_model=user_schema.UserUpdateEmailResponse)
async def update_user_email(
    user_id: int, 
    user_body: user_schema.UserUpdateEmail,
    db: AsyncSession = Depends(get_db),
):
    user = await user_crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return await user_crud.update_user_email(db, user_body, original=user)

@router.patch("/update_user_location/{firebase_user_id}", response_model=user_schema.UserUpdateLocationResponse)
async def update_user_location(
    firebase_user_id: str,
    user_body: user_schema.UserUpdateLocation,
    db: AsyncSession = Depends(get_db),
):
    user = await user_crud.get_firebase_user(db, firebase_user_id=firebase_user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.now_location == user_body.now_location:
        return JSONResponse(content={"message": "Status send successfully"})
    else:
        if user.location_flag == True :
            if user_body.now_location == "研究室内" :
                update_user_location = await user_crud.update_user_location_status(db, user_body, original=user, status="出席")
            elif user_body.now_location == "キャンパス外" :
                update_user_location = await user_crud.update_user_location_status(db, user_body, original=user, status="帰宅")
            else :
                update_user_location = await user_crud.update_user_location_status(db, user_body, original=user, status="一時退席")
        else :
            if user_body.now_location == "研究室内" :
                update_user_location = await user_crud.update_user_location_status_flag(db, user_body, original=user)
            else :
                update_user_location = await user_crud.update_user_location(db, user_body, original=user)
        # 更新が成功した後、WebSocketを通じてユーザーにメッセージを送信
        message = {"user_id": user.id, "now_location": update_user_location.now_location}
        await connection_manager.broadcast(message)
        return update_user_location

@router.delete("/users/{user_id}", response_model=None)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await user_crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return await user_crud.delete_user(db, original=user)