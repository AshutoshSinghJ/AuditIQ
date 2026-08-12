# AuditIQ - AI-Powered Invoice Audit & Document Query API

AuditIQ is a beginner-friendly FastAPI backend that supports two workflows:

1. Invoice audit: upload a text-based invoice PDF, extract fields with Groq, validate them, apply Python risk rules, store the result in MongoDB, and return JSON.
2. Document query: upload a text-based PDF, split it into chunks, create simple text embeddings, store chunks in MongoDB, retrieve relevant chunks with vector similarity, and ask Groq to answer questions using that context.

The project is designed for interview explanation, so the RAG flow is intentionally simple and easy to trace.

## Technology Stack

- Python
- FastAPI
- Groq API
- PyMuPDF
- Pydantic
- MongoDB with PyMongo
- Embeddings
- RAG
- Swagger UI

## Workflows

### Invoice Audit

```text
Upload invoice PDF
-> Extract text using PyMuPDF
-> Send text to Groq
-> Receive structured JSON fields
-> Validate using Pydantic
-> Detect missing fields and inconsistencies in Python
-> Calculate High, Medium, or Low risk in Python
-> Store audit result in MongoDB
-> Return JSON
```

### Document Query RAG

```text
Upload document PDF
-> Extract text using PyMuPDF
-> Split text into chunks
-> Create embeddings for each chunk
-> Store chunks and embeddings in MongoDB
-> User asks a question
-> Create embedding for the question
-> Retrieve most similar chunks using cosine similarity
-> Send question and retrieved context to Groq
-> Return context-grounded answer with sources
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
│   ├── audit_service.py
│   ├── embedding_service.py
│   └── document_service.py
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

## API Endpoints

### `POST /audit`

Uploads and audits one invoice PDF.

Main steps:

1. Reject non-PDF files.
2. Extract text from all pages.
3. Return an error if there is no readable text.
4. Ask Groq to return invoice fields as JSON.
5. Parse with `json.loads()`.
6. Validate with `InvoiceFields`.
7. Detect missing fields and inconsistencies in Python.
8. Calculate risk in Python.
9. Store the audit result in MongoDB.
10. Return the saved result with `_id` as a string.

### `GET /audits`

Returns the latest 20 saved audit results.

### `POST /documents`

Uploads one text-based PDF for document querying.

Main steps:

1. Reject non-PDF files.
2. Extract readable text using PyMuPDF.
3. Split text into chunks.
4. Create an embedding for each chunk.
5. Store the document, chunks, and embeddings in MongoDB.
6. Return document ID and chunk count.

### `GET /documents`

Returns the latest 20 uploaded documents without returning full chunk text or embeddings.

### `POST /query`

Asks a question about uploaded documents.

Example request:

```json
{
  "question": "What is the total amount?",
  "document_id": "optional_document_id",
  "top_k": 3
}
```

If `document_id` is not provided, the API searches across all uploaded documents.

Main steps:

1. Create an embedding for the question.
2. Compare it with stored chunk embeddings using cosine similarity.
3. Select the top matching chunks.
4. Send the question and chunks to Groq.
5. Return a grounded answer and source chunks.

## Extracted Invoice Fields

Groq is asked to return only:

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

## Mandatory Fields

- `invoice_number`
- `invoice_date`
- `vendor_name`
- `total_amount`
- `currency`

A field is missing when it is `None`, empty, or only whitespace.

## Inconsistency Rules

These are checked in Python:

- `total_amount` is negative.
- `tax_amount` is greater than `total_amount`.
- `currency` is not exactly three alphabetic characters.

## Risk Rules

- `High`: Two or more mandatory fields are missing, total is negative, or tax is greater than total.
- `Medium`: Exactly one mandatory field is missing or currency format is invalid.
- `Low`: No mandatory fields are missing and no inconsistencies exist.

Groq does not calculate the final risk.

## Embeddings and Vector Search

This project uses a simple local embedding function in `embedding_service.py`.

It tokenizes text, maps tokens into a fixed-size numeric vector using hashing, normalizes the vector, and compares vectors using cosine similarity.

This keeps the RAG workflow easy to explain in a fresher interview. It is not a production-grade embedding model.

## MongoDB Collections

The app uses:

```text
audit_results
documents
```

`audit_results` stores invoice audit outputs.

`documents` stores uploaded document metadata, chunks, and chunk embeddings.

## Installation

```bash
cd auditiq
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

On macOS or Linux:

```bash
source venv/bin/activate
```

## Environment Setup

Create `.env`:

```bash
copy .env.example .env
```

On macOS or Linux:

```bash
cp .env.example .env
```

Fill in:

```text
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_groq_model
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=auditiq
```

## Run

```bash
uvicorn app.main:app --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Swagger Testing

Invoice audit:

1. Open `POST /audit`.
2. Upload `sample_invoice.pdf`.
3. Execute.
4. Check `risk_level`.

Document query:

1. Open `POST /documents`.
2. Upload `sample_invoice.pdf` or another text-based PDF.
3. Copy the returned `_id`.
4. Open `POST /query`.
5. Ask a question like:

```json
{
  "question": "What is the invoice number?",
  "document_id": "paste_document_id_here",
  "top_k": 3
}
```

## Sample Invoice

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

## Limitations

- Supports only text-based PDFs.
- Scanned PDFs are not supported because OCR is not implemented.
- The embedding function is simple and local, not a production embedding model.
- Vector search is done in Python using cosine similarity, not with a dedicated vector database.
- No frontend, authentication, Docker, cloud deployment, or background jobs.
- LLM answer quality depends on retrieved context and Groq response quality.

## Interview Explanation

The safest explanation:

```text
Groq extracts invoice fields and answers document questions.
Python validates, retrieves context, checks rules, and calculates final risk.
MongoDB stores audit results and document chunks with embeddings.
```
