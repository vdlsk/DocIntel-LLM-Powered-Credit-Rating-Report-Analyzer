"""
llm.py - the ONLY file that knows which AI provider we use.
To switch provider, change LLM_PROVIDER in the .env file ("gemini" or "openai").
"""
import os
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()


def get_llm():
    """Chat model used for extraction, routing and answering."""
    if PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), temperature=0)


def get_embeddings():
    """Embedding model used to turn text chunks into vectors for search."""
    if PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"))
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    return GoogleGenerativeAIEmbeddings(model=os.getenv("GEMINI_EMBED_MODEL", "models/gemini-embedding-001"))
