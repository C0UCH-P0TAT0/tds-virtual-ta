import json
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# === Paths ===
DATA_PATH = "data/discourse/jan2025_posts.json"
INDEX_DIR = "index"
INDEX_PATH = os.path.join(INDEX_DIR, "faiss_index.bin")
DOCS_PATH = os.path.join(INDEX_DIR, "docs.json")

# === Load raw posts ===
print("📂 Loading data from:", DATA_PATH)
with open(DATA_PATH, "r", encoding="utf-8") as f:
    raw_posts = json.load(f)

# === Extract text and metadata ===
documents = []
texts = []

print("🧹 Extracting valid posts...")
for i, post in enumerate(raw_posts):
    text = post.get("content_text", "").strip()
    url = post.get("url", "")
    title = post.get("title", "Untitled")

    if text:
        texts.append(text)
        documents.append({
            "text": text,
            "url": url,
            "title": title
        })
    else:
        print(f"[⚠️] Skipping empty post at index {i} (no content_text)")

if not texts:
    raise ValueError("❌ No valid texts found. Make sure 'content_text' is populated in your JSON.")

# === Embed texts using SentenceTransformer ===
print("🧠 Loading sentence transformer model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

print("🧬 Encoding all posts and replies...")
embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

print(f"✅ Embeddings shape: {embeddings.shape}")
if embeddings.shape[0] == 0:
    raise RuntimeError("❌ Embeddings are empty. Aborting index build.")

# === Build FAISS Index ===
print("⚙️ Building FAISS index...")
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# === Save index and metadata ===
print("💾 Saving FAISS index and document metadata...")
os.makedirs(INDEX_DIR, exist_ok=True)
faiss.write_index(index, INDEX_PATH)

with open(DOCS_PATH, "w", encoding="utf-8") as f:
    json.dump(documents, f, indent=2)

print(f"\n✅ Index saved to: {INDEX_PATH}")
print(f"✅ Docs metadata saved to: {DOCS_PATH}")
