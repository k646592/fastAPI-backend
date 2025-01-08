from fastapi import HTTPException
from sqlalchemy import select, func, desc, delete
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, aliased
from datetime import datetime, timedelta

import api.models.group_chat as chat_model
import api.models.user as user_model
import api.schemas.group_chat as chat_schema


# グループチャットのcruds

async def get_create_chat_users(
        db: AsyncSession, user_id: str
) -> chat_schema.GetChatMemberCreateBase:
    stmt = select(user_model.User).where(user_model.User.id != user_id)
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    # 結果を Pydantic モデルに変換
    user_list = [
        chat_schema.GetChatMemberCreateBase(id=user.id, group=user.group, name=user.name, grade=user.grade)
        for user in users
    ]
    return user_list

async def create_group_chat(
        db: AsyncSession, group_chat_create: chat_schema.GroupChatRoomCreate, member_ids: list[str]
) -> chat_model.GroupChatRoom:
    group_chat = chat_model.GroupChatRoom(**group_chat_create.dict())
    db.add(group_chat)
    await db.flush()  # グループチャットルームのIDを取得するためにflushします

    # メンバーをGroupChatRoomUserテーブルに追加
    for user_id in member_ids:
        group_chat_user = chat_model.GroupChatRoomUser(
            group_chat_room_id=group_chat.id,
            user_id=user_id,
            joined_date=group_chat.created_at,
            leave_date=None,
            join=True,
        )
        db.add(group_chat_user)
    await db.commit()
    await db.refresh(group_chat)
    return group_chat

async def get_entry_group_chat_room(db: AsyncSession, user_id: int) -> list[chat_schema.GroupChatRoom]:
    # サブクエリで各グループチャットルームのunread_countを計算
    unread_count_subquery = (
        select(
            chat_model.UnreadMessage.group_chat_room_id,
            func.count(chat_model.UnreadMessage.id).label("unread_count"),
        )
        .where(chat_model.UnreadMessage.user_id == user_id)  # 対象ユーザーの未読メッセージ
        .group_by(chat_model.UnreadMessage.group_chat_room_id)
        .subquery()
    )

    # メインクエリでグループチャットルームとunread_countを取得
    result = await db.execute(
        select(
            chat_model.GroupChatRoom,
            unread_count_subquery.c.unread_count
        )
        .join(
            chat_model.GroupChatRoomUser,
            chat_model.GroupChatRoom.id == chat_model.GroupChatRoomUser.group_chat_room_id
        )
        .outerjoin(
            unread_count_subquery,
            chat_model.GroupChatRoom.id == unread_count_subquery.c.group_chat_room_id
        )
        .where(chat_model.GroupChatRoomUser.user_id == user_id)
        .where(chat_model.GroupChatRoomUser.join == True)  # joinがTrueのもののみ
        .order_by(chat_model.GroupChatRoom.updated_at.desc())  # updated_at順にソート
    )

    # 結果を取得し、Pydanticモデルにマッピング
    group_chats = result.all()
    return [
        chat_schema.GroupChatRoom(
            id=chat.GroupChatRoom.id,
            name=chat.GroupChatRoom.name,
            created_at=chat.GroupChatRoom.created_at,
            updated_at=chat.GroupChatRoom.updated_at,
            image_url=chat.GroupChatRoom.image_url,
            image_name=chat.GroupChatRoom.image_name,
            unread_count=chat.unread_count or 0  # unread_countがない場合は0を設定
        )
        for chat in group_chats
    ]

async def get_not_entry_group_chat_room(db: AsyncSession, user_id: int) -> list[chat_schema.GroupChatRoom]:
    # サブクエリ: 指定されたユーザーが参加しているグループチャットルームのIDを取得
    subquery = (
        select(chat_model.GroupChatRoomUser.group_chat_room_id)
        .where(chat_model.GroupChatRoomUser.user_id == user_id)
        .where(chat_model.GroupChatRoomUser.join == True)  # joinがTrueのもののみ
    ).subquery()

    # サブクエリに含まれないグループチャットを取得
    result = await db.execute(
        select(chat_model.GroupChatRoom)
        .where(~chat_model.GroupChatRoom.id.in_(subquery))
    )
    
    # 結果を取得して Pydantic モデルに変換
    non_entry_group_chats = result.scalars().all()
    return [
        chat_schema.GroupChatRoom(
            id=chat.id,
            name=chat.name,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            image_url=chat.image_url,
            image_name=chat.image_name,
            unread_count=0  # 参加していないグループは未読数を0とする
        )
        for chat in non_entry_group_chats
    ]

