from sqlalchemy import select, func, delete
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

import api.models.user as user_model
import api.models.report as report_model
import api.schemas.report as report_schema

async def get_reports(db: AsyncSession, user_id: str, page: int) -> list[report_model.Report]:
    offset = (page - 1) * 10

    result = await db.execute(
        select(
            report_model.Report,
        )
        .options(joinedload(report_model.Report.user))
        .filter(
            (report_model.Report.recipient_user_id == user_id) |  # 受信先がログイン中のユーザー
            (report_model.Report.user_id == user_id)  # 送信者がログイン中のユーザー
        )
        .order_by(report_model.Report.created_at.desc())  # 日付の降順
        .offset(offset)  # ページングの開始位置
        .limit(10)  # 1ページあたりの件数
    )
    reports = result.fetchall()

    return [
        report_schema.ReportWithAdditionalInfo(
            id=report.Report.id,
            content=report.Report.content,
            created_at=report.Report.created_at,
            user_id=report.Report.user_id,
            user_name=report.Report.user.name if report.Report.user else None,
            recipient_user_id=report.Report.recipient_user_id,
            recipient_user_name=report.Report.recipient_user_name,
            roger=report.Report.roger,
        )
        for report in reports
    ]

async def get_user(db: AsyncSession, user_id: str) -> user_model.User | None:
    result: Result = await db.execute(
        select(user_model.User).filter(user_model.User.id == user_id)
    )
    return result.scalars().first()

async def create_report(
        db: AsyncSession, report_create: report_schema.ReportCreate
) -> report_model.Report:
    report = report_model.Report(**report_create.dict())
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report

async def get_report(db: AsyncSession, id: int) -> report_model.Report | None:
    result: Result = await db.execute(
        select(report_model.Report).filter(report_model.Report.id == id)
    )
    return result.scalars().first()

async def delete_report(db: AsyncSession, original: report_model.Report) -> None:
    await db.delete(original)
    await db.commit()

async def update_rogers(db: AsyncSession, report_id: int, roger_value: bool) -> None:
    """
    レポートのroger値を更新する
    """
    result: Result = await db.execute(
        select(report_model.Report).filter(report_model.Report.id == report_id)
    )
    report = result.scalars().first()
    if report:
        report.roger = roger_value
        db.add(report)
        await db.commit()
        await db.refresh(report)