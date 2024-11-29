from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

import api.models.user as user_model
import api.models.board as board_model
import api.schemas.board as board_schema

async def get_boards(db: AsyncSession, page: int) -> list[board_model.Board]:
    # OFFSET計算: (ページ番号 - 1) * ページサイズ
    offset = (page - 1) * 10
    
    result = await db.execute(
        select(board_model.Board)
        .options(joinedload(board_model.Board.user))
        .order_by(board_model.Board.created_at.desc())  # 日付の降順
        .offset(offset)  # ページングの開始位置
        .limit(10)  # ページサイズ（1ページあたりの件数）
    )
    boards = result.scalars().all()
    
    return [
        board_schema.BoardWithUserName(
            id=board.id,
            content=board.content,
            created_at=board.created_at,
            group=board.group,
            user_id=board.user_id,
            user_name=board.user.name if board.user else None,
        )
        for board in boards
    ]

async def get_user(db: AsyncSession, user_id: int) -> user_model.User | None:
    result: Result = await db.execute(
        select(user_model.User).filter(user_model.User.id == user_id)
    )
    return result.scalars().first()

async def create_board(
        db: AsyncSession, board_create: board_schema.BoardCreate
) -> board_model.Board:
    board = board_model.Board(**board_create.dict())
    db.add(board)
    await db.commit()
    await db.refresh(board)
    return board

async def get_board(db: AsyncSession, id: int) -> board_model.Board | None:
    result: Result = await db.execute(
        select(board_model.Board).filter(board_model.Board.id == id)
    )
    return result.scalars().first()

async def delete_board(db: AsyncSession, original: board_model.Board) -> None:
    await db.delete(original)
    await db.commit()

