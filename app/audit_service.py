from datetime import datetime, timezone

from app.models import InvoiceFields


MANDATORY_FIELDS = [
    "invoice_number",
    "invoice_date",
    "vendor_name",
    "total_amount",
    "currency",
]


def find_missing_fields(fields: InvoiceFields) -> list[str]:
    missing_fields = []

    for field_name in MANDATORY_FIELDS:
        value = getattr(fields, field_name)

        if value is None:
            missing_fields.append(field_name)
        elif isinstance(value, str) and not value.strip():
            missing_fields.append(field_name)

    return missing_fields


def find_inconsistencies(fields: InvoiceFields) -> list[str]:
    inconsistencies = []

    if fields.total_amount is not None and fields.total_amount < 0:
        inconsistencies.append("total_amount is negative")

    if (
        fields.tax_amount is not None
        and fields.total_amount is not None
        and fields.tax_amount > fields.total_amount
    ):
        inconsistencies.append("tax_amount is greater than total_amount")

    if fields.currency is not None and not is_valid_currency(fields.currency):
        inconsistencies.append("currency is not exactly three alphabetic characters")

    return inconsistencies


def is_valid_currency(currency: str) -> bool:
    return len(currency) == 3 and currency.isalpha()


def calculate_risk(missing_fields: list[str], inconsistencies: list[str]) -> tuple[str, list[str]]:
    risk_reasons = []

    has_negative_total = "total_amount is negative" in inconsistencies
    has_tax_greater_than_total = "tax_amount is greater than total_amount" in inconsistencies
    has_invalid_currency = "currency is not exactly three alphabetic characters" in inconsistencies

    if len(missing_fields) >= 2:
        risk_reasons.append("Two or more mandatory fields are missing")

    if has_negative_total:
        risk_reasons.append("Total amount is negative")

    if has_tax_greater_than_total:
        risk_reasons.append("Tax amount is greater than total amount")

    if risk_reasons:
        return "High", risk_reasons

    if len(missing_fields) == 1:
        risk_reasons.append("Exactly one mandatory field is missing")

    if has_invalid_currency:
        risk_reasons.append("Currency format is invalid")

    if risk_reasons:
        return "Medium", risk_reasons

    return "Low", []


def create_audit_result(file_name: str, fields: InvoiceFields) -> dict:
    missing_fields = find_missing_fields(fields)
    inconsistencies = find_inconsistencies(fields)
    risk_level, risk_reasons = calculate_risk(missing_fields, inconsistencies)

    return {
        "file_name": file_name,
        "document_type": "invoice",
        "extracted_fields": fields.model_dump(),
        "missing_fields": missing_fields,
        "inconsistencies": inconsistencies,
        "risk_level": risk_level,
        "risk_reasons": risk_reasons,
        "processing_status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
