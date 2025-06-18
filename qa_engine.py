import os
import json
import faiss
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from transformers import pipeline

# === Load Models ===

# Sentence embedder for retrieval
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# HuggingFace QA model (extractive)
qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")

# === Load Index and Data ===

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_DIR = os.path.join(BASE_DIR, "index")

# Load FAISS index
faiss_index = faiss.read_index(os.path.join(INDEX_DIR, "faiss_index.bin"))

# Load documents (each is a dict with "text", "url", "title", etc.)
with open(os.path.join(INDEX_DIR, "docs.json"), "r", encoding="utf-8") as f:
    documents: List[dict] = json.load(f)

# === Answer Function ===

def answer_question(question: str, top_k: int = 5) -> Tuple[str, List[dict]]:
    """
    Given a user question, returns an answer and a list of relevant links.
    """

    # Embed the question
    question_embedding = embed_model.encode([question])
    distances, indices = faiss_index.search(question_embedding, top_k)

    context_chunks = []
    links = []
    seen_urls = set()

    for idx in indices[0]:
        if 0 <= idx < len(documents):
            doc = documents[idx]
            text = doc.get("text", "")
            url = doc.get("url", "")
            title = doc.get("title", "")

            if url and url not in seen_urls:
                context_chunks.append(text)
                links.append({"url": url, "text": title})
                seen_urls.add(url)

    # Join top contexts (up to 2000 characters for the QA model)
    context = "\n\n".join(context_chunks)[:2000]

    try:
        result = qa_pipeline(question=question, context=context)
        answer = result["answer"].strip()
        score = result.get("score", 0.0)

        # Fallback only if generic or low-confidence
        if (
            not answer
            or answer.lower() in ["n/a", "no answer", ""]
            or score < 0.25
        ):
            answer = "I'm not sure, but here are some relevant threads that might help."

    except Exception as e:
        answer = f"Error during QA: {e}"

    return answer, links
