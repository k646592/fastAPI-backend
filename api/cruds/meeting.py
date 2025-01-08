from sqlalchemy import select, func
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from datetime import datetime
from sqlalchemy import desc  # descをインポートする

import api.models.meeting as meeting_model
import api.schemas.meeting as meeting_schema

async def get_meetings(
        team: str, 
        kinds: str,
        db: AsyncSession
) -> list[meeting_schema.MeetingWithUserName]:
    result = await db.execute(
        select(meeting_model.Meeting)
        .options(joinedload(meeting_model.Meeting.user))
        .where(
            meeting_model.Meeting.team == team,
            meeting_model.Meeting.kinds == kinds
        )  # teamとkindsの値が一致する条件を追加
        .order_by(desc(meeting_model.Meeting.created_at))  # created_atの降順に指定
    )
    
    meetings = result.scalars().all()
    
    return [
        meeting_schema.MeetingWithUserName(
            id=meeting.id,
            title=meeting.title,
            created_at=meeting.created_at,
            team=meeting.team,
            main_text=meeting.main_text,
            user_id=meeting.user_id,
            user_name=meeting.user.name if meeting.user else None,  # Userオブジェクトが存在しない場合を考慮
            kinds=meeting.kinds
        )
        for meeting in meetings
    ]

async def create_meeting(
        db: AsyncSession, meeting_create: meeting_schema.MeetingCreate
) -> meeting_model.Meeting:
    meeting = meeting_model.Meeting(**meeting_create.dict())
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)
    return meeting

async def get_meeting(db: AsyncSession, id: int) -> meeting_model.Meeting | None:
    result: Result = await db.execute(
        select(meeting_model.Meeting).filter(meeting_model.Meeting.id == id)
    )
    return result.scalars().first()

async def update_meeting(
        db: AsyncSession, meeting_update: meeting_schema.MeetingUpdate, original: meeting_model.Meeting
) -> meeting_model.Meeting:
    original.title = meeting_update.title
    original.team = meeting_update.team
    original.kinds = meeting_update.kinds
    db.add(original)
    await db.commit()
    await db.refresh(original)
    return original

async def update_meeting_main_text(db: AsyncSession, update_main_text: meeting_schema.MeetingUpdateMainText, original: meeting_model.Meeting
) -> meeting_model.Meeting:
    original.main_text = update_main_text.main_text
    db.add(original)
    await db.commit()
    await db.refresh(original)
    return original

async def delete_meeting(db: AsyncSession, original: meeting_model.Meeting) -> None:
    await db.delete(original)
    await db.commit()
