from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

import api.models.user as user_model
import api.models.event as event_model
import api.schemas.event as event_schema

async def get_events(db: AsyncSession) -> list[event_model.Event]:
    result = await db.execute(
        select(event_model.Event)
        .options(joinedload(event_model.Event.user))
        )
    events = result.scalars().all()
    
    return [
        event_schema.EventWithUserName(
            id=event.id,
            title=event.title,
            description=event.description,
            unit=event.unit,
            user_id=event.user_id,
            user_name=event.user.name if event.user else None,  # Userオブジェクトが存在しない場合を考慮
            mail_send=event.mail_send,
            start=event.start,
            end=event.end,
        )
        for event in events
    ]

async def get_user(db: AsyncSession, user_id: int) -> user_model.User | None:
    result: Result = await db.execute(
        select(user_model.User).filter(user_model.User.id == user_id)
    )
    return result.scalars().first()

async def create_event(
        db: AsyncSession, event_create: event_schema.EventCreate
) -> event_model.Event:
    event = event_model.Event(**event_create.dict())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event

async def get_event(db: AsyncSession, id: int) -> event_model.Event | None:
    result: Result = await db.execute(
        select(event_model.Event).filter(event_model.Event.id == id)
    )
    return result.scalars().first()

async def update_event(
        db: AsyncSession, event_update: event_schema.EventUpdate, original: event_model.Event
) -> event_model.Event:
    original.title = event_update.title
    original.description = event_update.description
    original.unit = event_update.unit
    original.user_id = event_update.user_id
    original.start = event_update.start
    original.end = event_update.end
    original.mail_send = event_update.mail_send
    db.add(original)
    await db.commit()
    await db.refresh(original)
    return original

async def delete_event(db: AsyncSession, original: event_model.Event) -> None:
    await db.delete(original)
    await db.commit()

