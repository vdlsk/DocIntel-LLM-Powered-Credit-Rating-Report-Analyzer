"""
vectorstore.py - cut the report into small chunks, turn each into a vector, save in Chroma.
Each chunk remembers its page number, so answers can cite pages.
Saved on disk, so the same PDF is never embedded twice.
"""
import os
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

DB_FOLDER = "chroma_db"


def build_store(pages, collection_name: str, embeddings):
    store = Chroma(collection_name=collection_name, embedding_function=embeddings,
                   persist_directory=os.path.join(DB_FOLDER))
    if store._collection.count() == 0:            # first time for this PDF
        chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150).split_documents(pages)
        store.add_documents(chunks)
    return store
