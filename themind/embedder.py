from sentence_transformers import SentenceTransformer
import numpy as np

# load a pretrained sentence transformer model
# we're using a class so that its reusable and loads once not every call -> more organized
# model is 80mb so reloading it every time is slow and storing it globally is messy 
# reduces reporducbility too!
class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name) # made model object

    def encode(self, texts: list[str]) -> np.ndarray:
        """returns [len(texts), dimensions(usually 384)]"""
        embeddings = self.model.encode(texts, batch_size=32,
                                       show_progress_bar=False, # in non interactive env not needed
                                       convert_to_numpy=True) # we want numpy not torch object - no training needed
        
        return embeddings 

