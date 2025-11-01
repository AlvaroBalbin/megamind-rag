# this will be used for the streamlit frontend
# streamlit is a great to build interactive web UIs in python quickly

import requests
import streamlit as st

st.title("MegaMind-Rag: the genie in the bottle")
st.set_page_config(page_title="MegaMind-Rag", page_icon=None, layout="centered") # dont have a page icon yet

# place a widget to input your question
question = st.text_input(label="Ask a question:")

if st.button("Ask") and question.strip(): # if question was empty all whitespace is removed and it returns False
    response = requests.post(
        "https://localhost:8000/ask", # we ll keep this for now before we launch -> testing
        json={"question": question.strip()},
        timeout=10, # reduce this if requests work well consistently
    )

data = response.json() # parse the raw response body as JSON and get python dict object

# write the section for answer and default it to empty
st.subheader("Answer")
st.write(data.get("answer", default=""))

# write the sources section 
st.subheader("Sources")
for src in data.get("sources", []):
    # since we are currently using L2 distance a lower score -> means closer meaning
    # if we were to use cosine similarity a higher score would be better
    st.write(f"{src["doc_name"]}#{src["chunk_id"]} (score={round(src["score"],3)})")

# if we dont know the latency just put ?
st.caption(f"Latency: {data.get("latency_ms", "?")}ms")
