# store semantic vector index
# store the metadata (which vector will pair with which chunk)
# this will be like the semantic database engine connecting the offline to the online parts

# you can call here to create FAISS binary index then when answering a query you can have a
# persistent memory, allowing it to "remember" document embeddings between different runs

import faiss
import json
import numpy as np
from pathlib import Path

class StoreKnowledge:
    def __init__(self, index_path: str, chunks_path: str):
        self.index_path = index_path # where FAISS index vector lives
        self.chunks_path = chunks_path # what the vector means in  words
        self.index = None
        self.chunks = None

    def load(self):
        """load faiss index and then chunk metadata"""
        self.index = faiss.read_index(str(self.index_path))

        chunks: list[dict] = []
        # now chunk metadata
        with open(self.chunks_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                chunks.append(json.loads(line)) # deserialization
            self.chunks = chunks

    # currently only using one query
    def query(self, query_vector: np.ndarray, top_k: int = 5) -> list[dict]:
        """take query embedding then search FAISS index for most 
        similar document chunk. then just return a list of dictionaries
        describing those top-k chunks
        in short: find me 5 pieces of text in knowledge base that are 
        closest to this question
        """
        # make sure you got the right shape for FAISS
        # usually a user will only ask one question that will collapse the dimesions
        # into 1 -> we need to add another axis so FAISS is happy with it
        # [question, dimensions] instead [dim,]
        if query_vector.ndim == 1:
            query_vector = query_vector[np.newaxis, :]

        # do a similarity search with faiss - dont have to do this manually
        distances, indices = self.index.search(query_vector, top_k)

        # flatten arrays out so we only got a 1D array instead of 2D array
        distances = distances[0]; indices = indices[0]

        if self.chunks is None:
            raise RuntimeError("Store is empty rerun data/")
    
        results = []
        for distance, idx in zip(distances, indices):
            if idx < 0 or idx >= len(self.chunks): # Faiss might return error if top-k is not found
                continue # skip unwanted indices
            metadata = self.chunks[idx]
            results.append(
                {
                    "dist_score": float(distance),
                    "doc_name": metadata["doc_name"],
                    "chunk_id": metadata["chunk_id"],
                    "text": metadata["text"],
                }
            )
        return results
    
    @staticmethod
    def save_index_chunk(vectors: np.ndarray, chunk_records: list[dict], out_dir: str="data"):
        # safe check if directory exists
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)

        # build the faiss index
        dim = vectors.shape[1]
        # faiss index a data structure optimized for searching nearest neighbour in vector space
        index = faiss.IndexFlatL2(dim) # simple and highly accurate -> for a small dataset it shouldnt be too slow
        # print("index.is_trained") -> used to debug
        index.add(vectors)

        # write this binary mass into output
        faiss.write_index(index, str(out / "faiss.index"))

        # each line represents on chunk of text + its metadata(doc_name and id)
        # the errors="replace" lets us replace really weird chars(happens in these kind of docs)
        with open(out / "chunks.jsonl", "w", encoding="utf-8", errors="replace") as f:
            for record in chunk_records:
                # dont ensure ascii we might have different languages or math/greek letters
                f.write(json.dumps(record, ensure_ascii=False) + "\n") 

# expose the class so it can be accessed in ingest.py
def save_index_chunk(vectors, chunk_records, out_dir: str = "data"):
    return StoreKnowledge.save_index_chunk(vectors, chunk_records, out_dir)





