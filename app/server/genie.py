"""Genie Conversation API wrapper + document upload to the raw/input/userdata volume."""
from __future__ import annotations

import io
import re

from server.config import (
    GENIE_SPACE_ID,
    USERDATA_PATH,
    WAREHOUSE_ID,
    get_workspace_client,
)
from server.db import sql


def _slug(name: str) -> str:
    """Safe filename for the volume."""
    base = re.sub(r"[^A-Za-z0-9._-]", "_", name or "upload")
    return base[:120] or "upload"


# ------------------------------ Document upload ------------------------------
def upload_document(filename: str, data: bytes) -> dict:
    """Land an uploaded file in the raw/input/userdata volume, extract its text."""
    w = get_workspace_client()
    safe = _slug(filename)
    dest = f"{USERDATA_PATH}/{safe}"

    # Ensure the userdata folder exists, then upload the raw bytes.
    w.files.create_directory(USERDATA_PATH)
    w.files.upload(dest, io.BytesIO(data), overwrite=True)

    text = _extract_text(safe, data)
    return {
        "filename": safe,
        "volume_path": dest,
        "chars": len(text),
        "preview": text[:1500],
        "text": text,
    }


def _extract_text(filename: str, data: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception as e:  # pragma: no cover - best effort
            return f"[Could not extract PDF text: {e}]"
    # csv / txt / json / md — decode as utf-8
    try:
        return data.decode("utf-8", errors="replace")
    except Exception:
        return "[Binary file — no text extracted]"


# ------------------------------ Genie chat ------------------------------
def ask(question: str, conversation_id: str | None = None, doc_context: str = "") -> dict:
    """Send a question to the Genie space; continue a conversation if given an id."""
    if not GENIE_SPACE_ID:
        return {"error": "GENIE_SPACE_ID is not configured for this app."}

    w = get_workspace_client()

    content = question
    if doc_context:
        snippet = doc_context[:6000]
        note = " (document truncated)" if len(doc_context) > 6000 else ""
        content = (
            f"Use this uploaded document as additional context{note}:\n"
            f"\"\"\"\n{snippet}\n\"\"\"\n\nQuestion: {question}"
        )

    if conversation_id:
        msg = w.genie.create_message_and_wait(
            space_id=GENIE_SPACE_ID, conversation_id=conversation_id, content=content
        )
    else:
        msg = w.genie.start_conversation_and_wait(
            space_id=GENIE_SPACE_ID, content=content
        )

    return _format_message(w, msg)


def _format_message(w, msg) -> dict:
    text_parts: list[str] = []
    generated_sql = None
    columns: list[str] = []
    rows: list[list] = []

    for att in (msg.attachments or []):
        if att.text and att.text.content:
            text_parts.append(att.text.content)
        if att.query and att.query.query:
            generated_sql = att.query.query
            # Fetch the result rows for the attachment.
            try:
                res = w.genie.get_message_query_result(
                    space_id=msg.space_id,
                    conversation_id=msg.conversation_id,
                    message_id=msg.message_id,
                )
                sr = res.statement_response
                if sr and sr.manifest and sr.manifest.schema and sr.result:
                    columns = [c.name for c in sr.manifest.schema.columns]
                    rows = sr.result.data_array or []
            except Exception:
                pass

    answer = "\n\n".join(text_parts).strip()
    if not answer and generated_sql:
        answer = "Here are the results."

    return {
        "conversation_id": msg.conversation_id,
        "message_id": msg.message_id,
        "answer": answer or "I couldn't produce an answer for that.",
        "sql": generated_sql,
        "columns": columns,
        "rows": rows[:200],
        "error": msg.error.error if msg.error else None,
    }
