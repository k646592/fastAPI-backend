from sqlalchemy import create_engine
import os
import logging
from sqlalchemy.exc import SQLAlchemyError

from api.models.board import Base
from api.models.event import Base
from api.models.attendance import Base
from api.models.user import Base
from api.models.chat import Base
from api.models.meeting import Base
from api.models.door_state_manager import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_URL = os.getenv("DB_URL", "mysql+pymysql://root@db:3306/demo?charset=utf8")
engine = create_engine(DB_URL, echo=True)

def reset_database():
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Dropped all tables successfully.")
        Base.metadata.create_all(bind=engine)
        logger.info("Created all tables successfully.")
    except SQLAlchemyError as e:
        logger.error(f"An error occurred during the database reset: {e}")


if __name__ == "__main__":
    reset_database()