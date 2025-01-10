from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.db import get_db

import api.cruds.seat as seat_crud
import api.schemas.seat as seat_schema

router = APIRouter()

@router.post("/seats", response_model=list[seat_schema.SeatResponse])
async def update_or_create_seats(
    seats: list[seat_schema.SeatUpdate], 
    db: AsyncSession = Depends(get_db)
):
    # データを更新または作成
    all_seats = await seat_crud.bulk_update_or_create_seats_and_get_all(db, seats)

    return all_seats