# this will be used for the streamlit frontend
# streamlit is a great to build interactive web UIs in python quickly

import requests
import streamlit as st
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from themind import ingest

st.title("MegaMind-Rag: the genie in the bottle")
st.set_page_config(page_title="MegaMind-Rag", page_icon=None, layout="centered") # dont have a page icon yet

st.subheader("Upload documents")
uploaded_file = st.file_uploader("Drop PDF / MD / TXT, type=['pdf', 'md', 'txt']")

# make sure docs/ exists - should always 
os.makedirs("docs", exist_ok=True)

if "indexed_files" not in st.session_state: # mini dictionary by streamlit to remember for reruns
    st.session_state.indexed_files = []

if uploaded_file is not None:
    # save file to docs
    save_path = os.path.join("docs", uploaded_file.name)
    with open(save_path, "wb") as f: # write binary and give raw bytes all in one go
        f.write(uploaded_file.getbuffer())

    st.success(f"Saved to {save_path}")

    if uploaded_file.name not in st.session_state.indexed_files:
        # re-run ingestion so the new doc in FAISS
        with st.spinner("Indexing document..."):
            ingest.run_ingest(docs_dir="docs", out_dir="data")
        # add onto session values so we dont always re-index
        st.session_state.indexed_files.append(uploaded_file.name)
    

        st.success("Index rebuilt, you can ask about it now")

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
    st.caption(f"Latency: {data.get("latency_ms", "?")}ms")
