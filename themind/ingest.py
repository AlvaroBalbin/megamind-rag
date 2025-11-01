# this script reads all the documents, breaks them into chunks, turns those 
# chunks then into vector embeddings, saving them as FAISS index plus a metadata file
# create a semantic index that lives alongside our system

# the data flow is the following:
# docs -> load_documents() -> chunk_text() -> Embedder.encode() -> save_index_chunks() -v
                                                                            # read for retrieval

from pathlib import Path
from tqdm import tqdm
import numpy as np

from .loaders import load_documents
from .chunking import chunk_text
from .embedder import Embedder
from .store import save_index_chunk


def run_ingest(docs_dir: str = "docs", out_dir: str = "data"):
    embedder = Embedder() # initialize instance of the class

    all_chunks_records: list[dict] = [] # stores text metadata and text
    all_vectors: list[np.ndarray] = [] # corresponding numeric embeddings

    for doc in load_documents(docs_dir):
        # the generator is going to "run" as many documents that are uploaded
        doc_name = doc["doc_name"]
        raw_text = doc["text"]

        chunks = chunk_text(raw_text)
        # we want to just keep the text portion of chunks not the metadata
        texts = [chunk["text"] for chunk in chunks]
        
        # check if texts is empty
        # this shouldnt happen since we safety'd it in chunking but its good in case
        # should not slow down performance lol :)
        if not texts:
            continue

        # now embed all the chunks into a vector - this is a per-document
        vectors = embedder.encode(texts) # on current model you should (get no_chunks, 384)

        # store metadata now that we've embedded
        for i, chunk in enumerate(chunks):
            record = {
                "doc_name": doc_name,
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
            }
        # store metadata for every chunk where it came from(document) and its text
        all_chunks_records.append(record)
        # store embedding data as a vector into all_vectors
        all_vectors.append(vectors)

    # we need now need to stack loads of numpy arrays one per document onto each other
    # thats because FAISS wants [num_of_chunks, total dimensions] as its input 
    # the best way to achieve this is to use .vstack for numpy stacking is doing row-wise
    # basically glue everything into a 2D array
    stacked_mtx = np.vstack(all_vectors).astype("float32")
    save_index_chunk(stacked_mtx, all_chunks_records, out_dir=out_dir)

if __name__ == "__main__": # when running file do ingest.py not when importing
    run_ingest()
