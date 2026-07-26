import os

from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "auditiq")

client = MongoClient(MONGODB_URI)
database = client[DATABASE_NAME]
audit_collection = database["audit_results"]


def insert_audit_result(audit_result: dict) -> str:
    result = audit_collection.insert_one(audit_result)
    return str(result.inserted_id)


def get_latest_audits(limit: int = 20) -> list[dict]:
    audits = audit_collection.find().sort("_id", -1).limit(limit)
    return [convert_object_id(audit) for audit in audits]


def convert_object_id(document: dict) -> dict:
    document["_id"] = str(document["_id"])
    return document
