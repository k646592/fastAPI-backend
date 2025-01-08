from fastapi import HTTPException
from sqlalchemy import select, func, desc, and_
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, aliased
from datetime import datetime, timedelta

import api.models.private_chat as chat_model
import api.models.user as user_model
import api.schemas.private_chat as chat_schema

# 個人チャットのcruds

async def get_private_chat_room_ids(db: AsyncSession, user_id: str) -> list[int]:
    """
    ログイン中のユーザIDから、関連するPrivateChatRoomのIDを取得
    """
    query = (
        select(chat_model.PrivateChatRoomUser.private_chat_room_id)
        .filter(chat_model.PrivateChatRoomUser.user_id == user_id)
    )
    result = await db.execute(query)
    return [row.private_chat_room_id for row in result.fetchall()]

async def get_unread_message_count(db: AsyncSession, user_id: str, chat_room_ids: list[int]) -> int:
    query = (
        select(func.count())
        .select_from(chat_model.PrivateMessage)
        .where(
            and_(
                chat_model.PrivateMessage.private_chat_room_id.in_(chat_room_ids),  # 対象のルームID
                chat_model.PrivateMessage.user_id != user_id,       # 自分が送信者ではない
                chat_model.PrivateMessage.is_read == False            # 未読メッセージ
            )
        )
    )
    result = await db.execute(query)
    return result.scalar()  # カウント結果を返す

async def get_private_chat_users_with_updated_at(
   db: AsyncSession, 
   chat_room_ids: list[int], 
   user_id: str
) -> list[chat_schema.PrivateChatRoomInfo]:
   
   # 未読メッセージ数のサブクエリ（user_id以外のメッセージをカウント）
   unread_count = (
       select(
           chat_model.PrivateMessage.private_chat_room_id,
           func.count(chat_model.PrivateMessage.id).label('unread_count')
       )
       .filter(
           chat_model.PrivateMessage.private_chat_room_id.in_(chat_room_ids),
           chat_model.PrivateMessage.is_read == False,
           chat_model.PrivateMessage.user_id != user_id  # user_id以外の未読メッセージをカウント
       )
       .group_by(chat_model.PrivateMessage.private_chat_room_id)
       .subquery()
   )

   # メインクエリ
   query = (
       select(
           chat_model.PrivateChatRoomUser.private_chat_room_id,
           chat_model.PrivateChatRoomUser.user_id,
           chat_model.PrivateChatRoom.updated_at,
           func.coalesce(unread_count.c.unread_count, 0).label('unread_count')
       )
       .join(
           chat_model.PrivateChatRoom,
           chat_model.PrivateChatRoom.id == chat_model.PrivateChatRoomUser.private_chat_room_id
       )
       .outerjoin(
           unread_count,
           unread_count.c.private_chat_room_id == chat_model.PrivateChatRoomUser.private_chat_room_id
       )
       .filter(
           chat_model.PrivateChatRoomUser.user_id != user_id,
           chat_model.PrivateChatRoom.id.in_(chat_room_ids)
       )
   )

   result = await db.execute(query)
   rows = result.fetchall()

   return [
       chat_schema.PrivateChatRoomInfo(
           private_chat_room_id=row.private_chat_room_id,
           user_id=row.user_id,
           updated_at=row.updated_at,
           unread_count=row.unread_count
       )
       for row in rows
   ]


