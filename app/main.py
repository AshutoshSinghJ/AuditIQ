from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import ValidationError
from pymongo.errors import PyMongoError

from app.audit_service import create_audit_result
from app.database import get_latest_audits, insert_audit_result
from app.groq_service import extract_invoice_fields
from app.models import InvoiceFields
from app.pdf_service import extract_text_from_pdf


app = FastAPI(title="AuditIQ - AI-Powered Document Audit Prototype")


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
