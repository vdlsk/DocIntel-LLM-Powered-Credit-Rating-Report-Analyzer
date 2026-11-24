"""
api.py - the same DocIntel brain, exposed as a REST API (FastAPI).
Run:  uvicorn api:app --reload      then open http://localhost:8000/docs  (free interactive page)

  POST /reports            upload a PDF  -> returns report_id + extracted data + metrics
  GET  /reports/{id}       get the saved result again
  POST /reports/{id}/ask   {"question": "..."} -> answer from the LangGraph chat agent
"""
import hashlib

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from graph import ask
from pipeline import process_pdf

app = FastAPI(title="DocIntel API")
REPORTS = {}          # report_id -> (report, metrics, store). Simple in-memory storage (demo only).


class Question(BaseModel):
    question: str


def _summary(report_id):
    report, metrics, _ = REPORTS[report_id]
    return {"report_id": report_id, "report": report.model_dump(),
            "metrics": metrics.where(metrics.notna(), None).to_dict("records")}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reports")
async def upload_report(file: UploadFile = File(...)):
    data = await file.read()
    if not file.filename.lower().endswith(".pdf") or not data:
        raise HTTPException(400, "Please upload a non-empty PDF file")
    report_id = hashlib.md5(data).hexdigest()[:12]
    if report_id not in REPORTS:
        REPORTS[report_id] = process_pdf(data)
    return _summary(report_id)


@app.get("/reports/{report_id}")
def get_report(report_id: str):
    if report_id not in REPORTS:
        raise HTTPException(404, "Unknown report_id")
    return _summary(report_id)


@app.post("/reports/{report_id}/ask")
def ask_report(report_id: str, body: Question):
    if report_id not in REPORTS:
        raise HTTPException(404, "Unknown report_id")
    report, metrics, store = REPORTS[report_id]
    return {"answer": ask(body.question, report, metrics, store)}
