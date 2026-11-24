"""
test_offline.py - checks everything that does NOT need an API key.
A tiny fake AI is used so we can test extraction and the chatbot routes too.
Run:  python test_offline.py
"""
import os
import shutil
import tempfile

from fpdf import FPDF
from langchain_core.embeddings import DeterministicFakeEmbedding

import chatbot
import extraction
import graph
import llm
from analysis import compute_metrics, health_flags
from loader import load_pdf
from schema import CreditReport, FinancialYear
from vectorstore import build_store


class FakeMessage:
    def __init__(self, content): self.content = content


class FakeLLM:
    """Pretends to be the AI: returns a ready report, a fixed route, and a fixed answer."""
    def __init__(self, route="document"): self.route, self.schema = route, None
    def with_structured_output(self, schema):
        clone = FakeLLM(self.route); clone.schema = schema; return clone
    def invoke(self, prompt):
        if self.schema is CreditReport:
            return CreditReport(company_name="Test Co", rating="AA-", outlook="Stable",
                                financials=[FinancialYear(year="FY23", revenue=100, ebitda=20, net_profit=10,
                                                          total_debt=50, net_worth=100, interest_expense=5)])
        if self.schema is chatbot.Route:
            return chatbot.Route(route=self.route)
        return FakeMessage("fake answer")


def make_pdf(path):
    pdf = FPDF()
    for text in ["Page one: Test Co rating rationale and strengths.", "Page two: risks include volatile raw material prices."]:
        pdf.add_page(); pdf.set_font("Helvetica", size=12); pdf.multi_cell(0, 10, text)
    pdf.output(path)


def run():
    tmp = tempfile.mkdtemp()
    pdf_path = os.path.join(tmp, "t.pdf"); make_pdf(pdf_path)

    # 1. loader keeps page numbers
    pages = load_pdf(pdf_path)
    assert [p.metadata["page"] for p in pages] == [1, 2], "page numbers wrong"
    print("loader OK")

    # 2. analysis maths
    report = CreditReport(company_name="X", financials=[
        FinancialYear(year="FY22", revenue=100, ebitda=20, net_profit=8, total_debt=300, net_worth=100, interest_expense=15),
        FinancialYear(year="FY23", revenue=80, ebitda=6, net_profit=1, total_debt=300, net_worth=100, interest_expense=4)])
    m = compute_metrics(report)
    last = m.iloc[-1]
    assert round(last["Revenue Growth %"], 1) == -20.0
    assert round(last["EBITDA Margin %"], 1) == 7.5
    assert round(last["Debt / Equity (x)"], 1) == 3.0
    assert round(last["Interest Cover (x)"], 1) == 1.5
    assert len(health_flags(m)) == 4
    empty = compute_metrics(CreditReport(company_name="Y", financials=[FinancialYear(year="FY1")]))
    assert empty.iloc[0]["Debt / Equity (x)"] is None or str(empty.iloc[0]["Debt / Equity (x)"]) == "nan"
    print("analysis OK")

    # 3. vector store: builds once, reuses on second call, search returns page numbers
    import vectorstore
    vectorstore.DB_FOLDER = os.path.join(tmp, "db")
    emb = DeterministicFakeEmbedding(size=32)
    store = build_store(pages, "test_col", emb)
    first = store._collection.count()
    store = build_store(pages, "test_col", emb)
    assert store._collection.count() == first > 0, "should not embed twice"
    assert store.similarity_search("risks", k=1)[0].metadata["page"] in (1, 2)
    print("vectorstore OK")

    # 4. extraction + both chatbot routes with the fake AI
    llm.get_llm = lambda: FakeLLM()
    extraction.get_llm = llm.get_llm; chatbot.get_llm = llm.get_llm
    got = extraction.extract_report(pages)
    assert got.company_name == "Test Co" and got.rating == "AA-"
    metrics = compute_metrics(got)
    chatbot.get_llm = lambda: FakeLLM("structured")
    assert "extracted report data" in graph.ask("What is the rating?", got, metrics, store)
    chatbot.get_llm = lambda: FakeLLM("document")
    assert "Source pages" in graph.ask("Why this rating?", got, metrics, store)
    print("extraction + chatbot routes OK")

    # 5. REST API (FastAPI) end to end with the fake AI
    import api, pipeline
    from fastapi.testclient import TestClient
    pipeline.get_embeddings = lambda: emb
    chatbot.get_llm = lambda: FakeLLM("document")
    client = TestClient(api.app)
    assert client.get("/health").json() == {"status": "ok"}
    with open(pdf_path, "rb") as f:
        up = client.post("/reports", files={"file": ("t.pdf", f, "application/pdf")}).json()
    assert up["report"]["company_name"] == "Test Co" and up["metrics"][0]["Year"] == "FY23"
    ans = client.post(f"/reports/{up['report_id']}/ask", json={"question": "Why?"}).json()
    assert "Source pages" in ans["answer"]
    assert client.get("/reports/nope").status_code == 404
    assert client.post("/reports", files={"file": ("x.txt", b"hi", "text/plain")}).status_code == 400
    print("graph + FastAPI OK")

    shutil.rmtree(tmp)
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    run()
