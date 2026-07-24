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
        if att.query:
            # Genie's natural-language description of the result (the "overview /
            # key observations" narrative shown in the Genie UI) — keep it.
            if att.query.description:
                text_parts.append(att.query.description)
            if att.query.query:
                generated_sql = att.query.query
                # Fetch the result rows. Genie often splits the response into several
                # attachments (query in one, text in another); the query rows must be
                # fetched BY ATTACHMENT ID — the message-level call returns 0 rows in
                # that case. Fall back to the message-level call if needed.
                sr = None
                try:
                    res = w.genie.get_message_query_result_by_attachment(
                        space_id=msg.space_id,
                        conversation_id=msg.conversation_id,
                        message_id=msg.message_id,
                        attachment_id=att.attachment_id,
                    )
                    sr = res.statement_response
                except Exception:
                    sr = None
                if not (sr and sr.result and sr.result.data_array):
                    try:
                        res = w.genie.get_message_query_result(
                            space_id=msg.space_id,
                            conversation_id=msg.conversation_id,
                            message_id=msg.message_id,
                        )
                        sr = res.statement_response
                    except Exception:
                        sr = None
                if sr and sr.manifest and sr.manifest.schema and sr.result:
                    columns = [c.name for c in sr.manifest.schema.columns]
                    rows = sr.result.data_array or []

    # De-duplicate identical attachment texts while preserving order.
    seen = set()
    unique_parts = []
    for p in text_parts:
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            unique_parts.append(p)
    answer = "\n\n".join(unique_parts).strip()

    # Expand Genie's own answer into a fuller, demo-grade explanation grounded in the
    # data. This PRESERVES everything Genie said (overview + observations) and adds
    # analysis — it never shortens. SQL is intentionally NOT surfaced to the user.
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
    """Expand Genie's own answer + full result set into a complete, detailed explanation.

    Key rule: PRESERVE everything Genie said (its overview and key observations) and add
    to it — never summarise or drop content. Falls back to Genie's raw answer on any error
    or if the model returns something shorter than Genie already gave us.
    """
    if not question or not answer and not rows:
        return answer

    # Feed the full result set (capped generously) so the model can describe the whole trend,
    # not just the first few rows.
    preview = ""
    if columns and rows:
        head = rows[:200]
        preview = " | ".join(columns) + "\n" + "\n".join(
            " | ".join("" if c is None else str(c) for c in r) for r in head
        )
        if len(rows) > 200:
            preview += f"\n… ({len(rows) - 200} more rows)"

    doc_note = ""
    if doc_context:
        doc_note = (
            "\n\nThe user also uploaded a document; relevant excerpt:\n\"\"\"\n"
            + doc_context[:3000] + "\n\"\"\"\n"
            "Where the question relates to the document, connect its content to the data."
        )

    system = (
        "You are the Fraud Chatbot for an insurance company, speaking to fraud analysts and claims "
        "managers in a customer demo. You are given the analytics engine's own answer and its full "
        "result set. Produce a COMPLETE, detailed, well-structured response in clear British English.\n\n"
        "CRITICAL RULES:\n"
        "- PRESERVE everything in the analytics engine's answer. Reproduce its overview and every key "
        "observation IN FULL — never summarise, shorten, truncate, or omit any point it made. If it "
        "gave an 'Overview' and 'Key observations', keep those sections and their content.\n"
        "- You may EXPAND: add more detail, describe the full trend across all periods/rows, note "
        "peaks, troughs, ranges and comparisons, and finish with a brief '**What this suggests**' "
        "takeaway for fraud investigation. Add, never remove.\n"
        "- Structure with a short '**Overview**' paragraph and a '**Key observations**' bulleted list "
        "(one bullet per notable point), matching the engine's structure where present.\n"
        "- Describe the WHOLE result set, not just the first rows. For a monthly trend, walk through the "
        "movement over time and call out the highest and lowest months.\n"
        "- Money is GBP: format with £ and thousands separators (e.g. £34,100; £K/£M for large sums). "
        "Rates as percentages to one decimal place.\n"
        "- Use ONLY the numbers provided; never invent figures or columns. Do NOT mention SQL, queries, "
        "tables or column names as technical artefacts — speak in business terms."
    )
    user = (
        f"User question:\n{question}\n\n"
        f"Analytics engine's answer (preserve and expand — do not shorten):\n"
        f"{answer or '(no text answer; describe the data below in full)'}\n\n"
        f"Full result set:\n{preview or '(no tabular data returned)'}"
        f"{doc_note}"
    )
    try:
        out = llm(system, user, temperature=0.3, max_tokens=2500).strip()
        # Guard: never return something shorter than Genie's own answer.
        if out and len(out) >= len(answer):
            return out
        return answer
    except Exception:
        return answer
