from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload
from datetime import datetime
import pytz

import api.models.user as user_model
import api.models.attendance as attendance_model
import api.schemas.attendance as attendance_schema

async def get_users(db: AsyncSession) -> list[user_model.User]:
    result = await db.execute(select(user_model.User))
    return result.scalars().all()

async def get_user(db: AsyncSession, user_id: int) -> user_model.User | None:
    result: Result = await db.execute(
        select(user_model.User).filter(user_model.User.id == user_id)
    )
    return result.scalars().first()

async def update_user_status(
        db: AsyncSession, user_update_status: attendance_schema.UserUpdateStatus, original: user_model.User
) -> user_model.User:
    original.status = user_update_status.status
    db.add(original)
    await db.commit()
    await db.refresh(original)
    return original

async def update_user_status_newday(db: AsyncSession):
    try:
        # 全てのユーザーを取得
        users = await get_users(db)
        if not users:
            print("ユーザーが見つかりませんでした")
            return

        # 全てのユーザーのステータスを「未出席」に更新
        for user in users:
            user.status = "未出席"

        # 現在の日付を取得（タイムゾーンは適宜設定）
        today = datetime.now(pytz.timezone('Asia/Tokyo')).date()

        # titleが欠席で、startとendの間に今日の日付があるattendanceを検索
        result = await db.execute(
            select(attendance_model.Attendance)
            .where(attendance_model.Attendance.title == "欠席")
            .where(attendance_model.Attendance.start <= today)
            .where(attendance_model.Attendance.end >= today)
            .options(selectinload(attendance_model.Attendance.user))  # Userを事前にロード
        )
        attendances = result.scalars().all()

        # 対象のユーザーのステータスを「欠席」に更新
        for attendance in attendances:
            attendance.user.status = "欠席"

        # 変更をデータベースにコミット
        await db.commit()

    except Exception as e:
        # エラーハンドリング
        await db.rollback()  # エラー時にロールバック
        print(f"エラーが発生しました: {e}")


async def get_attendances(db: AsyncSession) -> list[attendance_model.Attendance]:
    result = await db.execute(
        select(attendance_model.Attendance)
        .options(joinedload(attendance_model.Attendance.user))
    )
    attendances = result.scalars().all()
    
    return [
        attendance_schema.AttendanceWithUserName(
            id=attendance.id,
            title=attendance.title,
            description=attendance.description,
            user_id=attendance.user_id,
            user_name=attendance.user.name if attendance.user else None,  # Userオブジェクトが存在しない場合を考慮
            mail_send=attendance.mail_send,
            start=attendance.start,
            end=attendance.end,
            undecided=attendance.undecided
        )
        for attendance in attendances
    ]

async def create_attendance(
        db: AsyncSession, attendance_create: attendance_schema.AttendanceCreate
) -> attendance_model.Attendance:
    attendance = attendance_model.Attendance(**attendance_create.dict())
    db.add(attendance)
    await db.commit()
    await db.refresh(attendance)
    return attendance

async def get_attendance(db: AsyncSession, id: int) -> attendance_model.Attendance | None:
    result: Result = await db.execute(
        select(attendance_model.Attendance).filter(attendance_model.Attendance.id == id)
    )
    return result.scalars().first()

async def update_attendance(
        db: AsyncSession, attendance_update: attendance_schema.AttendanceUpdate, original: attendance_model.Attendance
) -> attendance_model.Attendance:
    original.title = attendance_update.title
    original.description = attendance_update.description
    original.user_id = attendance_update.user_id
    original.start = attendance_update.start
    original.end = attendance_update.end
    original.mail_send = attendance_update.mail_send
    original.undecided = attendance_update.undecided
    db.add(original)
    await db.commit()
    await db.refresh(original)
    return original

async def delete_event(db: AsyncSession, original: attendance_model.Attendance) -> None:
    await db.delete(original)
    await db.commit()

