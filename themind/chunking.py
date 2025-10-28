# this function will split overlapping segments each with a maximum fixed size
# then embed these "chunks" into vectors to search and retrieve relevant parts 
# when answering a query

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