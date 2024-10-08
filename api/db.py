from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DB_URL = os.getenv("DB_URL", "mysql+pymysql://root@db:3306/demo?charset=utf8")
ASYNC_DB_URL = os.getenv("ASYNC_DB_URL", "mysql+aiomysql://root@db:3306/demo?charset=utf8")

async_engine = create_async_engine(
    ASYNC_DB_URL, 
    echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
)
async_session = sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine,
    class_=AsyncSession
)

Base = declarative_base()

async def get_db():
    """DBセッションを取得する非同期ジェネレータ関数"""
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            print(f"Database session error: {e}")
            raise  # 必要に応じて例外を再スローして呼び出し側でハンドリング
