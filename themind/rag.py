# the actual brain of the system
# retrievel -> prompt build -> LLM -> answer and cited sources

import time
from typing import Any

from .retrieve import Retriever
from .llm_provider import LLMProvider

def build_context_block(results: list[dict]) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(
            f"[i] (Source: {r["doc_name"]} #{r["chunk_id"]})\n {r["text"]}\n)"
        )

    return "\n".join(lines)

# for the prompt I asked gpt to make a great prompt -> gave me inspiration :)
def build_prompt(question: str, results: list[dict]) -> str:
    context_block = build_context_block(results) # get context block
    prompt = f"""
    You are a domain expert assistant.
    Answer ONLY using the CONTEXT.
    If the answer is not in the context, say "I don't know.

    CONTEXT:
    {context_block}

    QUESTION:
    {question}

    FINAL ANSWER:"""

    return prompt

# the function will return the string that the info holds but it can be of many data types
def answer_question(question: str, retriever: Retriever, llm: LLMProvider) -> dict[str, Any]:
    time_start = time.perf_counter()
    results = retriever.retrieve(question)
    prompt = build_prompt(question, results)
    answer_text = llm.generate_answer(prompt)
    latency = int((time.perf_counter - time_start) * 1000) # convert seconds to milliseconds

    # capture all the sources into a nice list
    sources = [{
        "doc_name": r["doc_name"],
        "chunk_id": r["chunk_id"],
        "text": r["text"],
    } for r in results]

    # now return everything aesthetically
    return  {
        "answer": answer_text,
        "sources": sources,
        "latency_ms": latency, # this might be used for debugging or part of the response too
    }