async def get_users_in_group_chat_room(db: AsyncSession, group_chat_room_id: int):
    # クエリを作成して、指定されたグループチャットに参加しているユーザと関連する GroupChatRoomUser のデータを取得
    query = (
        select(user_model.User, chat_model.GroupChatRoomUser)
        .join(chat_model.GroupChatRoomUser, user_model.User.id == chat_model.GroupChatRoomUser.user_id)
        .where(chat_model.GroupChatRoomUser.group_chat_room_id == group_chat_room_id)
    )

    result = await db.execute(query)
    rows = result.all()
    
    return rows

# group_chatに参加しているユーザを退会させる
async def update_group_chat_member(db: AsyncSession, group_chat_room_id: int, user_id: str):
    # group_chat_room_id と user_id で GroupChatRoomUser を検索
    result = await db.execute(
        select(chat_model.GroupChatRoomUser)
        .where(chat_model.GroupChatRoomUser.group_chat_room_id == group_chat_room_id)
        .where(chat_model.GroupChatRoomUser.user_id == user_id)
    )
    
    group_chat_room_user = result.scalars().first()

    if group_chat_room_user:
        # join フィールドを更新
        group_chat_room_user.join = False
        group_chat_room_user.leave_date = datetime.now()
        group_chat_room_user.joined_date = None
        # 変更をコミット
        db.add(group_chat_room_user)
        await db.commit()
        await db.refresh(group_chat_room_user)
        return group_chat_room_user
    else:
        return None  # 該当するレコードがない場合

async def add_or_update_user_in_group_chat(db: AsyncSession, group_chat_room_id: int, user_ids: list[str]):
    results = []

    # 既に存在するユーザーを一度に取得
    existing_users_query = (
        select(chat_model.GroupChatRoomUser)
        .where(chat_model.GroupChatRoomUser.group_chat_room_id == group_chat_room_id)
        .where(chat_model.GroupChatRoomUser.user_id.in_(user_ids))
    )
    existing_users = await db.execute(existing_users_query)
    existing_users_dict = {user.user_id: user for user in existing_users.scalars().all()}

    for user_id in user_ids:
        if user_id in existing_users_dict:
            existing_user = existing_users_dict[user_id]
            # 既に存在する場合、joinをTrueに更新
            existing_user.join = True
            existing_user.joined_date = datetime.now()
            existing_user.leave_date = None
            db.add(existing_user)
            results.append(existing_user)
        else:
            # 存在しない場合、新しいレコードを作成して追加
            new_user = chat_model.GroupChatRoomUser(
                group_chat_room_id=group_chat_room_id,
                user_id=user_id,
                join=True,  # 初期値はTrue
                joined_date=datetime.utcnow()  # 加入日時を設定
            )
            db.add(new_user)
            results.append(new_user)

    # 一度にコミット
    await db.commit()

    # 結果を返す前にリフレッシュ
    for user in results:
        await db.refresh(user)

    return results

async def delete_group_chat_room_others(db: AsyncSession, group_chat_room_id: int):
    # グループチャットルームを取得
    result = await db.execute(
        select(chat_model.GroupChatRoom)
        .options(joinedload(chat_model.GroupChatRoom.group_messages), joinedload(chat_model.GroupChatRoom.group_chat_rooms_users))
        .filter(chat_model.GroupChatRoom.id == group_chat_room_id)
    )
    group_chat_room = result.scalars().first()

    # チャットルームが存在しない場合は404を返す
    if not group_chat_room:
        raise HTTPException(status_code=404, detail="Group chat room not found")

    # 関連するGroupMessageとGroupChatRoomUserを削除
    await db.delete(group_chat_room)
    
    # コミットしてデータベースを更新
    await db.commit()

    return {"message": "Group chat room deleted successfully"}

async def get_users_in_group_chat_room_excluding_user(
    db: AsyncSession, group_chat_room_id: int, exclude_user_id: str
) -> list[str]:
    # クエリを作成して、指定されたグループチャットに参加しているユーザを取得。ただし指定された user_id を除外。
    query = (
        select(user_model.User.id)
        .join(chat_model.GroupChatRoomUser, user_model.User.id == chat_model.GroupChatRoomUser.user_id)
        .where(chat_model.GroupChatRoomUser.group_chat_room_id == group_chat_room_id)
        .where(user_model.User.id != exclude_user_id)  # 除外条件
    )

    # クエリを実行
    result = await db.execute(query)
    
    # 結果をリストに変換
    user_ids = [row[0] for row in result.fetchall()]  # fetchallを使って全ての結果を取得

    return user_ids

async def create_unread_message(
        db: AsyncSession, create_unread_message: chat_schema.UnreadMessageCreate
) -> chat_model.UnreadMessage:
    unread_message = chat_model.UnreadMessage(**create_unread_message.dict())
    db.add(unread_message)
    await db.commit()
    await db.refresh(unread_message)
    return unread_message

