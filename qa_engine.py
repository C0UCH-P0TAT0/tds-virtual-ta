from sentence_transformers import SentenceTransformer
import faiss
import json
import os
from openai import OpenAI

# Load sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load OpenAI key from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Locate JSON data file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, "data", "discourse", "jan2025_posts.json")

# Load discourse posts
with open(json_path, "r", encoding="utf-8") as f:
    posts = json.load(f)

# Prepare corpus for embeddings and metadata for URLs
corpus = [post.get("title", "") + "\n" + post.get("content", "") for post in posts]
metadata = [{"url": post.get("url", "#"), "text": post.get("title", "")} for post in posts]

# Encode the corpus and build FAISS index
embeddings = model.encode(corpus, show_progress_bar=True)
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

def answer_question(question: str, top_k: int = 3):
    # Encode and search for top_k similar posts
    question_embedding = model.encode([question])
    distances, indices = index.search(question_embedding, top_k)

    links = []
    context_chunks = []
    seen = set()

    for idx in indices[0]:
        if idx < len(metadata):
            link = metadata[idx]
            if link["url"] not in seen:
                links.append(link)
                seen.add(link["url"])
                context_chunks.append(corpus[idx])

    context = "\n\n".join(context_chunks)

    # Construct prompt
    prompt = f"""You are a helpful assistant for an online Data Science degree student.

Here are excerpts from past student discussions:

{context}

Answer the following question clearly and accurately:
"{question}"
"""

    try:
        # Use the new OpenAI client to call GPT
        response = client.chat.completions.create(
            model="gpt-4o",  # or gpt-3.5-turbo
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error generating answer from OpenAI: {e}"

    return answer, links
