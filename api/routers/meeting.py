from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

import api.cruds.meeting as meeting_crud
from api.db import get_db

import api.schemas.meeting as meeting_schema

router = APIRouter()

@router.get("/meetings", response_model=list[meeting_schema.MeetingWithUserName])
async def list_meetings(db: AsyncSession = Depends(get_db)):
    return await meeting_crud.get_meetings(db)

@router.get("meetings/{id}", response_model=meeting_schema.GetMeetingMainText)
async def get_meeting(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    meeting = await meeting_crud.get_meeting(db, id=id)
    # meetingt_dataオブジェクトを作成
    meeting_data = {
        "main_text": meeting.main_text,
        "id": meeting.id,
    }
    meeting_get = meeting_schema.GetMeetingMainText(**meeting_data)

    return meeting_get

@router.post("/meetings", response_model=meeting_schema.MeetingCreateResponse)
async def create_meeting(
    meeting_body: meeting_schema.MeetingCreate, db: AsyncSession = Depends(get_db)
):
    new_meeting = await meeting_crud.create_meeting(db, meeting_body)
    return new_meeting

@router.patch("/meetings/{id}", response_model=meeting_schema.MeetingUpdateResponse)
async def update_event(
    id: int, 
    meeting_body: meeting_schema.MeetingUpdate, 
    db: AsyncSession = Depends(get_db)
):
    meeting = await meeting_crud.get_meeting(db, id=id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Event not found")
    
    updated_meeting = await meeting_crud.update_meeting(db, meeting_body, original=meeting)
    return updated_meeting

@router.patch("/update_main_text/{id}", response_model=meeting_schema.MeetingUpdateMainTextResponse)
async def update_main_text(
    id: int,
    meeting_body: meeting_schema.MeetingUpdateMainText,
    db: AsyncSession = Depends(get_db)
):
    meeting = await meeting_crud.get_meeting(db, id=id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    updated_meeting = await meeting_crud.update_meeting_main_text(db, meeting_body, original=meeting)
    return updated_meeting

@router.delete("/meetings/{id}", response_model=None)
async def delete_meeting(id: int, db: AsyncSession = Depends(get_db)):
    meeting = await meeting_crud.get_meeting(db, id=id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return await meeting_crud.delete_meeting(db, original=meeting)