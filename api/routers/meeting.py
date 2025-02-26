from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List

import api.cruds.meeting as meeting_crud
from api.db import get_db

import api.schemas.meeting as meeting_schema

router = APIRouter()

# ================================
#  既存の CRUD (REST API) 部分
# ================================
@router.get("/meetings", response_model=list[meeting_schema.MeetingWithUserName])
async def list_meetings(
    team: str = Query(..., description="Team name to filter"),
    kinds: str = Query(..., description="Kinds to filter"),
    db: AsyncSession = Depends(get_db)
):
    return await meeting_crud.get_meetings(team=team, kinds=kinds, db=db)

@router.get("/meetings/{id}", response_model=meeting_schema.GetMeetingMainText)
async def get_meeting(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    meeting = await meeting_crud.get_meeting(db, id=id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    meeting_data = {
        "main_text": meeting.main_text,
        "id": meeting.id,
    }
    meeting_get = meeting_schema.GetMeetingMainText(**meeting_data)
    return meeting_get

@router.post("/meetings", response_model=meeting_schema.MeetingCreateResponse)
async def create_meeting(
    meeting_body: meeting_schema.MeetingCreate, db: AsyncSession = Depends(get_db)
):
    new_meeting = await meeting_crud.create_meeting(db, meeting_body)
    return new_meeting

@router.patch("/meetings/{id}", response_model=meeting_schema.MeetingUpdateResponse)
async def update_event(
    id: int,
    meeting_body: meeting_schema.MeetingUpdate,
    db: AsyncSession = Depends(get_db)
):
    meeting = await meeting_crud.get_meeting(db, id=id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Event not found")
    updated_meeting = await meeting_crud.update_meeting(db, meeting_body, original=meeting)
    return updated_meeting

@router.patch("/update_main_text/{id}", response_model=meeting_schema.MeetingUpdateMainTextResponse)
async def update_main_text(
    id: int,
    meeting_body: meeting_schema.MeetingUpdateMainText,
    db: AsyncSession = Depends(get_db)
):
    meeting = await meeting_crud.get_meeting(db, id=id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    updated_meeting = await meeting_crud.update_meeting_main_text(db, meeting_body, original=meeting)
    return updated_meeting

@router.delete("/meetings/{id}", response_model=None)
async def delete_meeting(id: int, db: AsyncSession = Depends(get_db)):
    meeting = await meeting_crud.get_meeting(db, id=id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return await meeting_crud.delete_meeting(db, original=meeting)


# ==================================
# ★ WebSocket 通信の追加部分 (ここから)
# ==================================

class ConnectionManager:
    """
    MeetingID ごとに接続している WebSocket を管理するクラス。
    active_connections = {
      <meeting_id>: [<WebSocket>, <WebSocket>, ...],
      ...
    }
    """
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, meeting_id: int, websocket: WebSocket):
        await websocket.accept()  # WebSocket 接続を許可
        if meeting_id not in self.active_connections:
            self.active_connections[meeting_id] = []
        self.active_connections[meeting_id].append(websocket)

    def disconnect(self, meeting_id: int, websocket: WebSocket):
        if meeting_id in self.active_connections:
            self.active_connections[meeting_id].remove(websocket)
            # リストが空になったらキーごと削除
            if not self.active_connections[meeting_id]:
                del self.active_connections[meeting_id]

    async def broadcast(self, meeting_id: int, message: str):
        """同じ meeting_id に接続中のクライアント全員に message を送信"""
        if meeting_id in self.active_connections:
            for connection in self.active_connections[meeting_id]:
                await connection.send_text(message)


manager = ConnectionManager()

@router.websocket("/ws/meetings/{meeting_id}")
async def websocket_meeting(
    websocket: WebSocket,
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    print(f"WebSocket request received for meeting {meeting_id}")
    
    """
    フルテキスト上書き方式の簡易サンプル。
    1) クライアントが接続してきたら、現在の main_text を送る
    2) クライアントからテキスト全文を受け取るとDBに上書きし、同じ会議IDに接続中の全員にブロードキャスト
    """
    await manager.connect(meeting_id, websocket)

    # DB から該当ミーティングを取得
    meeting = await meeting_crud.get_meeting(db, id=meeting_id)
    if not meeting:
        # ミーティングが見つからない場合
        await websocket.send_text("Meeting not found.")
        await websocket.close()
        manager.disconnect(meeting_id, websocket)
        return

    # 接続直後に、現在の main_text を送信（初期表示用）
    await websocket.send_text(meeting.main_text or "")

    try:
        # メッセージ受信を待ち続ける
        while True:
            data = await websocket.receive_text()  # クライアントからテキスト全文を受け取る

            # DB上のmain_textを上書き
            meeting.main_text = data
            db.add(meeting)
            await db.commit()
            await db.refresh(meeting)

            # 同じmeeting_idに接続しているクライアント全員に最新テキストを送信
            await manager.broadcast(meeting_id, data)

    except WebSocketDisconnect:
        # 接続が切れた場合はリストから削除
        manager.disconnect(meeting_id, websocket)

# ==================================
# ★ WebSocket 通信の追加部分 (ここまで)
# ==================================