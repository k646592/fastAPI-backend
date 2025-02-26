from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from api.db import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)  # ID
    content = Column(String(1024), nullable=False)  # 投稿内容 (VARCHAR(1024))
    created_at = Column(DateTime, nullable=False)  # 作成日時
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False)  # 投稿者ID
    user_name = Column(String(256), nullable=False)  # 投稿者名
    recipient_user_id = Column(String(32), ForeignKey("users.id"), nullable=False)  # 送信先ユーザーID
    recipient_user_name = Column(String(256), nullable=False)  # 送信先ユーザー名
    roger = Column(Boolean, default=False)  # 確認済みフラグ

    # Users テーブルとのリレーション
    user = relationship("User", foreign_keys=[user_id], back_populates="sent_reports")
    recipient_user = relationship("User", foreign_keys=[recipient_user_id], back_populates="received_reports")