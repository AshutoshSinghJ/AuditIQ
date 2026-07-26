# AuditIQ - AI-Powered Document Audit Prototype

AuditIQ is a beginner-friendly backend-only FastAPI project that audits text-based invoice PDFs.

It extracts invoice text with PyMuPDF, asks Groq to return structured JSON, validates the JSON with Pydantic, checks simple audit rules in Python, stores the result in MongoDB, and returns the saved audit result as JSON.

## Technology Stack

- Python
- FastAPI
- Groq API
- PyMuPDF
- Pydantic
- MongoDB with PyMongo
- FastAPI Swagger UI for testing

## Workflow

```text
Upload invoice PDF
-> Extract text using PyMuPDF
-> Send text to Groq
-> Receive structured JSON
-> Validate it using Pydantic
-> Check missing fields and inconsistencies in Python
-> Calculate High, Medium or Low risk
-> Store the result in MongoDB
-> Return the result as JSON
```

## Folder Structure

```text
auditiq/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── pdf_service.py
│   ├── groq_service.py
│   └── audit_service.py
├── examples/
│   ├── high_risk_response.json
│   ├── low_risk_response.json
│   └── medium_risk_response.json
├── .env.example
├── requirements.txt
├── sample_invoice.pdf
├── sample_invoice.txt
└── README.md
```

## Extracted Fields

Groq is asked to return only these fields:

```json
{
  "invoice_number": null,
  "invoice_date": null,
  "vendor_name": null,
  "customer_name": null,
  "total_amount": null,
  "tax_amount": null,
  "currency": null
}
```

Groq must return valid JSON only, use `null` for missing values, avoid markdown, and avoid inventing values.

## Mandatory Fields

These fields are mandatory:

- `invoice_number`
- `invoice_date`
- `vendor_name`
- `total_amount`
- `currency`

A field is treated as missing when it is `None`, empty, or only whitespace.

## Inconsistency Rules

These checks are done in Python, not by Groq:

- `total_amount` is negative.
- `tax_amount` is greater than `total_amount`.
- `currency` is not exactly three alphabetic characters.

## Risk Rules

- `High`: Two or more mandatory fields are missing, the total is negative, or tax is greater than total.
- `Medium`: Exactly one mandatory field is missing or currency format is invalid.
- `Low`: No mandatory fields are missing and no inconsistencies exist.

Groq does not decide the final risk level.

## Installation

```bash
cd auditiq
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

On macOS or Linux, activate the virtual environment with:

```bash
source venv/bin/activate
```

## Environment Setup

Create a `.env` file from `.env.example`:

```bash
copy .env.example .env
```

On macOS or Linux:

```bash
cp .env.example .env
```

Then fill in:

```text
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_groq_model
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=auditiq
```

Do not hardcode secrets in the source code.

## MongoDB Setup

Install and start MongoDB locally.

The app uses:

```text
Database: auditiq
Collection: audit_results
```

No extra MongoDB setup is required. The database and collection are created automatically when the first result is inserted.

## Run Command

```bash
uvicorn app.main:app --reload
```

## Swagger Testing

Open:

```text
http://127.0.0.1:8000/docs
```

Use `POST /audit` to upload `sample_invoice.pdf`.

Use `GET /audits` to view the latest 20 saved audit results.

## API Endpoints

### POST /audit

Accepts one PDF invoice file.

Main behavior:

1. Rejects non-PDF files.
2. Extracts text from all PDF pages.
3. Returns an error if the PDF has no readable text.
4. Sends the text to Groq.
5. Parses the Groq response with `json.loads()`.
6. Validates the result with `InvoiceFields`.
7. Finds missing mandatory fields.
8. Detects simple inconsistencies in Python.
9. Calculates the risk level in Python.
10. Stores the result in MongoDB.
11. Returns the stored result with `_id` converted to a string.

### GET /audits

Returns the latest 20 saved audit results from MongoDB with ObjectIds converted to strings.

## Sample Invoice

The project includes:

- `sample_invoice.pdf`
- `sample_invoice.txt`

Sample invoice text:

```text
INVOICE

Invoice Number: INV-1001
Invoice Date: 2026-07-20

Vendor Name: Bright Office Supplies
Customer Name: Apex Learning Center

Subtotal: 900.00
Tax Amount: 90.00
Total Amount: 990.00
Currency: USD

