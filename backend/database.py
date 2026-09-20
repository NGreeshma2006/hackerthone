import os

from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

SQLALCHEMY_DATABASE_URL = "sqlite:///./backend/stockstory.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

mongo_uri = os.getenv("MONGO_URI")
mongo_db_name = os.getenv("MONGO_DB_NAME", "stockstory")

mongo_client = None
mongo_db = None
mongo_checked = False



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_mongo_db():
    """Return the configured MongoDB database, or None when unavailable."""
    global mongo_client, mongo_db, mongo_checked
    if mongo_checked or not mongo_uri:
        return mongo_db
    mongo_checked = True
    try:
        from pymongo import MongoClient
        # Fail quickly when Atlas/DNS is unavailable so the API can use its
        # SQLite fallback instead of leaving requests hanging.
        mongo_client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000,
            socketTimeoutMS=2000,
        )
        mongo_client.admin.command("ping")
        mongo_db = mongo_client[mongo_db_name]
    except Exception:
        if mongo_client is not None:
            mongo_client.close()
        mongo_client = None
        mongo_db = None
    return mongo_db


