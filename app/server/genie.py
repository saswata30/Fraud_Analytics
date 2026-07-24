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
from server.db import llm, sql


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

    return _format_message(w, msg, question, doc_context)


def _format_message(w, msg, question: str = "", doc_context: str = "") -> dict:
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

    # Elaborate Genie's (often terse) answer into a verbose, detailed explanation
    # grounded in the returned data. The SQL is intentionally NOT surfaced to the user.
    verbose = _elaborate(question, answer, columns, rows, doc_context)

    return {
        "conversation_id": msg.conversation_id,
        "message_id": msg.message_id,
        "answer": verbose or answer or "I couldn't produce an answer for that.",
        "columns": columns,
        "rows": rows[:200],
        "error": msg.error.error if msg.error else None,
    }


def _elaborate(question: str, answer: str, columns: list, rows: list, doc_context: str) -> str:
    """Use the workspace LLM to turn a short answer + result rows into a detailed,
    demo-grade explanation. Falls back to the raw answer if the LLM is unavailable."""
    if not question:
        return answer
    # Compact the result set for the prompt (cap rows/cols to stay well within context).
    preview = ""
    if columns and rows:
        head = rows[:40]
        preview = " | ".join(columns) + "\n" + "\n".join(
            " | ".join(str(c) for c in r) for r in head
        )
        if len(rows) > 40:
            preview += f"\n… ({len(rows) - 40} more rows)"

    doc_note = ""
    if doc_context:
        doc_note = (
            "\n\nThe user also uploaded a document; relevant excerpt:\n\"\"\"\n"
            + doc_context[:3000] + "\n\"\"\"\n"
            "Where the question relates to the document, connect its content to the data."
        )

    system = (
        "You are a Fraud Chatbot analyst for an insurance company, speaking to fraud analysts and "
        "claims managers in a customer demo. Rewrite the provided result into a thorough, well-structured, "
        "business-friendly explanation in clear British English. Requirements:\n"
        "- Open with a direct 1-sentence answer to the question, stating the key number(s).\n"
        "- Then add 2-4 short paragraphs (or a tidy bulleted breakdown) that interpret the numbers: "
        "call out the largest/smallest values, notable patterns, comparisons and what they imply for fraud risk.\n"
        "- Money is GBP: format with a £ and thousands separators (e.g. £34,100; use £K/£M for large sums). "
        "Rates as percentages to one decimal place.\n"
        "- Add one brief 'What this suggests' takeaway with a practical fraud-investigation implication.\n"
        "- Be accurate: use ONLY the numbers provided; never invent figures or columns. "
        "Do NOT mention SQL, queries, tables, or column names as technical artefacts — speak in business terms.\n"
        "- Do not use headings larger than bold labels; keep it readable in a chat bubble."
    )
    user = (
        f"User question:\n{question}\n\n"
        f"Concise result from the analytics engine:\n{answer or '(no text answer; use the data below)'}\n\n"
        f"Supporting data:\n{preview or '(no tabular data returned)'}"
        f"{doc_note}"
    )
    try:
        out = llm(system, user, temperature=0.3, max_tokens=900)
        return out.strip() or answer
    except Exception:
        return answer
