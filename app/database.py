import os

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "auditiq")

client = MongoClient(MONGODB_URI)
database = client[DATABASE_NAME]
audit_collection = database["audit_results"]
document_collection = database["documents"]


def insert_audit_result(audit_result: dict) -> str:
    result = audit_collection.insert_one(audit_result)
    return str(result.inserted_id)


def get_latest_audits(limit: int = 20) -> list[dict]:
    audits = audit_collection.find().sort("_id", -1).limit(limit)
    return [convert_object_id(audit) for audit in audits]


def insert_document(document: dict) -> str:
    result = document_collection.insert_one(document)
    return str(result.inserted_id)


def get_latest_documents(limit: int = 20) -> list[dict]:
    documents = document_collection.find().sort("_id", -1).limit(limit)
    return [summarize_document(document) for document in documents]


def get_documents_for_query(document_id: str | None = None) -> list[dict]:
    if not document_id:
        return list(document_collection.find())

    try:
        object_id = ObjectId(document_id)
    except InvalidId:
        return []

    return list(document_collection.find({"_id": object_id}))


def convert_object_id(document: dict) -> dict:
    document["_id"] = str(document["_id"])
    return document


def summarize_document(document: dict) -> dict:
    return {
        "_id": str(document["_id"]),
        "file_name": document["file_name"],
        "document_type": document["document_type"],
        "chunk_count": document["chunk_count"],
        "processing_status": document["processing_status"],
        "created_at": document["created_at"],
    }
