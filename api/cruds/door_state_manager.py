from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

import api.models.door_state_manager as door_state_manager_model
import api.schemas.door_state_manager as door_state_manager_schema

async def create_door_state(
        db: AsyncSession, create_body: door_state_manager_schema.DoorStatus 
) -> door_state_manager_model.DoorStateManager:
    door_state_manager = door_state_manager_model.DoorStateManager(**create_body.dict())
    db.add(door_state_manager)
    await db.commit()
    await db.refresh(door_state_manager)
    return door_state_manager

async def get_door_state(db: AsyncSession, id: int) -> door_state_manager_model.DoorStateManager | None:
    result: Result = await db.execute(
        select(door_state_manager_model.DoorStateManager).filter(door_state_manager_model.DoorStateManager.id == id)
    )
    return result.scalars().first()

async def update_door_state(
        db: AsyncSession, update_body: door_state_manager_schema.DoorStatus, original: door_state_manager_model.DoorStateManager
) -> door_state_manager_model.DoorStateManager:
    original.status = update_body.status
    db.add(original)
    await db.commit()
    await db.refresh(original)
    return original