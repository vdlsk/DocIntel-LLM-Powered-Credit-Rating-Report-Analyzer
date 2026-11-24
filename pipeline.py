"""
pipeline.py - the 4 steps that turn a PDF into everything we need.
Both the Streamlit app and the FastAPI server call this one function.
"""
import hashlib
import os
import tempfile

from analysis import compute_metrics
from extraction import extract_report
from llm import get_embeddings
from loader import load_pdf
from vectorstore import build_store


def process_pdf(file_bytes: bytes):
    """PDF bytes -> (report, metrics table, vector store)."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(file_bytes)
        path = f.name
    try:
        pages = load_pdf(path)                                   # 1. read pages
    finally:
        os.remove(path)
    report = extract_report(pages)                               # 2. AI fills the form
    metrics = compute_metrics(report)                            # 3. Python maths
    name = "doc_" + hashlib.md5(file_bytes).hexdigest()[:16]
    store = build_store(pages, name, get_embeddings())           # 4. save for search
    return report, metrics, store
