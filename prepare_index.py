import os
import json
import faiss
from sentence_transformers import SentenceTransformer

# === Config ===
DATA_PATH = os.path.join("data", "discourse", "jan2025_posts.json")
OUT_DIR = "index"
os.makedirs(OUT_DIR, exist_ok=True)

# === Load Data ===
with open(DATA_PATH, "r", encoding="utf-8") as f:
    posts = json.load(f)

corpus = []
metadata = []

for post in posts:
    title = post.get("title", "").strip()
    content = post.get("content", "").strip()
    full_text = f"{title}\n{content}".strip()
    corpus.append(full_text)
    metadata.append({
        "url": post.get("url", "#"),
        "text": title or content[:50]
    })

# === Load Embedder ===
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(corpus, show_progress_bar=True)

# === Save FAISS index ===
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)
faiss.write_index(index, os.path.join(OUT_DIR, "faiss_index.bin"))

# === Save supporting files ===
with open(os.path.join(OUT_DIR, "corpus.json"), "w", encoding="utf-8") as f:
    json.dump(corpus, f)

with open(os.path.join(OUT_DIR, "metadata.json"), "w", encoding="utf-8") as f:
    json.dump(metadata, f)

print("✅ Index preparation complete.")
