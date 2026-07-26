import json
import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")


SYSTEM_PROMPT = """
You extract fields from text-based invoice PDFs.
Return valid JSON only.
Return only these keys:
invoice_number, invoice_date, vendor_name, customer_name, total_amount, tax_amount, currency.
Use null for missing information.
Do not return markdown or explanations.
Do not invent unavailable values.
"""


def extract_invoice_fields(invoice_text: str) -> dict:
    if not GROQ_API_KEY:
        raise RuntimeError("Groq API key is missing.")

    if not GROQ_MODEL:
        raise RuntimeError("Groq model is missing.")

    client = Groq(api_key=GROQ_API_KEY)

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0.1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": invoice_text},
            ],
        )
    except Exception as exc:
        raise RuntimeError("Groq API request failed.") from exc

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("Groq returned invalid JSON.") from exc
