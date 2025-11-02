# this will be used for the streamlit frontend
# streamlit is a great to build interactive web UIs in python quickly

import requests
import streamlit as st
import os
import sys
import boto3
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

BACKEND_URL = (
    st.secrets.get("BACKEND_URL")
    or os.getenv("BACKEND_URL")
    or "https://megamind-rag.onrender.com"
)

st.set_page_config(page_title="MegaMind-Rag", page_icon=None, layout="centered") # dont have a page icon yet
st.title("MegaMind-Rag: the genie in the bottle")

session = boto3.session.Session(
    aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
    region_name=st.secrets["AWS_DEFAULT_REGION"],
)

s3 = session.client("s3")
user_id = "default_user" # figure it out later with authentication
BUCKET = st.secrets["S3_BUCKET_NAME"]
APP_ENV = st.secrets["APP_ENV"]

st.subheader("Upload documents")
uploaded_file = st.file_uploader("Drop PDF / MD / TXT ",
    type=['pdf', 'md', 'txt'],)

if "indexed_files" not in st.session_state: # mini dictionary by streamlit to remember for reruns
    st.session_state.indexed_files = []

if uploaded_file is not None:
    # save file to docs
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    key = f"{APP_ENV}/users/{user_id}/docs/{ts}-{uploaded_file.name}"

    
    s3.upload_fileobj(uploaded_file, BUCKET, key)
    st.success(f"Uploaded to S3: {key}")

    backend_url = BACKEND_URL
    try:
        requests.post(
        f"{backend_url}/ingest",
        json={"user_id": user_id, "env": APP_ENV},
        timeout=30,
        )
    except Exception as e:
        st.warning("Could not connect to backend for ingestion")

st.caption(f"Indexed files: {st.session_state.indexed_files}")

st.subheader("S3 objects for this user")
user_id = "default_user"
docs_prefix = f"{APP_ENV}/users/{user_id}/docs/"
indexes_prefix = f"{APP_ENV}/users/{user_id}/indexes/"

# list docs
docs_resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=docs_prefix)
docs = [obj["Key"] for obj in docs_resp.get("Contents", []) if not obj["Key"].endswith("/")]

st.write("Docs in S3:")
for key in docs:
    st.write("-", key)

# list indexes
idx_resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=indexes_prefix)
idxs = [obj["Key"] for obj in idx_resp.get("Contents", []) if not obj["Key"].endswith("/")]

st.write("Index files in S3:")
for key in idxs:
    st.write("-", key)

# place a widget to input your question
question = st.text_input(label="Ask a question:")

if st.button("Ask") and question.strip(): # if question was empty all whitespace is removed and it returns False
    response = requests.post(
    f"{BACKEND_URL}/ask",
    json={
        "question": question.strip(),
        "user_id": user_id,
        "env": APP_ENV,
    },
    timeout=10,
)
    

    data = response.json() # parse the raw response body as JSON and get python dict object

    # write the section for answer and default it to empty
    st.subheader("Answer")
    st.write(data.get("answer", ""))

    # write the sources section 
    st.subheader("Sources")
    for src in data.get("sources", []):
        # since we are currently using L2 distance a lower score -> means closer meaning
        # if we were to use cosine similarity a higher score would be better
        score = src.get("score", None)
        if score is not None:
            st.write(f"{src['doc_name']}#{src['chunk_id']} (score={round(score,3)})")
        else:
            st.write(f"{src['doc_name']}#{src['chunk_id']}")

    # if we dont know the latency just put ?
    st.caption(f"Latency: {data.get('latency_ms', '?')}ms")