async def create_unread_messages(
    db: AsyncSession, user_ids: list[str], group_chat_room_id: int, group_message_id: int
) -> None:
    try:
        unread_messages = [
            chat_model.UnreadMessage(
                group_chat_room_id=group_chat_room_id,
                user_id=user_id,
                group_message_id=group_message_id
            )
            for user_id in user_ids
        ]
        
        # add_all() を await で実行
        db.add_all(unread_messages)
        await db.flush()  # データベースに変更をフラッシュ
        await db.commit()  # トランザクションをコミット
        
    except Exception as e:
        await db.rollback()  # エラー時はロールバック
        raise e


async def get_group_chat_room(
        db: AsyncSession, group_chat_room_id: int
) -> chat_model.GroupChatRoom | None:
    result: Result = await db.execute(
        select(chat_model.GroupChatRoom).filter(chat_model.GroupChatRoom.id == group_chat_room_id)
    )
    return result.scalars().first()

async def update_time_group_chat_room(
        db: AsyncSession, update_private_chat_room: chat_schema.UpdateGroupChatRoomTime, original: chat_model.GroupChatRoom
) -> chat_model.GroupChatRoom:
    original.updated_at = update_private_chat_room.updated_at
    db.add(original)
    await db.commit()
    await db.refresh(original)
    return original

async def get_group_chat_room_user(
    db: AsyncSession, group_chat_room_id: int, user_id: str
) -> chat_model.GroupChatRoomUser | None:
    result: Result = await db.execute(
        select(chat_model.GroupChatRoomUser)
        .filter(chat_model.GroupChatRoomUser.group_chat_room_id == group_chat_room_id)
        .filter(chat_model.GroupChatRoomUser.user_id == user_id)
    )
    return result.scalars().first()

async def get_user(db: AsyncSession, id: str) -> user_model.User | None:
    result: Result = await db.execute(
        select(user_model.User).filter(user_model.User.id == id)
    )
    return result.scalars().first()

async def get_group_messages(db: AsyncSession, group_chat_room_id: int, page: int) -> list[chat_schema.GroupMessage]:
    # OFFSET計算: (ページ番号 - 1) * ページサイズ
    offset = (page - 1) * 10

    # サブクエリで各メッセージのunread_countを計算
    unread_count_subquery = (
        select(
            chat_model.UnreadMessage.group_message_id,
            func.count(chat_model.UnreadMessage.id).label("unread_count"),
        )
        .where(chat_model.UnreadMessage.group_chat_room_id == group_chat_room_id)
        .group_by(chat_model.UnreadMessage.group_message_id)
        .subquery()
    )

    # メインクエリでメッセージとunread_countを取得
    result = await db.execute(
        select(
            chat_model.GroupMessage,
            unread_count_subquery.c.unread_count,
        )
        .outerjoin(
            unread_count_subquery,
            chat_model.GroupMessage.id == unread_count_subquery.c.group_message_id,
        )
        .where(chat_model.GroupMessage.group_chat_room_id == group_chat_room_id)
        .order_by(chat_model.GroupMessage.sent_at.desc())
        .offset(offset)
        .limit(10)
    )

    # メッセージデータの取得
    messages = result.all()

    # GroupMessage型に変換
    return [
        chat_schema.GroupMessage(
            id=message.GroupMessage.id,
            group_chat_room_id=message.GroupMessage.group_chat_room_id,
            user_id=message.GroupMessage.user_id,
            sent_at=message.GroupMessage.sent_at,
            message_type=message.GroupMessage.message_type,
            content=message.GroupMessage.content,
            image_url=message.GroupMessage.image_url,
            image_name=message.GroupMessage.image_name,
            file_url=message.GroupMessage.file_url,
            file_name=message.GroupMessage.file_name,
            unread_count=message.unread_count or 0,  # 未読数がない場合は0
        )
        for message in messages
    ]

async def post_group_message(
        db: AsyncSession, group_message: chat_schema.GroupMessageCreate
) -> chat_model.GroupMessage:
    group_message = chat_model.GroupMessage(**group_message.dict())
    db.add(group_message)
    await db.commit()
    await db.refresh(group_message)

    return group_message
    
async def get_users_not_in_group_chat(db: AsyncSession, group_chat_room_id: int):
    # サブクエリで、指定されたグループチャットに既に参加しているユーザーのIDを取得
    subquery = (
        select(chat_model.GroupChatRoomUser.user_id)
        .where(chat_model.GroupChatRoomUser.group_chat_room_id == group_chat_room_id)
        .where(chat_model.GroupChatRoomUser.join == True)
        .subquery()
    )

    # そのユーザーIDを除外して、ユーザーデータを取得
    result = await db.execute(
        select(user_model.User)
        .where(~user_model.User.id.in_(subquery))
    )
    
    # 結果をリストとして返す
    return result.scalars().all()

