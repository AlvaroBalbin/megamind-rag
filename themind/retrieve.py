# if we get a human question we need to pull top-k relevant chunks from our documents
# this is what that function solves

import numpy as np

from .embedder import Embedder
from .store import StoreKnowledge

class Retriever:
    # again we use a class so we dont have to pass two heavy objects repetitively
    def __init__(self, store: StoreKnowledge, embedder: Embedder, top_k: int = 5):
        self.store = store
        self.embedder = embedder
        self.top_k = top_k

    def retrieve(self, question: str):
        # get the embedding vector for the question
        question_vector = self.embedder.encode([question])[0] # expects a list of texts so use []
        results = self.store.query(question_vector.astype("float32"), top_k=self.top_k)

        return results
