from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import ValidationError
from pymongo.errors import PyMongoError

from app.audit_service import create_audit_result
from app.database import (
    get_documents_for_query,
    get_latest_audits,
    get_latest_documents,
    insert_audit_result,
    insert_document,
)
from app.document_service import create_document_record, find_relevant_chunks
from app.groq_service import answer_document_question, extract_invoice_fields
from app.models import InvoiceFields, QueryRequest
from app.pdf_service import extract_text_from_pdf


app = FastAPI(title="AuditIQ - AI-Powered Invoice Audit & Document Query API")


@app.post("/audit")
async def audit_invoice(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    pdf_bytes = await file.read()

    try:
        extracted_text = extract_text_from_pdf(pdf_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not extracted_text:
        raise HTTPException(status_code=400, detail="PDF has no readable text.")

    try:
        groq_data = extract_invoice_fields(extracted_text)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        invoice_fields = InvoiceFields(**groq_data)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail="Groq JSON did not match the invoice schema.") from exc

    audit_result = create_audit_result(file.filename, invoice_fields)

    try:
        inserted_id = insert_audit_result(audit_result)
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail="Could not save audit result.") from exc

    audit_result["_id"] = inserted_id
    return audit_result


@app.get("/audits")
def list_audits():
    try:
        return get_latest_audits()
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail="Could not read audit results.") from exc


@app.post("/documents")
async def upload_document(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    pdf_bytes = await file.read()

    try:
        extracted_text = extract_text_from_pdf(pdf_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not extracted_text:
        raise HTTPException(status_code=400, detail="PDF has no readable text.")

    document = create_document_record(file.filename, extracted_text)

    if document["chunk_count"] == 0:
        raise HTTPException(status_code=400, detail="Document text could not be chunked.")

    try:
        inserted_id = insert_document(document)
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail="Could not save document.") from exc

    return {
        "_id": inserted_id,
        "file_name": document["file_name"],
        "document_type": document["document_type"],
        "chunk_count": document["chunk_count"],
        "processing_status": document["processing_status"],
        "created_at": document["created_at"],
    }


@app.get("/documents")
def list_documents():
    try:
        return get_latest_documents()
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail="Could not read documents.") from exc


@app.post("/query")
def query_document(query: QueryRequest):
    if not query.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        documents = get_documents_for_query(query.document_id)
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail="Could not read documents.") from exc

    if not documents:
        raise HTTPException(status_code=404, detail="No matching documents found.")

    relevant_chunks = find_relevant_chunks(query.question, documents, query.top_k)

    if not relevant_chunks:
        raise HTTPException(status_code=404, detail="No relevant document context found.")

    try:
        answer = answer_document_question(query.question, relevant_chunks)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "question": query.question,
        "answer": answer,
        "sources": relevant_chunks,
    }