async def get_group_chat_rooms(db: AsyncSession) -> list[chat_model.GroupChatRoom]:
    result = await db.execute(select(chat_model.GroupChatRoom))
    return result.scalars().all()

async def get_group_chat_users_count(
        db: AsyncSession,
        group_chat_room_id: int
) -> int:
    # クエリを作成して、条件に一致するレコードの個数を取得
    result = await db.execute(
        select(func.count())
        .select_from(chat_model.GroupChatRoomUser)
        .where(chat_model.GroupChatRoomUser.group_chat_room_id == group_chat_room_id)
        .where(chat_model.GroupChatRoomUser.join == True)  # joinがTrueのもの
    )
    
    # 結果を取得
    count = result.scalar()
    
    return count
    
async def unread_group_messages_update(
    db: AsyncSession,
    group_chat_room_id: int,
    user_id: str
) -> list[chat_schema.GroupMessageUnreadUpdate]:
    # UnreadMessageからgroup_message_idを取得
    result = await db.execute(
        select(chat_model.UnreadMessage.group_message_id)
        .where(chat_model.UnreadMessage.group_chat_room_id == group_chat_room_id)
        .where(chat_model.UnreadMessage.user_id == user_id)
    )
    group_message_ids = result.scalars().all()

    if not group_message_ids:
        return []

    # UnreadMessageから該当するレコードを削除
    await db.execute(
        delete(chat_model.UnreadMessage)
        .where(chat_model.UnreadMessage.group_chat_room_id == group_chat_room_id)
        .where(chat_model.UnreadMessage.user_id == user_id)
    )
    await db.commit()

    # 取得したgroup_message_idをGroupMessageUnreadUpdate形式で返す
    unread_updates = [
        chat_schema.GroupMessageUnreadUpdate(group_message_id=message_id)
        for message_id in group_message_ids
    ]

    return unread_updates

async def message_unread_update_websocket(
    db: AsyncSession,
    group_chat_room_id: int,
    user_id: str,
    group_message_id: int
) -> None:
    # 削除対象のレコードを確認するためにselectを実行
    result = await db.execute(
        select(chat_model.UnreadMessage)
        .where(chat_model.UnreadMessage.group_chat_room_id == group_chat_room_id)
        .where(chat_model.UnreadMessage.user_id == user_id)
        .where(chat_model.UnreadMessage.group_message_id == group_message_id)
    )
    unread_messages = result.scalars().all()

    # レコードが見つかったか確認
    if unread_messages:
        # UnreadMessageの削除
        await db.execute(
            delete(chat_model.UnreadMessage)
            .where(chat_model.UnreadMessage.group_chat_room_id == group_chat_room_id)
            .where(chat_model.UnreadMessage.user_id == user_id)
            .where(chat_model.UnreadMessage.group_message_id == group_message_id)
        )
        # 変更をデータベースに反映
        await db.commit()
    else:
        print("対象のUnreadMessageが見つかりませんでした。")
    
async def get_group_chat_room_ids(db: AsyncSession, user_id: str) -> list[int]:
    """
    指定されたユーザーが参加中のグループチャットIDの一覧を取得します。

    Args:
        db (AsyncSession): 非同期セッションインスタンス
        user_id (str): ユーザーID

    Returns:
        list[int]: グループチャットIDのリスト
    """
    # クエリを作成して実行
    result = await db.execute(
        select(chat_model.GroupChatRoomUser.group_chat_room_id)
        .where(chat_model.GroupChatRoomUser.user_id == user_id)
    )
    # 結果をリスト形式で取得
    group_chat_room_ids = [row[0] for row in result.fetchall()]
    return group_chat_room_ids

async def get_unread_message_count(db: AsyncSession, chat_room_ids: list[int], user_id: str) -> int:
    """
    指定されたチャットルームとユーザーの未読メッセージ総数を取得します。

    Args:
        db (AsyncSession): 非同期セッションインスタンス
        chat_room_ids (list[int]): チャットルームIDのリスト
        user_id (str): ユーザーID

    Returns:
        int: 未読メッセージの総数
    """
    if not chat_room_ids:
        return 0  # チャットルームが存在しない場合、未読メッセージ数は0

    # 未読メッセージ数をカウント
    result = await db.execute(
        select(func.count(chat_model.UnreadMessage.id))
        .where(chat_model.UnreadMessage.group_chat_room_id.in_(chat_room_ids))
        .where(chat_model.UnreadMessage.user_id == user_id)
    )
    # 総数を取得
    total_unread_messages = result.scalar() or 0
    return total_unread_messages