from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import api.models.seat as seat_model

import api.schemas.seat as seat_schema

async def bulk_update_or_create_seats_and_get_all(
    db: AsyncSession, seats: list[seat_schema.SeatUpdate]
) -> list[seat_model.Seat]:
    """
    複数の座席データを更新または作成し、その後すべての座席データを取得して返す。
    """
    for seat_data in seats:
        # 座席IDがすでに存在するか確認
        result = await db.execute(select(seat_model.Seat).filter(seat_model.Seat.id == seat_data.id))
        existing_seat = result.scalar_one_or_none()

        if existing_seat:
            # 更新
            existing_seat.status = seat_data.status
        else:
            # 作成
            new_seat = seat_model.Seat(id=seat_data.id, status=seat_data.status)
            db.add(new_seat)

    # コミットして変更を保存
    await db.commit()

    # 更新後の座席データを取得
    result = await db.execute(select(seat_model.Seat))
    all_seats = result.scalars().all()
    return all_seats
