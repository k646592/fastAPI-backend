from sqlalchemy import select, func, delete
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

import api.models.user as user_model
import api.models.board as board_model
import api.schemas.board as board_schema

async def get_boards(db: AsyncSession, user_id: str, page: int) -> list[board_model.Board]:
    # OFFSET計算: (ページ番号 - 1) * ページサイズ
    offset = (page - 1) * 10

    # サブクエリ: 各 board_id ごとの Acknowledgement 数を集計
    acknowledgement_count_subquery = (
        select(
            board_model.Acknowledgement.board_id,
            func.count(board_model.Acknowledgement.id).label("acknowledgement_count")
        )
        .group_by(board_model.Acknowledgement.board_id)
        .subquery()
    )

    # サブクエリ: 現在のユーザーが了解を押している board_id の一覧
    user_acknowledgement_subquery = (
        select(board_model.Acknowledgement.board_id)
        .where(board_model.Acknowledgement.user_id == user_id)
        .subquery()
    )

    # メインクエリ: Board とサブクエリを結合
    result = await db.execute(
        select(
            board_model.Board,
            acknowledgement_count_subquery.c.acknowledgement_count,
            user_acknowledgement_subquery.c.board_id.label("is_acknowledged")
        )
        .options(joinedload(board_model.Board.user))
        .outerjoin(
            acknowledgement_count_subquery, 
            board_model.Board.id == acknowledgement_count_subquery.c.board_id
        )  # Board と Acknowledgement 集計サブクエリを結合
        .outerjoin(
            user_acknowledgement_subquery, 
            board_model.Board.id == user_acknowledgement_subquery.c.board_id
        )  # Board と現在のユーザーの Acknowledgement サブクエリを結合
        .order_by(board_model.Board.created_at.desc())  # 日付の降順
        .offset(offset)  # ページングの開始位置
        .limit(10)  # ページサイズ（1ページあたりの件数）
    )
    boards = result.fetchall()  # scalars()ではなくfetchall()で複数カラムの結果を取得

    # データを整形
    return [
        board_schema.BoardWithOtherInfo(
            id=board.Board.id,
            content=board.Board.content,
            created_at=board.Board.created_at,
            group=board.Board.group,
            user_id=board.Board.user_id,
            user_name=board.Board.user.name if board.Board.user else None,
            acknowledgements=board.acknowledgement_count or 0,  # None の場合は 0
            is_acknowledged=board.is_acknowledged is not None  # None なら未押下、値があれば押下済み
        )
        for board in boards
    ]

async def get_user(db: AsyncSession, user_id: str) -> user_model.User | None:
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
    # 関連する Acknowledgement を削除
    await db.execute(
        delete(board_model.Acknowledgement).where(board_model.Acknowledgement.board_id == original.id)
    )
    await db.delete(original)
    await db.commit()


async def get_acknowledged_users(db: AsyncSession, board_id: int) -> list[dict]:
    result = await db.execute(
        select(
            board_model.Acknowledgement.user_id,
            user_model.User.name,
            user_model.User.image_url,
            user_model.User.image_name,
            board_model.Acknowledgement.created_at  
        )
        .join(user_model.User, user_model.User.id == board_model.Acknowledgement.user_id)  # User テーブルと結合
        .where(board_model.Acknowledgement.board_id == board_id)  # 指定した board_id に限定
    )

    users = result.fetchall()

    # 必要な形式に変換
    return [
        board_schema.AcknowledgementsWithUserInfo(
            user_id=user.user_id,
            user_name=user.name,
            image_url=user.image_url,
            image_name=user.image_name,
            created_at=user.created_at,  
        )
        for user in users
    ]

async def create_acknowledgement(
        db: AsyncSession, acknowledgement_create: board_schema.AcknowledgementCreate
) -> board_model.Acknowledgement:
    acknowledgement = board_model.Acknowledgement(**acknowledgement_create.dict())
    db.add(acknowledgement)
    await db.commit()
    await db.refresh(acknowledgement)
    return acknowledgement

async def get_acknowledgement_by_board_and_user(
    db: AsyncSession, board_id: int, user_id: str
) -> board_model.Acknowledgement | None:
    result: Result = await db.execute(
        select(board_model.Acknowledgement)
        .filter(
            board_model.Acknowledgement.board_id == board_id,
            board_model.Acknowledgement.user_id == user_id
        )
    )
    return result.scalars().first()


async def delete_acknowledgement(db: AsyncSession, original: board_model.Acknowledgement) -> None:
    await db.delete(original)
    await db.commit()
