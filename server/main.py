# server/main.py
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# local import - requires server/__init__.py (see below)
from .rag import engine

load_dotenv()

app = FastAPI(title="RAG with Gemini (LangChain)")

# CORS (allow all for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve index at root and static assets under /static
# - This prevents static from intercepting /api routes.
app.mount("/static", StaticFiles(directory="client"), name="static")

@app.get("/")
def index():
    return FileResponse("client/index.html")

class AskPayload(BaseModel):
    question: str

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if not os.getenv("GOOGLE_API_KEY"):
        raise HTTPException(status_code=400, detail="Missing GOOGLE_API_KEY in environment.")

    filename = file.filename or "uploaded_file"
    if not (filename.lower().endswith(".pdf") or filename.lower().endswith(".txt") or filename.lower().endswith(".docx")):
        raise HTTPException(status_code=400, detail="Only .pdf, .txt, .docx are supported.")

    data = await file.read()
    try:
        result = engine.build_index(data, filename)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ask")
async def ask(payload: AskPayload):
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty.")
    try:
        result = engine.ask(payload.question.strip())
        if result.get("status") != "ok":
            raise HTTPException(status_code=400, detail=result.get("message", "Unknown error"))
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


