from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

import api.schemas.report as report_schema
import api.cruds.report as report_crud
from api.db import get_db

router = APIRouter()


@router.get("/reports", response_model=List[report_schema.ReportWithAdditionalInfo])
async def get_reports(user_id: str, page: int = 1, db: AsyncSession = Depends(get_db)):
    """
    指定されたユーザー宛のレポートを取得するエンドポイント
    """
    return await report_crud.get_reports(db=db, user_id=user_id, page=page)


@router.post("/reports", response_model=report_schema.Report)
async def create_report(
    report_body: report_schema.ReportCreate, db: AsyncSession = Depends(get_db)
):
    """
    新しいレポートを作成するエンドポイント
    """
    return await report_crud.create_report(db=db, report_create=report_body)


@router.get("/reports/{report_id}", response_model=report_schema.ReportWithAdditionalInfo)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    """
    特定のレポートを取得するエンドポイント
    """
    report = await report_crud.get_report(db=db, id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.delete("/reports/{report_id}", response_model=None)
async def delete_report(report_id: int, db: AsyncSession = Depends(get_db)):
    """
    指定されたレポートを削除するエンドポイント
    """
    report = await report_crud.get_report(db=db, id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    await report_crud.delete_report(db=db, original=report)


@router.put("/reports/{report_id}/roger", response_model=None)
async def update_rogers(report_id: int, roger_value: bool, db: AsyncSession = Depends(get_db)):
    """
    レポートの`roger`値を更新するエンドポイント
    """
    report = await report_crud.get_report(db=db, id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    await report_crud.update_rogers(db=db, report_id=report_id, roger_value=roger_value)