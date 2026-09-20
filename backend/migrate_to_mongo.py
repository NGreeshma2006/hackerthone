import argparse
import os
from datetime import datetime

from dotenv import load_dotenv
from pymongo import MongoClient

from backend.database import SessionLocal
from backend.models.models import (
    BusinessSetting,
    Product,
    ProductAlias,
    StockTransaction,
    UnitConversion,
)


def model_document(record):
    document = {}
    for column in record.__table__.columns:
        value = getattr(record, column.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        document[column.name] = value
    return document


def migrate(replace=False):
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI")
    database_name = os.getenv("MONGO_DB_NAME", "stockstory")
    if not mongo_uri or "YOUR_PASSWORD" in mongo_uri or "<" in mongo_uri:
        raise RuntimeError("Set a valid Atlas password in MONGO_URI before migrating.")

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    mongo_database = client[database_name]
    sqlite_database = SessionLocal()

    collections = {
        "products": Product,
        "stock_transactions": StockTransaction,
        "product_aliases": ProductAlias,
        "unit_conversions": UnitConversion,
        "business_settings": BusinessSetting,
    }
    counts = {}
    try:
        for collection_name, model in collections.items():
            documents = [model_document(record) for record in sqlite_database.query(model).all()]
            if collection_name not in mongo_database.list_collection_names():
                mongo_database.create_collection(collection_name)
            collection = mongo_database[collection_name]
            if replace:
                collection.delete_many({})
            if documents:
                collection.bulk_write(
                    [
                        __import__("pymongo").UpdateOne(
                            {"id": document["id"]},
                            {"$set": document},
                            upsert=True,
                        )
                        for document in documents
                    ]
                )
            counts[collection_name] = len(documents)
    finally:
        sqlite_database.close()
        client.close()

    for collection_name, count in counts.items():
        print(f"{collection_name}: {count}")
    print(f"Migrated to MongoDB database: {database_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy StockStory data from SQLite to MongoDB Atlas.")
    parser.add_argument("--replace", action="store_true", help="Clear target collections before copying.")
    args = parser.parse_args()
    migrate(replace=args.replace)