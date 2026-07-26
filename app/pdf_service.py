import fitz


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError("Invalid PDF file.") from exc

    text_parts = []

    for page in document:
        text_parts.append(page.get_text())

    document.close()
    return "\n".join(text_parts).strip()