async def get_private_chat_users_with_details(
    db: AsyncSession,
    chat_room_infos: list[chat_schema.PrivateChatRoomInfo]
) -> list[chat_schema.PrivateChatUser]:
    """
    チャットルーム情報からユーザー情報を取得し、PrivateChatUser型として返す。
    """
    # user_id を抽出
    user_ids = [info.user_id for info in chat_room_infos]

    # ユーザー情報を取得
    query = select(
        user_model.User.id,
        user_model.User.email,
        user_model.User.grade,
        user_model.User.group,
        user_model.User.name,
        user_model.User.status,
        user_model.User.image_name,
        user_model.User.image_url,
        user_model.User.now_location,
        user_model.User.location_flag
    ).filter(user_model.User.id.in_(user_ids))

    result = await db.execute(query)
    user_rows = result.fetchall()

    # user_id をキーとした updated_at の辞書を作成
    updated_at_map = {info.user_id: info.updated_at for info in chat_room_infos}
    unread_count_map = {info.user_id: info.unread_count for info in chat_room_infos}

    # データを PrivateChatUser に変換
    private_chat_users = [
        chat_schema.PrivateChatUser(
            id=row.id,
            email=row.email,
            grade=row.grade,
            group=row.group,
            name=row.name,
            status=row.status,
            image_name=row.image_name,
            image_url=row.image_url,
            now_location=row.now_location,
            location_flag=row.location_flag,
            updated_at=updated_at_map.get(row.id),  # updated_at をマッピング
            unread_count=unread_count_map.get(row.id, 0)
        )
        for row in user_rows
    ]

    private_chat_users = sorted(
        private_chat_users,
        key=lambda user: user.updated_at or datetime.min,  # updated_at が None の場合に対応
        reverse=True  # 降順
    )

    return private_chat_users

async def get_users_not_in_chat_room_infos(
    db: AsyncSession,
    chat_room_infos: list[chat_schema.PrivateChatRoomInfo],
    user_id: str
) -> list[chat_schema.PrivateChatUser]:
    """
    chat_room_infos の user_id と一致せず、かつログイン中の user_id を除外したユーザーを取得し、
    PrivateChatUser 型として返す。updated_at は None に設定。
    """
    # chat_room_infos から user_id を抽出
    chat_user_ids = [info.user_id for info in chat_room_infos]

    # user_model から一致しないユーザーを取得
    query = select(
        user_model.User.id,
        user_model.User.email,
        user_model.User.grade,
        user_model.User.group,
        user_model.User.name,
        user_model.User.status,
        user_model.User.image_name,
        user_model.User.image_url,
        user_model.User.now_location,
        user_model.User.location_flag
    ).filter(
        ~user_model.User.id.in_(chat_user_ids),  # chat_room_infos の user_id と一致しない
        user_model.User.id != user_id  # ログイン中の user_id を除外
    )  # NOT IN 演算子で一致しないユーザーを取得

    result = await db.execute(query)
    user_rows = result.fetchall()

    # データを PrivateChatUser に変換
    private_chat_users = [
        chat_schema.PrivateChatUser(
            id=row.id,
            email=row.email,
            grade=row.grade,
            group=row.group,
            name=row.name,
            status=row.status,
            image_name=row.image_name,
            image_url=row.image_url,
            now_location=row.now_location,
            location_flag=row.location_flag,
            updated_at=None,  # updated_at を None に設定
            unread_count=0,
        )
        for row in user_rows
    ]

    return private_chat_users

async def get_or_create_private_chat_room(db: AsyncSession, user1_id: str, user2_id: str) -> chat_schema.PrivateChatRoom:
    # チャットルームを探す
    result = await db.execute(
        select(chat_model.PrivateChatRoom)
        .join(chat_model.PrivateChatRoomUser)
        .where(chat_model.PrivateChatRoomUser.user_id.in_([user1_id, user2_id]))
        .group_by(chat_model.PrivateChatRoom.id)
        .having(func.count(chat_model.PrivateChatRoom.id) == 2)
    )
    private_chat_room = result.scalars().first()

    # チャットルームが存在しない場合、新規作成
    if not private_chat_room:
        try:
            current_time = datetime.utcnow() + timedelta(hours=9)  # 日本時間 (UTC + 9時間)
            private_chat_room = chat_model.PrivateChatRoom(updated_at=current_time)  # updated_atを設定
            db.add(private_chat_room)
            await db.flush()  # chat_room.idを取得するためにflush

            db.add_all([
                chat_model.PrivateChatRoomUser(private_chat_room_id=private_chat_room.id, user_id=user1_id),
                chat_model.PrivateChatRoomUser(private_chat_room_id=private_chat_room.id, user_id=user2_id)
            ])
            await db.commit()
            await db.refresh(private_chat_room)
        except Exception as e:
            await db.rollback()
            raise e  # エラーメッセージをログに残すため再度発生させる

    return private_chat_room

