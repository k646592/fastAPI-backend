from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

import api.models.user as user_model
import api.schemas.user as user_schema

async def get_users(db: AsyncSession) -> list[user_model.User]:
    result = await db.execute(select(user_model.User))
    return result.scalars().all()

async def create_user(db: AsyncSession, user_create_data: user_model.User) -> user_model.User:
    user_create = user_model.User(**user_create_data)

    db.add(user_create)
    await db.commit()
    await db.refresh(user_create)
    return user_create

async def get_user(db: AsyncSession, id: str) -> user_model.User | None:
    result: Result = await db.execute(
        select(user_model.User).filter(user_model.User.id == id)
    )
    return result.scalars().first()

async def update_user(
        db: AsyncSession, user_update: user_schema.UserUpdate, original: user_model.User
) -> user_model.User:
    original.group = user_update.group
    original.grade = user_update.grade
    original.name = user_update.name
    db.add(original)
    await db.commit()
    await db.refresh(original)
    return original

async def update_user_image(
        db: AsyncSession, user_update: user_schema.UserUpdateImage, original: user_model.User
) -> user_model.User:
    original.image_name = user_update.image_name
    original.image_url = user_update.image_url
    db.add(original)
    await db.commit()
    await db.refresh(original)
    return original

async def update_user_location(
        db: AsyncSession, user_update: user_schema.UserUpdateLocation, original: user_model.User
) -> user_model.User:
    original.now_location = user_update.now_location
    db.add(original)
    await db.commit()
    await db.refresh(original)
    return original

async def update_user_location_status(
        db: AsyncSession, user_update: user_schema.UserUpdateLocation, original: user_model.User, status: str
) -> user_model.User:
    original.now_location = user_update.now_location
    original.status = status
    db.add(original)
    await db.commit()
    await db.refresh(original)
    return original

async def update_user_location_status_flag(
        db: AsyncSession, user_update: user_schema.UserUpdateLocation, original: user_model.User
) -> user_model.User:
    original.now_location = user_update.now_location
    original.location_flag = True
    original.status = "出席"
    db.add(original)
    await db.commit()
    await db.refresh(original)
    return original

async def get_user_name(db: AsyncSession, id: str) -> user_model.User | None:
    result: Result = await db.execute(
        select(user_model.User).filter(user_model.User.id == id)
    )
    return result.scalars().first()

async def update_user_email(
        db: AsyncSession, user_update: user_schema.UserUpdateEmail, original: user_model.User
) -> user_model.User:
    original.email = user_update.email
    db.add(original)
    await db.commit()
    await db.refresh(original)
    return original

async def delete_user(db: AsyncSession, original: user_model.User) -> None:
    await db.delete(original)
    await db.commit()