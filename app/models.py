from pydantic import BaseModel, Field


class InvoiceFields(BaseModel):
    invoice_number: str | None = None
    invoice_date: str | None = None
    vendor_name: str | None = None
    customer_name: str | None = None
    total_amount: float | None = None
    tax_amount: float | None = None
    currency: str | None = None


class AuditResult(BaseModel):
    file_name: str
    document_type: str
    extracted_fields: InvoiceFields
    missing_fields: list[str]
    inconsistencies: list[str]
    risk_level: str
    risk_reasons: list[str]
    processing_status: str
    created_at: str


class QueryRequest(BaseModel):
    question: str
    document_id: str | None = None
    top_k: int = Field(default=3, ge=1, le=5)
