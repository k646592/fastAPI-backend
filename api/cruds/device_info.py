from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

import api.models.device_info as device_model
import api.schemas.device_info as device_schema


async def create_device_info(
        db: AsyncSession, device_info_create: device_schema.DeviceInfoCreate
) -> device_model.DeviceInfo:
    device_info = device_model.DeviceInfo(**device_info_create.dict())
    db.add(device_info)
    await db.commit()
    await db.refresh(device_info)
    return device_info
