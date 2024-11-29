from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import json

import api.cruds.board as board_crud
from api.db import get_db

import api.schemas.board as board_schema

router = APIRouter()

class ConnectionBoardManager:
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
connection_board_manager = ConnectionBoardManager()

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

@router.get("/boards/", response_model=list[board_schema.BoardWithUserName])
async def list_boards(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db)
):
    return await board_crud.get_boards(db, page=page)

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