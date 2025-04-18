import os
from dotenv import load_dotenv
from typing import List
from google import generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")


def format_context(chunks: List[str], scores: List[float], max_chunks: int = 5) -> str:
    """Format document chunks into a readable prompt context."""
    context = ""
    # passing the relevance scores for each chunk to the LLM for better RAG
    for i, (chunk, score) in enumerate(zip(chunks[:max_chunks], scores[:max_chunks])):
        context += f"**Source {i+1} (Relevance: {score:.2f}):**\n{chunk.strip()}\n\n"
    return context.strip()


# === Core Answer Generation ===
def generate_answer(query: str, chunks: List[str], scores: List[float], search_web: bool) -> str:
    if not chunks and not search_web:
        return "I couldn't find any relevant content to answer your question."

    context = ""
    if chunks and search_web:
        # Only include top-1 chunk
        context = format_context([chunks[0]], [scores[0]], max_chunks=1)
    elif chunks:
        # Use top-5 chunks for doc-only
        context = format_context(chunks, scores)

    if not search_web:
        prompt = f"""**Role**: You are a document-based assistant. 
1. Base answers ONLY on the provided context below.
2. If unsure, say "I don't have enough information."
3. Cite sources using [1], [2], etc.

**Context**:
{context}

**Question**: {query}

**Answer**:"""
    else:
        prompt = f"""You are an assistant who can answer questions using your own knowledge *and* optional context. 
If the context is useful, incorporate it. Otherwise, I would love it if you relied on your own knowledge. Cite any relevant local sources as [1].

**Context**:
{context}



**Question**: {query}. It is more than okay if none of the context is relevant. Tell me what you know.

**Answer**:"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Error generating answer: {e}"



# these functions below are used to generate the expanded query for the LLM. 
# Eventually however, the `expanded_search` function in `core/retriever.py` that they all culminate in is never used anywhere.
# === Helper to Call LLM with a Prompt ===
def get_llm_help(prompt: str = "") -> str:
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Error generating LLM content: {e}"
    

# === Query Expansion ===
def llm_query_expansion(query: str, prev_queries: List[str]) -> str:
    previous_queries_section = (
        f"Previous Queries: {', '.join(prev_queries)}\n" if prev_queries else ""
    )
    prompt = f"""You are a helpful assistant that expands user queries to be more specific and detailed. You can use previous queries as context. Avoid making the expanded query similar to previous queries. JUST GIVE THE EXPANDED QUERY WITHOUT ANY EXPLANATION.

User Query: {query}
{previous_queries_section}
Expanded Query:"""
    return get_llm_help(prompt)


# === Keyword Extraction from LLM Answer ===
def extract_keywords_from_answer(answer: str) -> List[str]:
    prompt = f"""Extract the most relevant keywords or search terms from the following answer to improve future document retrieval. Return them as a comma-separated list.

Answer: {answer}
Keywords:"""
    keywords_text = get_llm_help(prompt)
    return [kw.strip() for kw in keywords_text.split(",")]


# === Main Feedback Loop Function ===
def feedback_loop_rag(query: str, previous_queries: List[str], retriever, search_web=False) -> dict:

    # Step 1: Expand query
    expanded_query = llm_query_expansion(query, previous_queries)

    # Step 2: Retrieve using expanded query
    initial_results = retriever.search(expanded_query)
    chunks = [doc for doc, _, _, _ in initial_results]
    scores = [meta["bm25_score"] for _, _, _, meta in initial_results]

    # Step 3: First-pass answer
    first_answer = generate_answer(query, chunks, scores, search_web=search_web)

    # Step 4: Extract keywords
    keywords = extract_keywords_from_answer(first_answer)
    refined_query = " ".join(keywords)

    # Step 5: Retrieve using keywords
    refined_results = retriever.search(refined_query)
    refined_chunks = [doc for doc, _, _, _ in refined_results]
    refined_scores = [meta["bm25_score"] for _, _, _, meta in refined_results]

    # Step 6: Final answer
    final_answer = generate_answer(query, refined_chunks, refined_scores, search_web=search_web)

    # Prepare sources for display
    initial_sources = [
        (doc, path, meta["bm25_score"])
        for doc, path, _, meta in initial_results
    ]
    refined_sources = [
        (doc, path, meta["bm25_score"])
        for doc, path, _, meta in refined_results
    ]

    return {
        "final_answer": final_answer,
        "initial_sources": initial_sources,
        "refined_sources": refined_sources,
    }
