from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import json

import api.cruds.board as board_crud
from api.db import get_db

import api.schemas.board as board_schema

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

class ConnectionBoardManager(BaseConnectionManager):
    pass

class ConnectionAcknowledgementManager(BaseConnectionManager):
    pass

# インスタンスを作成
connection_board_manager = ConnectionBoardManager()
connection_acknowledgement_manager = ConnectionAcknowledgementManager()

@router.websocket("/ws_board_list")
async def websocket_board_endpoint(websocket: WebSocket):
    await connection_board_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await connection_board_manager.broadcast(message)
    except WebSocketDisconnect:
        connection_board_manager.disconnect(websocket)
    except json.JSONDecodeError:
        print("Invalid JSON format")
    except Exception as e:
        connection_board_manager.disconnect(websocket)
        print(f"WebSocket Error: {e}")  # ログにエラー出力

@router.get("/boards/{user_id}/", response_model=list[board_schema.BoardWithOtherInfo])
async def list_boards(
    user_id: int,
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db)
):
    return await board_crud.get_boards(db, user_id=user_id, page=page)

@router.post("/boards", response_model=board_schema.BoardCreateResponse)
async def create_board(
    board_body: board_schema.BoardCreate, db: AsyncSession = Depends(get_db)
):
    try:
        new_board = await board_crud.create_board(db, board_body)
        user = await board_crud.get_user(db, new_board.user_id)

        # 更新が成功した後、WebSocketを通じてユーザーにメッセージを送信
        message = {
                "action": "create",
                "id": new_board.id, 
                "content": new_board.content, 
                "created_at": board_body.created_at.isoformat(), 
                "group": new_board.group,
                "user_id": new_board.user_id,
                "user_name": user.name,
                "acknowledgements": 0,
                "is_acknowledged": False,
        }
        await connection_board_manager.broadcast(message)
        return new_board
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.delete("/boards/{id}", response_model=None)
async def delete_board(id: int, db: AsyncSession = Depends(get_db)):
    board = await board_crud.get_board(db, id=id)
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")

    await board_crud.delete_board(db, original=board)

    # 更新が成功した後、WebSocketを通じてユーザーにメッセージを送信
    message = {
        "action": "delete",  # 追加: アクションの種類を指定
        "id": id,
    }
    await connection_board_manager.broadcast(message)

    return {"detail": "Board deleted successfully"}

@router.websocket("/ws_acknowledgement_list")
async def websocket_acknowledgement_endpoint(websocket: WebSocket):
    await connection_acknowledgement_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await connection_acknowledgement_manager.broadcast(message)
    except WebSocketDisconnect:
        connection_acknowledgement_manager.disconnect(websocket)
    except json.JSONDecodeError:
        print("Invalid JSON format")
    except Exception as e:
        connection_acknowledgement_manager.disconnect(websocket)
        print(f"WebSocket Error: {e}")  # ログにエラー出力

@router.get("/acknowledgement_users/{board_id}", response_model=list[board_schema.AcknowledgementsWithUserInfo])
async def list_acknowledgement_users(
    board_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await board_crud.get_acknowledged_users(db, board_id=board_id)

@router.post("/acknowledgements", response_model=board_schema.AcknowledgementCreateResponse)
async def create_acknowledgement(
    acknowledgement_body: board_schema.AcknowledgementCreate, db: AsyncSession = Depends(get_db)
):
    try:
        new_acknowledgement = await board_crud.create_acknowledgement(db, acknowledgement_create=acknowledgement_body)

        # 更新が成功した後、WebSocketを通じてユーザーにメッセージを送信
        # acknowledgementの数を更新
        message = {
                "action": "create",
                "board_id": new_acknowledgement.board_id,
        }
        await connection_acknowledgement_manager.broadcast(message)
        return new_acknowledgement
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.delete("/acknowledgements/{board_id}/{user_id}", response_model=None)
async def delete_acknowledgement(
    board_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    acknowledgement = await board_crud.get_acknowledgement_by_board_and_user(db, board_id=board_id, user_id=user_id)
    if acknowledgement is None:
        raise HTTPException(status_code=404, detail="Acknowledgement not found")

    await board_crud.delete_acknowledgement(db, original=acknowledgement)

    # 更新が成功した後、WebSocketを通じてユーザーにメッセージを送信
    # acknowledgementの数を更新
    message = {
        "action": "delete",  # 追加: アクションの種類を指定
        "board_id": board_id,
    }
    await connection_acknowledgement_manager.broadcast(message)

    return {"detail": "Acknowledgemen deleted successfully"}