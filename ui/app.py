# this will be used for the streamlit frontend
# streamlit is a great to build interactive web UIs in python quickly

import requests
import streamlit as st
import os
import sys
import boto3
from pathlib import Path
from datetime import datetime, timezone
from fastapi import HTTPException

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
uploaded_files = st.file_uploader("Drop PDF / MD / TXT ",
    type=['pdf', 'md', 'txt'], accept_multiple_files=True)

if "indexed_files" not in st.session_state: # mini dictionary by streamlit to remember for reruns
    st.session_state.indexed_files = []

if uploaded_files is not None:
    # save file to docs
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    for uploaded_file in uploaded_files:
        key = f"{APP_ENV}/users/{user_id}/docs/{ts}-{uploaded_file.name}"

    
        s3.upload_fileobj(uploaded_file, BUCKET, key)
        st.success(f"Uploaded to S3: {key}")

st.caption(f"Indexed files: {st.session_state.indexed_files}")

if st.button("Ingest docs from the S3"):
    try:
        r = requests.post(
            f"{BACKEND_URL}/ingest",
            json={"user_id": user_id, "env": APP_ENV},
            timeout=300, # gave loads of time since render is garbage on free version
        )
        if r.ok:
            st.success("Ingestion triggered on backend")
        else:
            st.error(f"Ingest failed: {r.status_code} {r.text}")
    except Exception as e:
        st.error(f"Could not reach backend: {e}")
    

st.subheader("S3 objects for this user")
user_id = "default_user"
docs_prefix = f"{APP_ENV}/users/{user_id}/docs/"
indexes_prefix = f"{APP_ENV}/users/{user_id}/indexes/"

# list docs
with st.expander("Docs in S3", expanded=False):
    docs_resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=docs_prefix)
    docs = [
        obj["Key"]
        for obj in docs_resp.get("Contents", [])
        if not obj["Key"].endswith("/")
    ]
    if not docs:
        st.write("No docs yet.")
    else:
        for key in docs:
            st.write("-", key)

    select = st.multiselect("Select docs to delete", docs, key="delete_docs_select")
    if st.button("Delete selected docs", type="secondary"):
        if select:
            s3.delete_objects(
                    Bucket=BUCKET,
                    Delete={"Objects": [{"Key": k} for k in select]}
            )
            st.success(f"Deleted {len(select)} doc(s). Refresh the page to see the changes.")
        else:
            st.info("Pick at least one object.")

with st.expander("index files in S3", expanded=False):
    idx_resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=indexes_prefix)
    idxs = [
        obj["Key"]
        for obj in idx_resp.get("Contents", [])
        if not obj["Key"].endswith("/")
    ]
    if not idxs:
        st.write("No indexes yet. Click **Ingest** above.")
    else:
        for key in idxs:
            st.write("-", key)

    select_idx = st.multiselect("Select index files to delete", idxs, key="del_index_sel")
    if st.button("Delete selected index files", type="secondary"):
        if select_idx:
            s3.delete_objects(
                Bucket=BUCKET,
                Delete={"Objects": [{"Key": k} for k in select_idx]}
            )
            st.success(f"Deleted {len(select_idx)} index file(s). Refresh to see the new updated changes.")
        else:
            st.info("Pick at least one object.")

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
    # backend failed, lets see what it said
    if response.status_code != 200:
        st.error(f"backend returned {response.status_code}")
        st.code(response.text)
    # backend ok but json, so can you show raw
    elif "application/json" not in response.headers.get("content-type", ""):
        st.error("backend did not return json")
        st.code(response.text)
    else:
        # this was a good path
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


        