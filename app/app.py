import os

from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from server import backend, genie, news as news_mod

app = FastAPI(title="Allianz Fraud Analytics Workspace")


# ------------------------------ request models ------------------------------
class ChatReq(BaseModel):
    question: str
    conversation_id: str | None = None
    doc_context: str = ""


# ------------------------------ read endpoints ------------------------------
@app.get("/api/meta")
def meta():
    return backend.meta()


@app.get("/api/dashboard")
def dashboard():
    return backend.dashboard()


@app.get("/api/high-risk")
def high_risk(limit: int = 25):
    return backend.high_risk_claims(limit)


@app.get("/api/uc-link")
def uc_link(object: str = ""):
    return backend.uc_link(object)


@app.get("/api/news")
def news(refresh: bool = False):
    return news_mod.news(refresh=refresh)


# ------------------------------ Genie chat + doc upload ------------------------------
@app.post("/api/chat")
def chat(req: ChatReq):
    return genie.ask(req.question, req.conversation_id, req.doc_context)


@app.post("/api/upload")
async def upload(file: UploadFile):
    data = await file.read()
    return genie.upload_document(file.filename or "upload", data)


# ------------------------------ static frontend ------------------------------
_frontend = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(_frontend):
    from fastapi.staticfiles import StaticFiles

    app.mount("/assets", StaticFiles(directory=os.path.join(_frontend, "assets")), name="assets")

    _NO_CACHE = {"Cache-Control": "no-cache, no-store, must-revalidate"}

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        candidate = os.path.join(_frontend, full_path)
        if full_path and os.path.isfile(candidate):
            if "/assets/" in ("/" + full_path):
                return FileResponse(candidate)
            return FileResponse(candidate, headers=_NO_CACHE)
        return FileResponse(os.path.join(_frontend, "index.html"), headers=_NO_CACHE)
