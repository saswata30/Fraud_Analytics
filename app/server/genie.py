"""Genie Conversation API wrapper + document upload to the raw/input/userdata volume."""
from __future__ import annotations

import io
import re

import server.config as config
from server.config import GENIE_SPACE_ID, get_workspace_client
from server.db import sql


def _userdata_path() -> str:
    """Resolved raw/input/userdata volume path (catalog resolved on first use)."""
    config.resolve_catalog(sql)
    return config.USERDATA_PATH


def _slug(name: str) -> str:
    """Safe filename for the volume."""
    base = re.sub(r"[^A-Za-z0-9._-]", "_", name or "upload")
    return base[:120] or "upload"


# ------------------------------ Document upload ------------------------------
def upload_document(filename: str, data: bytes) -> dict:
    """Land an uploaded file in the raw/input/userdata volume, extract its text."""
    w = get_workspace_client()
    safe = _slug(filename)
    udir = _userdata_path()
    dest = f"{udir}/{safe}"

    # Ensure the userdata folder exists, then upload the raw bytes.
    w.files.create_directory(udir)
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
    description_parts: list[str] = []   # Genie's "You want to see…" preamble
    answer_parts: list[str] = []        # Genie's overview + key observations
    generated_sql = None
    columns: list[str] = []
    rows: list[list] = []
    has_viz = False

    for att in (msg.attachments or []):
        if att.text and att.text.content:
            answer_parts.append(att.text.content)
        if getattr(att, "viz", None):
            has_viz = True
        if att.query:
            # Genie's natural-language description of the result (shown above the
            # answer in the Genie UI) — keep it as a lead-in.
            if att.query.description:
                description_parts.append(att.query.description)
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

    def _dedupe(parts):
        seen, out = set(), []
        for p in parts:
            p = (p or "").strip()
            if p and p not in seen:
                seen.add(p)
                out.append(p)
        return out

    # Genie's UI shows the description as a lead-in, then the overview + key observations.
    # We surface Genie's OWN text verbatim (no re-summarising) so the app matches Genie exactly.
    description = "\n\n".join(_dedupe(description_parts)).strip()
    answer_body = "\n\n".join(_dedupe(answer_parts)).strip()
    answer = _structure_answer(description, answer_body)

    chart = _infer_chart(columns, rows) if (has_viz or rows) else None

    return {
        "conversation_id": msg.conversation_id,
        "message_id": msg.message_id,
        "answer": answer or "I couldn't produce an answer for that.",
        "columns": columns,
        "rows": rows[:500],
        "chart": chart,
        "error": msg.error.error if msg.error else None,
    }


def _structure_answer(description: str, body: str) -> str:
    """Format Genie's own text into an Overview + Key observations layout (like the Genie UI),
    WITHOUT rewriting any content. The description becomes a lead-in; the prose becomes the
    Overview; bullet lines (and the trailing summary sentence) become Key observations.
    """
    if not body:
        return description

    lines = body.split("\n")
    overview, bullets, trailing = [], [], []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if re.match(r"^[-*•]\s+", s):
            bullets.append(re.sub(r"^[-*•]\s+", "", s))
        elif bullets:
            # prose that appears AFTER the bullets = a concluding observation
            trailing.append(s)
        else:
            overview.append(s)

    # No bullets → nothing to restructure; return Genie's text as-is (with the lead-in).
    if not bullets:
        return (description + "\n\n" + body).strip() if description else body

    parts = []
    if description:
        parts.append(description)
    if overview:
        ov = " ".join(overview)
        # Drop a dangling "… include:" / "… are:" lead-in now that a header follows.
        ov = re.sub(r"[\s,;:–-]*\b(include|includes|including|are|are as follows|as follows)\s*:?\s*$",
                    ".", ov, flags=re.IGNORECASE).strip()
        parts.append("**Overview**\n" + ov)
    obs = ["**Key observations**"] + [f"- {b}" for b in bullets] + [f"- {t}" for t in trailing]
    parts.append("\n".join(obs))
    return "\n\n".join(parts).strip()


def _infer_chart(columns: list, rows: list) -> dict | None:
    """Infer a Genie-like chart spec from the result shape.

    - A date/time/month/year column on x → line chart (trend), every numeric column a series.
    - Otherwise a categorical first column + numeric column(s) → bar chart.
    Returns {type, x, series:[...], data:[{x, <series>: n}, ...]} or None.
    """
    if not columns or not rows or len(rows) < 2:
        return None

    lc = [c.lower() for c in columns]

    def is_num(v):
        if v is None:
            return False
        try:
            float(v)
            return True
        except (TypeError, ValueError):
            return False

    # numeric columns = those numeric in the first non-empty row
    sample = rows[0]
    numeric_idx = [i for i, v in enumerate(sample) if is_num(v)]
    if not numeric_idx:
        return None

    # find an x (time or category) column that is NOT one of the numeric series
    time_kw = ("month", "date", "year", "day", "week", "quarter", "period", "time", "_ts")
    x_idx = next((i for i, name in enumerate(lc)
                  if any(k in name for k in time_kw) and i not in numeric_idx), None)
    ctype = "line"
    if x_idx is None:
        # first non-numeric column as category → bar
        x_idx = next((i for i in range(len(columns)) if i not in numeric_idx), None)
        ctype = "bar"
    if x_idx is None:
        return None

    series_idx = [i for i in numeric_idx if i != x_idx]
    if not series_idx:
        return None

    def fmt_x(v):
        s = "" if v is None else str(v)
        # trim ISO timestamps to yyyy-MM
        if len(s) >= 7 and s[4] == "-" and s[:4].isdigit():
            return s[:7]
        return s

    data = []
    for r in rows[:500]:
        point = {"x": fmt_x(r[x_idx])}
        for i in series_idx:
            try:
                point[columns[i]] = float(r[i]) if r[i] is not None else None
            except (TypeError, ValueError):
                point[columns[i]] = None
        data.append(point)

    return {
        "type": ctype,
        "x": columns[x_idx],
        "series": [columns[i] for i in series_idx],
        "data": data,
    }
