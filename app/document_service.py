from datetime import datetime, timezone

from app.embedding_service import chunk_text, cosine_similarity, create_embedding


def create_document_record(file_name: str, document_text: str) -> dict:
    chunks = []

    for index, chunk in enumerate(chunk_text(document_text)):
        chunks.append(
            {
                "chunk_index": index,
                "text": chunk,
                "embedding": create_embedding(chunk),
            }
        )

    return {
        "file_name": file_name,
        "document_type": "document",
        "chunk_count": len(chunks),
        "chunks": chunks,
        "processing_status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def find_relevant_chunks(question: str, documents: list[dict], top_k: int = 3) -> list[dict]:
    question_embedding = create_embedding(question)
    scored_chunks = []

    for document in documents:
        for chunk in document.get("chunks", []):
            score = cosine_similarity(question_embedding, chunk["embedding"])
            scored_chunks.append(
                {
                    "document_id": str(document["_id"]),
                    "file_name": document["file_name"],
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"],
                    "score": round(score, 4),
                }
            )

    scored_chunks.sort(key=lambda chunk: chunk["score"], reverse=True)
    return scored_chunks[:top_k]
