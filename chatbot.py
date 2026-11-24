"""
chatbot.py - answers questions using TWO routes:
  1. "structured" -> numbers/ratings already extracted (fast and exact)
  2. "document"   -> search the PDF text (RAG) and cite page numbers
A tiny AI call first decides which route a question needs.
(graph.py wires these functions together as a LangGraph agent.)
"""
import json
from typing import Literal
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
from llm import get_llm


class Route(BaseModel):
    route: Literal["structured", "document"]


ROUTER_PROMPT = """Decide how to answer the question about a credit rating report.
- "structured": asks for rating, outlook, revenue, profit, debt, ratios, strengths or risks.
- "document": asks for reasons, explanations, rationale, or anything needing the report text.
Question: {q}"""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=20), reraise=True)
def _ask(prompt: str) -> str:
    return get_llm().invoke(prompt).content


def choose_route(question: str) -> str:
    try:
        return get_llm().with_structured_output(Route).invoke(ROUTER_PROMPT.format(q=question)).route
    except Exception:
        return "document"          # safe default if routing fails


def answer_structured(question, report, metrics) -> str:
    facts = {"report": report.model_dump(), "calculated_metrics": metrics.to_dict("records")}
    return _ask(f"Answer using ONLY these facts. If the answer is not here, say so.\n"
                f"FACTS:\n{json.dumps(facts, default=str)}\n\nQuestion: {question}")


def answer_document(question, store) -> tuple[str, list[int]]:
    docs = store.similarity_search(question, k=4)
    context = "\n\n".join(f"[Page {d.metadata['page']}] {d.page_content}" for d in docs)
    answer = _ask(f"Answer using ONLY the context. Mention page numbers like (p. 3). "
                  f"If the answer is not in the context, say so.\n\nCONTEXT:\n{context}\n\nQuestion: {question}")
    return answer, sorted({d.metadata["page"] for d in docs})
