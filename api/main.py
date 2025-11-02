# this is the entry point for the system
# wraps the retrieval system and the LLM logic into a web API
# the flow for the system api-wise is:
# http request(question) -> FastAPI receives it -> answer_question() runs
# retriver + LLM --> answer -> returns JSON with {answer, source, latency}

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import boto3
import tempfile

from themind.embedder import Embedder
from themind.store import StoreKnowledge
from themind.retrieve import Retriever
from themind.llm_provider import LLMProvider
from themind.rag import answer_question
from themind import ingest

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "eu-west-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

session = boto3.session.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)
s3 = session.client("s3")

# on startup get the global components (set as None, dont eat the ram away)
embedder = None
store = None
retriever = None
llm = None

# lazy loadings more effective
def get_pipeline():
    global embedder, store, retriever, llm
    if embedder is None:
        embedder = Embedder()

    if store is None:
        # use env so dont try to read MASSIVE local files
        index_dir = os.getenv("INDEX_DIR", "data")
        s = StoreKnowledge(
            index_path=f"{index_dir}/faiss.index",
            chunks_path=f"{index_dir}/chunks.jsonl",
        )

        try:
            s.load()
            print("[MAIN] store loaded in a lazy way")
        except Exception as e:
            print(f"[main] store not loaded yet: {e}")
        store = s

        if retriever is None:
            retriever = Retriever(store=store, embedder=embedder, top_k=3)

        if llm is None:
            llm = LLMProvider()

        return retriever, llm

"""you load your embedding model ONCE not every request
also create StoreKnowledge object pointing to your saved faiss index and metadata
and IMPORTANTLY:
    dont recreate everything for each request, load once per memory.
"""

# expose RAG pipepline thorugh HTTP so me or anyone cna ask questions to it from anywhere
# adding metadata onto the API, makes it clearer for it to be used in the future
# this will appear in swagger ui in /docs and /openai.json 
app = FastAPI(title="MegaMind-Rag", summary="Context specific response using RAG",
               description="An api which gives context specific" \
" response for specialized domains using retrieval augmented generation in unison " \
"with modern GenAI", version="1.618")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # who can access your API
    allow_credentials=True,       # allow cookies/auth headers
    allow_methods=["*"],          # allow all HTTP verbs (GET, POST, etc.)
    allow_headers=["*"],          # allow all request headers
)

class AskRequest(BaseModel):
    # here we're defining how data clients must send in POST requests
    question: str
    user_id: str
    env: str = None

# define a GET endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/ask")
def ask(request: AskRequest):
    retriever, llm = get_pipeline()
    response = answer_question(question=request.question, retriever=retriever, llm=llm)
    return response
# fast api turns JSON request into Python object of type AskRequest
# the returned dictionary is returned as a HTTP response, then FastAPI converts it to JSON

@app.post("/ingest")
def ingest_user_docs(request: AskRequest):
    env = request.env
    prefix = f"{env}/users/{request.user_id}/docs/"

    objects: list[dict] = []
    continuation_token = None # page marker 

    while True:
        kwargs = {"Bucket": S3_BUCKET_NAME, "Prefix": prefix}
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token

        resp = s3.list_objects_v2(**kwargs)
        if "Contents" in resp:
            objects.extend(resp["Contents"])

        if resp.get("IsTruncated"):
            continuation_token = resp.get("NextContinuationToken")
        else:
            break

    if not objects:
        return {"status": "ok", "message": f"no docs found under {prefix}"}

    with tempfile.TemporaryDirectory() as tmp_docs_dir:
        for obj in objects:
            key = obj["Key"]
            if key.endswith("/"):
                continue
            local_path = os.path.join(tmp_docs_dir, os.path.basename(key))
            s3.download_file(S3_BUCKET_NAME, key, local_path)

        tmp_out_dir = os.path.join(tmp_docs_dir, "data")
        os.makedirs(tmp_out_dir, exist_ok=True)

        ingest.run_ingest(docs_dir=tmp_docs_dir, out_dir=tmp_out_dir)

    return {"status": "ok", "message": f"ingestion completed for {request.user_id}"}

