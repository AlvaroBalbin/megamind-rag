from openai import OpenAI
import numpy as np
import os

# load a pretrained sentence transformer model
# we're using a class so that its reusable and loads once not every call -> more organized
# model is 80mb so reloading it every time is slow and storing it globally is messy 
# reduces reporducbility too!
class Embedder:
    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model_name = model_name

    def encode(self, texts: list[str]) -> np.ndarray:
        # make sure its a list
        if isinstance(texts, str):
            texts = [texts]

        response = self.client.embeddings.create(model=self.model_name, input=texts) # we want numpy not torch object - no training needed
        
        vectors = [item.embedding for item in response.data]
        return np.array(vectors, dtype="float32")