async def unread_private_messages_update(
    db: AsyncSession, 
    private_chat_room_id: int, 
    user_id: str
) -> list[chat_schema.PrivateMessageUnreadUpdate]:
    try:
        # 未読メッセージを取得
        unread_messages = await db.execute(
            select(chat_model.PrivateMessage)
            .filter(
                chat_model.PrivateMessage.private_chat_room_id == private_chat_room_id,
                chat_model.PrivateMessage.user_id == user_id,
                chat_model.PrivateMessage.is_read == False
            )
        )
        unread_messages = unread_messages.scalars().all()
            
        updated_messages = []

        # メッセージを一つずつ既読に更新
        for message in unread_messages:
            message.is_read = True
            updated_messages.append(
                chat_schema.PrivateMessageUnreadUpdate(id=message.id, is_read=message.is_read)
            )
        
        # 変更をコミット
        await db.commit()

        return updated_messages  # 更新されたメッセージのリストを返す

    except Exception as e:
        await db.rollback()
        raise e  # エラーメッセージをログに残すため再度発生させる


async def get_private_messages(db: AsyncSession, private_chat_room_id: int, page: int) -> list[chat_model.PrivateMessage]:
    # OFFSET計算: (ページ番号 - 1) * ページサイズ
    offset = (page - 1) * 10
    
    result = await db.execute(
        select(chat_model.PrivateMessage)
        .where(chat_model.PrivateMessage.private_chat_room_id == private_chat_room_id)
        .order_by(chat_model.PrivateMessage.sent_at.desc())
        .offset(offset)  # ページングの開始位置
        .limit(10)  # ページサイズ（1ページあたりの件数）
    )
    messages = result.scalars().all()
    
    return messages

async def message_unread_update_websocket(db: AsyncSession, private_message_id: int) -> chat_schema.PrivateMessageUnreadUpdate:
    # 対象のメッセージを取得
    result = await db.execute(
        select(chat_model.PrivateMessage)
        .where(chat_model.PrivateMessage.id == private_message_id)
    )
    message = result.scalar_one_or_none()

    # メッセージが見つかった場合、is_read を更新
    if message:
        message.is_read = True
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return chat_schema.PrivateMessageUnreadUpdate(
            id=message.id,
            is_read=message.is_read,
        )
    
    # メッセージが見つからない場合はエラーをスロー
    raise HTTPException(status_code=404, detail="Message not found")

async def post_private_message(
        db: AsyncSession, private_message: chat_schema.PrivateMessageCreate
) -> chat_model.PrivateMessage:
    private_message = chat_model.PrivateMessage(**private_message.dict())
    db.add(private_message)
    await db.commit()
    await db.refresh(private_message)

    return private_message

async def get_private_chat_room(db: AsyncSession, id: int) -> chat_model.PrivateChatRoom | None:
    result: Result = await db.execute(
        select(chat_model.PrivateChatRoom).filter(chat_model.PrivateChatRoom.id == id)
    )
    return result.scalars().first()

async def update_private_chat_room(
        db: AsyncSession, update_private_chat_room: chat_schema.PrivateChatRoomUpdate, original: chat_model.PrivateChatRoom
) -> chat_model.PrivateChatRoom:
    original.updated_at = update_private_chat_room.updated_at
    db.add(original)
    await db.commit()
    await db.refresh(original)
    return original


async def get_other_user_id(private_chat_room_id: int, user_id: str, db: AsyncSession):
    try:
        # チャットルーム内の他のユーザーを取得
        stmt = select(chat_model.PrivateChatRoomUser).filter(chat_model.PrivateChatRoomUser.private_chat_room_id == private_chat_room_id)
        result = await db.execute(stmt)
        users_in_room = result.scalars().all()

        # 送信者以外のユーザーIDを取得
        other_user = None
        for user in users_in_room:
            if user.user_id != user_id:
                other_user = user.user_id
                break

        if not other_user:
            raise HTTPException(status_code=404, detail="No other user found in the chat room")
        
        return other_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving other user: {str(e)}")

