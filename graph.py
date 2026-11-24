"""
graph.py - the chatbot as a small LangGraph "agent" (a flowchart that the AI walks through).

    question -> [router] --structured--> [structured_answer] -> answer
                    |
                    +-----document----> [document_answer]   -> answer

Each box is a normal Python function ("node"). They share one dictionary called the "state".
The router node asks the AI which path to take; LangGraph then follows the matching arrow.
"""
from typing import Any, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

import chatbot


class ChatState(TypedDict, total=False):
    question: str
    report: Any
    metrics: Any
    store: Any
    route: str
    answer: str


def router_node(state: ChatState):
    return {"route": chatbot.choose_route(state["question"])}


def structured_node(state: ChatState):
    text = chatbot.answer_structured(state["question"], state["report"], state["metrics"])
    return {"answer": text + "\n\n*Source: extracted report data*"}


def document_node(state: ChatState):
    text, pages = chatbot.answer_document(state["question"], state["store"])
    return {"answer": text + f"\n\n*Source pages: {', '.join(map(str, pages))}*"}


def build_graph():
    g = StateGraph(ChatState)
    g.add_node("router", router_node)
    g.add_node("structured", structured_node)
    g.add_node("document", document_node)
    g.add_edge(START, "router")
    g.add_conditional_edges("router", lambda s: s["route"], {"structured": "structured", "document": "document"})
    g.add_edge("structured", END)
    g.add_edge("document", END)
    return g.compile()


_graph = build_graph()


def ask(question: str, report, metrics, store) -> str:
    result = _graph.invoke({"question": question, "report": report, "metrics": metrics, "store": store})
    return result["answer"]
