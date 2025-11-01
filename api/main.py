# this is the entry point for the system
# wraps the retrieval system and the LLM logic into a web API
# the flow for the system api-wise is:
# http request(question) -> FastAPI receives it -> answer_question() runs
# retriver + LLM --> answer -> returns JSON with {answer, source, latency}

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv

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

# retriever needs successful store so we init after and llm too for clarity
retriever = Retriever(store=store, embedder=embedder, top_k=5)
llm = LLMProvider()

# expose RAG pipepline thorugh HTTP so me or anyone cna ask questions to it from anywhere
# adding metadata onto the API, makes it clearer for it to be used in the future
# this will appear in swagger ui in /docs and /openai.json 
app = FastAPI(title="MegaMind-Rag", summary="Context specific response using RAG",
               description="An api which gives context specific" \
" response for specialized domains using retrieval augmented generation in unison " \
"with modern GenAI", version="1.618")

class AskRequest(BaseModel):
    # here we're defining how data clients must send in POST requests
    question: str

# define a GET endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/ask")
def ask(request: AskRequest):
    response = answer_question(question=request, retriever=retriever, llm=llm)
    return response
# fast api turns JSON request into Python object of type AskRequest
# the returned dictionary is returned as a HTTP response, then FastAPI converts it to JSON
