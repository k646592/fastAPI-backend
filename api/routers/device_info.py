from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

import api.cruds.device_info as device_crud
from api.db import get_db

import api.schemas.device_info as device_schema


router = APIRouter()


@router.post("/device_info", response_model=device_schema.DeviceInfoCreateResponse)
async def create_device_info(
    device_body: device_schema.DeviceInfoCreate, db: AsyncSession = Depends(get_db)
):
    try:
        new_device = await device_crud.create_device_info(db, device_body)
        
        
        return new_device
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

