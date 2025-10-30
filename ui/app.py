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
        timeout=10,
    )