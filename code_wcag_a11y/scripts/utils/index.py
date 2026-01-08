def create_embedding_text(chunk: dict) -> str:
    parts = [
        chunk["full_context"],
    ]

    if chunk["type"] == "success_criterion":
        parts.extend(chunk.get("techniques", {}).get("sufficient", []))

    return "\n".join(p for p in parts if p)


def create_document_metadata(chunk: dict) -> dict:
    metadata = {
        "chunk_id": chunk["chunk_id"],
        "type": chunk["type"],
        "wcag_version": chunk["wcag_version"],
        "principle_num": chunk.get("principle_num"),
        "guideline_num": chunk.get("parent_num"),
    }

    if chunk["type"] == "success_criterion":
        metadata["sc_num"] = chunk.get("num")
        metadata["level"] = chunk.get("level")

    return metadata
