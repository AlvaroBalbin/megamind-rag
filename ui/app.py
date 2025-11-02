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

st.set_page_config(page_title="MegaMind-Rag", page_icon=None, layout="centered") # dont have a page icon yet
st.title("MegaMind-Rag: the genie in the bottle")

session = boto3.session.Session(
    aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
    region_name=st.secrets["AWS_DEFAULT_REGION"],
)

s3 = session.client("s3")
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
    user_id = "default_user" # figure it out later with authentication
    key = f"{APP_ENV}/users/{user_id}/docs/{ts}-{uploaded_file.name}"

    
    s3.upload_fileobj(uploaded_file, BUCKET, key)
    st.success(f"Uploaded to S3: {key}")

    backend_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
    try:
        requests.post(
        f"{backend_url}/ingest",
        json={"user_id": user_id, "env": APP_ENV},
        timeout=30,
        )
    except Exception as e:
        st.warning("Could not connect to backend for ingestion")

st.caption(f"Indexed files: {st.session_state.indexed_files}")

# place a widget to input your question
question = st.text_input(label="Ask a question:")

if st.button("Ask") and question.strip(): # if question was empty all whitespace is removed and it returns False
    response = requests.post(
        "http://127.0.0.1:8000/ask", # we ll keep this for now before we launch -> testing
        json={"question": question.strip()},
        timeout=10, # reduce this if requests work well consistently
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
