from fastapi import APIRouter, WebSocket, WebSocketDisconnect


import json


router = APIRouter()

# WebSocket接続を管理するクラス
class ConnectionTotalChatUserManager:
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

chat_user_total_manager = ConnectionTotalChatUserManager()

@router.websocket("/ws_chat_list_unread_total/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: str, 
):
    await chat_user_total_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)  # テキストデータをJSONにパース
            await chat_user_total_manager.broadcast({"type": "broadcast", "message": message}, user_id)

    except WebSocketDisconnect:
        chat_user_total_manager.disconnect(websocket, user_id)
    except json.JSONDecodeError:
        print("Invalid JSON format")
    except Exception as e:
        await websocket.close(code=1001)  # エラー時に接続を閉じる
        print(f"Unexpected error: {e}")