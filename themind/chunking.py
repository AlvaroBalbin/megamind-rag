# this function will split overlapping segments each with a maximum fixed size
# then embed these "chunks" into vectors to search and retrieve relevant parts 
# when answering a query

# currently using char-based chunking first. works good for the MVP 
# might go more advanced later

def chunk_text( 
        text: str,
        chunk_size_chars: int = 1200,
        overlap_chars: int = 200,
        ) -> list[dict]:
    
    chunks = []
    i = 0 # starting index in text
    chunk_id = 0 # chunk index
    n = len(text)

    while i < n:
        start = i
        end = min(i + chunk_size_chars, n) # you might be at the end of a text
        chunk_body = text[start: end] # get length of the chunk start -> adjusted end
        chunks.append({
            "chunk_id": chunk_id,
            "text": chunk_body,
            "start": start,
            "end": end,
        })
        chunk_id += 1
        i += chunk_size_chars - overlap_chars # start at overlap match point -> keeps context

        # in very small files you might have problems with i especially with low chars
        # safeguard point
        if i < start: # if they were equal it wouldnt be great either - havent considered it yet
            i = end

    return chunks