Payment Terms: Due within 15 days
```

## Example Low-Risk Response

```json
{
  "_id": "64f2a7b2c8e4a12345678901",
  "file_name": "sample_invoice.pdf",
  "document_type": "invoice",
  "extracted_fields": {
    "invoice_number": "INV-1001",
    "invoice_date": "2026-07-20",
    "vendor_name": "Bright Office Supplies",
    "customer_name": "Apex Learning Center",
    "total_amount": 990.0,
    "tax_amount": 90.0,
    "currency": "USD"
  },
  "missing_fields": [],
  "inconsistencies": [],
  "risk_level": "Low",
  "risk_reasons": [],
  "processing_status": "completed",
  "created_at": "2026-07-27T00:00:00+00:00"
}
```

## Example Medium-Risk Response

```json
{
  "_id": "64f2a7b2c8e4a12345678902",
  "file_name": "medium_invoice.pdf",
  "document_type": "invoice",
  "extracted_fields": {
    "invoice_number": "INV-2001",
    "invoice_date": "2026-07-20",
    "vendor_name": "Bright Office Supplies",
    "customer_name": "Apex Learning Center",
    "total_amount": 990.0,
    "tax_amount": 90.0,
    "currency": "US"
  },
  "missing_fields": [],
  "inconsistencies": [
    "currency is not exactly three alphabetic characters"
  ],
  "risk_level": "Medium",
  "risk_reasons": [
    "Currency format is invalid"
  ],
  "processing_status": "completed",
  "created_at": "2026-07-27T00:00:00+00:00"
}
```

## Example High-Risk Response

```json
{
  "_id": "64f2a7b2c8e4a12345678903",
  "file_name": "high_invoice.pdf",
  "document_type": "invoice",
  "extracted_fields": {
    "invoice_number": null,
    "invoice_date": null,
    "vendor_name": "Bright Office Supplies",
    "customer_name": "Apex Learning Center",
    "total_amount": 990.0,
    "tax_amount": 1200.0,
    "currency": "USD"
  },
  "missing_fields": [
    "invoice_number",
    "invoice_date"
  ],
  "inconsistencies": [
    "tax_amount is greater than total_amount"
  ],
  "risk_level": "High",
  "risk_reasons": [
    "Two or more mandatory fields are missing",
    "Tax amount is greater than total amount"
  ],
  "processing_status": "completed",
  "created_at": "2026-07-27T00:00:00+00:00"
}
```

## Basic Errors Handled

- Non-PDF upload
- Invalid PDF
- PDF with no readable text
- Groq API failure
- Invalid Groq JSON
- MongoDB insertion failure

The API returns simple FastAPI HTTP errors without exposing secrets or stack traces.

## File-by-File Explanation

- `app/__init__.py`: Marks `app` as a Python package.
- `app/main.py`: Defines the FastAPI app and the two endpoints.
- `app/models.py`: Contains the Pydantic models used for invoice fields and audit results.
- `app/database.py`: Connects to MongoDB and provides simple insert and find functions.
- `app/pdf_service.py`: Extracts readable text from text-based PDFs using PyMuPDF.
- `app/groq_service.py`: Sends invoice text to Groq and parses the JSON response.
- `app/audit_service.py`: Finds missing fields, detects inconsistencies, calculates risk, and builds the audit result.
- `.env.example`: Shows the required environment variables without secrets.
- `requirements.txt`: Lists the Python packages required to run the project.
- `sample_invoice.pdf`: A sample text-based invoice PDF for Swagger testing.
- `sample_invoice.txt`: The same sample invoice in plain text.
- `examples/*.json`: Example Low, Medium, and High risk API responses.
- `README.md`: Explains setup, workflow, endpoints, examples, limitations, and interview notes.

## Limitations

- Supports only text-based invoice PDFs.
- Does not support scanned PDFs or OCR.
- Does not include authentication.
- Does not include a frontend.
- Does not use RAG, embeddings, vector databases, Docker, Redis, background jobs, microservices, or cloud deployment.
- Accuracy depends on the quality of the extracted PDF text and the Groq response.
- Only simple Python audit rules are implemented.

## Interview Checklist

Before presenting this project, understand:

- What FastAPI is and how Swagger UI helps test APIs.
- How `UploadFile` receives a PDF upload.
- Why non-PDF files are rejected.
- How PyMuPDF extracts text from text-based PDFs.
- Why scanned PDFs need OCR and why this project does not include OCR.
- What Groq does in this project.
- Why the Groq prompt asks for JSON only.
- Why `json.loads()` is used after receiving the Groq response.
- How Pydantic validates the extracted fields.
- Which fields are mandatory and how missing fields are detected.
- Why inconsistency checks are done in Python instead of Groq.
- How High, Medium, and Low risk levels are calculated.
- How MongoDB stores one audit result document.
- Why MongoDB ObjectIds must be converted to strings before returning JSON.
- What each file in the project does.
- How environment variables keep secrets out of source code.
- What limitations you would mention honestly in an interview.
