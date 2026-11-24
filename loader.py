"""loader.py - read a PDF and keep the page number of every page (needed for citations)."""
from pypdf import PdfReader
from langchain_core.documents import Document


def load_pdf(path: str):
    reader = PdfReader(path)
    return [Document(page_content=page.extract_text() or "", metadata={"page": number})
            for number, page in enumerate(reader.pages, start=1)]
