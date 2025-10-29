# this is the entry point for the system
# wraps the retrieval system and the LLM logic into a web API
# the flow for the system api-wise is:
# http request(question) -> FastAPI receives it -> answer_question() runs
# retriver + LLM --> answer -> returns JSON with {answer, source, latency}

from fastapi import FastAPI
from pydantic import BaseModel

from themind.embedder import Embedder
from themind.store import StoreKnowledge
from themind.retrieve import Retriever
from themind.llm_provider import LLMProvider
from themind.rag import answer_question

# on startup get the global components (dont gotta do them later)
embedder = Embedder()
store = StoreKnowledge(index_path="data/faiss.index", chunks_path="data/chunks.jsonl")

"""you load your embedding model ONCE not every request
also create StoreKnowledge object pointing to your saved faiss index and metadata
and IMPORTANTLY:
    dont recreate everything for each request, load once per memory.
"""

# load stuff if it already exists if not (fresh project) just call a little error
try:
    store.load()
except Exception as e:
    print(f"[MAIN] could not load index/chunks yet: {e}")

