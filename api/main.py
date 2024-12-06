from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from datetime import datetime
import pytz
import os
import logging

from api.db import async_session
from api.routers import event, user, attendance, mail, chat, meeting, door_state_manager, board
import api.cruds.attendance as attendance_crud

app = FastAPI()

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORSの設定
origins = [
    os.getenv("FRONTEND_DOMAIN", "http://localhost"),
    os.getenv("FRONTEND_DOMAIN_DEV", "http://localhost:8000"),
    os.getenv("FRONTEND_DOMAIN_DEV_ALT", "http://localhost:60425")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def update_db_daily():
    """日付が変わった時にDBを非同期で更新する関数"""
    last_checked_day = datetime.now(pytz.timezone('Asia/Tokyo')).date()
    
    while True:
        # 1分ごとに現在時刻をチェック
        await asyncio.sleep(60)
        
        now = datetime.now(pytz.timezone('Asia/Tokyo'))
        current_day = now.date()
        
        if current_day != last_checked_day:
            try:
                # DB更新処理
                async with async_session() as session:
                    async with session.begin():
                        await attendance_crud.update_user_status_newday(session)
                logger.info(f"Database updated at {now}")
            except Exception as e:
                logger.error(f"Failed to update database: {e}")
            last_checked_day = current_day

@app.on_event("startup")
async def startup_event():
    """アプリ起動時に非同期タスクをスケジュール"""
    asyncio.create_task(update_db_daily())

app.include_router(event.router)
app.include_router(user.router)
app.include_router(attendance.router)
app.include_router(mail.router)
app.include_router(chat.router)
app.include_router(meeting.router)
app.include_router(door_state_manager.router)
app.include_router(board.router)