from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
import base64
from datetime import datetime

import api.models.chat as chat_model
import api.models.user as user_model
import api.schemas.chat as chat_schema

async def get_or_create_private_chat_room(db: AsyncSession, user1_id:int, user2_id:int) -> chat_schema.PrivateChatRoom:
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
        private_chat_room = chat_model.PrivateChatRoom()
        db.add(private_chat_room)
        await db.flush() # chat_room.idを取得するためにflush

        db.add_all([
            chat_model.PrivateChatRoomUser(private_chat_room_id=private_chat_room.id, user_id=user1_id),
            chat_model.PrivateChatRoomUser(private_chat_room_id=private_chat_room.id, user_id=user2_id)
        ])
        await db.commit()
        await db.refresh(private_chat_room)
    
    return private_chat_room

async def get_private_messages(db: AsyncSession, private_chat_room_id: int) -> list[chat_model.PrivateMessage]:
    result = await db.execute(
        select(chat_model.PrivateMessage)
        .where(chat_model.PrivateMessage.private_chat_room_id == private_chat_room_id)
        .order_by(chat_model.PrivateMessage.sent_at)
    )
    messages = result.scalars().all()
    
    # メッセージの画像データをbase64エンコード
    for message in messages:
        if message.image_data:
            message.image_data = base64.b64encode(message.image_data).decode('utf-8')
        if message.file_data:
            message.file_data = base64.b64encode(message.file_data).decode('utf-8')
    
    return messages

async def post_private_message(
        db: AsyncSession, private_message: chat_schema.PrivateMessageCreate
) -> chat_model.PrivateMessage:
    private_message = chat_model.PrivateMessage(**private_message.dict())
    db.add(private_message)
    await db.commit()
    await db.refresh(private_message)
    return private_message

async def create_group_chat(
        db: AsyncSession, group_chat_create: chat_schema.GroupChatRoomCreate, member_ids: list[int]
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

async def get_entry_group_chat_room(db: AsyncSession, user_id: int) ->  list[chat_model.GroupChatRoom]:
    # クエリを作成して、指定されたユーザが参加しているグループチャットの全データを取得する
    result = await db.execute(
        select(chat_model.GroupChatRoom)
        .join(chat_model.GroupChatRoomUser, chat_model.GroupChatRoom.id == chat_model.GroupChatRoomUser.group_chat_room_id)
        .where(chat_model.GroupChatRoomUser.user_id == user_id)
        .where(chat_model.GroupChatRoomUser.join == True)  # joinがTrueのもののみ
    )
    
    # 取得した結果をリストに変換
    group_chats = result.scalars().all()
    return group_chats

async def get_not_entry_group_chat_room(db: AsyncSession, user_id: int) ->  list[chat_model.GroupChatRoom]:
    # サブクエリを作成して、指定されたユーザが参加しているグループチャットのIDを取得
    subquery = (
        select(chat_model.GroupChatRoomUser.group_chat_room_id)
        .where(chat_model.GroupChatRoomUser.user_id == user_id)
        .where(chat_model.GroupChatRoomUser.join == True)  # joinがTrueのもののみ
    ).subquery()
    
    # 参加していないグループチャットを取得する
    result = await db.execute(
        select(chat_model.GroupChatRoom)
        .where(~chat_model.GroupChatRoom.id.in_(subquery))
    )
    
    # 取得した結果をリストに変換
    non_entry_group_chats = result.scalars().all()
    return non_entry_group_chats

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

async def get_group_messages(db: AsyncSession, group_chat_room_id: int) -> list[chat_model.GroupMessage]:
    result = await db.execute(
        select(chat_model.GroupMessage)
        .where(chat_model.GroupMessage.group_chat_room_id == group_chat_room_id)
        .order_by(chat_model.GroupMessage.sent_at)
    )
    messages = result.scalars().all()
    
    # メッセージの画像データをbase64エンコード
    for message in messages:
        if message.image_data:
            message.image_data = base64.b64encode(message.image_data).decode('utf-8')
        if message.file_data:
            message.file_data = base64.b64encode(message.file_data).decode('utf-8')
    
    return messages

async def post_group_message(
        db: AsyncSession, group_message: chat_schema.GroupMessageCreate
) -> chat_model.GroupMessage:
    group_message = chat_model.GroupMessage(**group_message.dict())
    db.add(group_message)
    await db.commit()
    await db.refresh(group_message)
    return group_message

async def update_group_chat_member(db: AsyncSession, group_chat_room_id: int, user_id: int):
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

async def add_or_update_user_in_group_chat(db: AsyncSession, group_chat_room_id: int, user_ids: list[int]):
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
