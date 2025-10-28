import os
from pathlib import Path
from pypdf import PdfReader

def load_text_file(path: Path)-> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()
    
def load_pdf_file(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)

def load_documents(docs_dir: str = "docs"):
    """
    goes into docs_dir and get (doc_name, text)
    """
    docs_dir = Path(docs_dir)
    for p in docs_dir.rglob("*"):
        if p.is_dir:
            continue
        ext = p.suffix.lower() # get suffix in lowercase easier to work with
        if ext in [".md", ".txt"]:
            text = load_text_file(p)
        elif ext in [".pdf"]:
            text = load_pdf_file
        else:
            # future imports will be available at some point lol
            continue

        # does two things clears empty space but also creates condition only ocntinue if data exists
        if text.strip():
            # we use yield cause it creates a generator function
            # pauses mid execution and yields a value back to the caller, then resume
            # from that point the next time you call the function
            yield {
                "doc_name": p.name, # the full path shortened -> no extensions
                "path": str(p), # full path
                "text": text
            }
    