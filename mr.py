import os
os.environ["STREAMLIT_SERVER_ENABLE_FILE_WATCHER"] = "false"

import streamlit as st
import time, random, math, json, sqlite3
import torch
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from diffusers import StableDiffusionPipeline

# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------
st.set_page_config(page_title="MASH", layout="centered")
st.title("🏠 MASH")

# --------------------------------------------------
# MODEL SELECTION (GPU / CPU)
# --------------------------------------------------
USE_GPU = torch.cuda.is_available()

@st.cache_resource
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")

@st.cache_resource
def load_llm():
    if USE_GPU:
        return pipeline(
            "text-generation",
            model="mistralai/Mistral-7B-Instruct-v0.2",
            device=0
        )
    return pipeline("text2text-generation", model="google/flan-t5-base")

@st.cache_resource
def load_sd():
    model_id = "stabilityai/sd-turbo" if not USE_GPU else "runwayml/stable-diffusion-v1-5"
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16 if USE_GPU else torch.float32
    )
    return pipe.to("cuda" if USE_GPU else "cpu")

embedder = load_embedder()
llm = load_llm()
sd_pipe = load_sd()

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def eliminate_to_one(options, count):
    idx = 0
    opts = options.copy()
    while len(opts) > 1:
        idx = (idx + count - 1) % len(opts)
        opts.pop(idx)
    return opts[0]

# --------------------------------------------------
# PERSISTENT MEMORY (JSON + SQLITE)
# --------------------------------------------------
MEMORY_DIR = "mash_memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

JSON_PATH = f"{MEMORY_DIR}/snapshots.json"
DB_PATH = f"{MEMORY_DIR}/mash_memory.db"

# ---------- JSON (quick snapshot history)
def load_json_memory():
    if not os.path.exists(JSON_PATH):
        return []
    with open(JSON_PATH, "r") as f:
        return json.load(f)

def save_json_memory(snapshot):
    history = load_json_memory()
    history.append(snapshot)
    with open(JSON_PATH, "w") as f:
        json.dump(history, f, indent=2)

# ---------- SQLITE (long-term structured memory)
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player TEXT,
            category TEXT,
            value TEXT,
            timestamp REAL
        )
        """)

def save_sqlite_memory(player, facts):
    ts = time.time()
    with sqlite3.connect(DB_PATH) as conn:
        for k, v in facts.items():
            conn.execute(
                "INSERT INTO memory (player, category, value, timestamp) VALUES (?, ?, ?, ?)",
                (player, k, v, ts)
            )

def load_sqlite_memory(player, limit=3):
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
        SELECT category, value FROM memory
        WHERE player = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """, (player, limit * 10)).fetchall()

    memory = {}
    for cat, val in rows:
        memory.setdefault(cat, []).append(val)
    return memory

init_db()

# --------------------------------------------------
# RAG (CURRENT + MEMORY)
# --------------------------------------------------
def build_vector_store(current, sqlite_memory):
    texts = []

    for k, v in current.items():
        texts.append(f"Current {k}: {v}")

    for k, values in sqlite_memory.items():
        for v in values[:2]:
            texts.append(f"Past {k}: {v}")

    emb = embedder.encode(texts)
    index = faiss.IndexFlatL2(emb.shape[1])
    index.add(np.array(emb).astype("float32"))

    return index, texts

def retrieve_context(index, texts):
    q = embedder.encode(["Describe this future vividly"]).astype("float32")
    _, idxs = index.search(q, min(6, len(texts)))
    return "\n".join(texts[i] for i in idxs[0])

# --------------------------------------------------
# NARRATIVE STYLES
# --------------------------------------------------
STYLE_PROMPTS = {
    "Whimsical": "Playful, imaginative, lighthearted",
    "Romantic": "Warm, emotional, love-focused",
    "Chaotic": "Unhinged, absurd, mischievous",
    "Serious": "Calm, grounded, realistic"
}

# --------------------------------------------------
# RAG SUMMARY
# --------------------------------------------------
def generate_summary(context, style):
    prompt = f"""
You are a fortune teller.

Tone: {STYLE_PROMPTS[style]}

ONLY use these facts:
{context}

Write one paragraph.
"""

    if llm.task == "text-generation":
        out = llm(prompt, max_new_tokens=160, temperature=0.8)
        return out[0]["generated_text"].replace(prompt, "").strip()

    return llm(prompt, max_length=200)[0]["generated_text"]

# --------------------------------------------------
# IMAGE GENERATION
# --------------------------------------------------
def generate_image(summary):
    prompt = f"""
Illustrated future scene.
{summary}
No text. No words.
"""
    return sd_pipe(prompt, num_inference_steps=10).images[0]

# --------------------------------------------------
# FINAL RESULTS (ASSUMES stage == result)
# --------------------------------------------------
if st.session_state.stage == "result":
    st.header("🎉 Your MASH Future")

    style = st.selectbox("Narrative Style", list(STYLE_PROMPTS.keys()))

    MASH_MAP = {"M": "Mansion", "A": "Apartment", "S": "Shack", "H": "House"}
    house = MASH_MAP[eliminate_to_one(list("MASH"), st.session_state.count)]

    p1 = {"Housing": house}

    for c in st.session_state.categories:
        p1[c] = eliminate_to_one(
            st.session_state.answers_p1[c],
            st.session_state.count
        )
        st.write(f"**{c}:** {p1[c]}")

    if st.button("🔮 Generate Story + Image"):
        with st.spinner("Consulting fate..."):
            sqlite_memory = load_sqlite_memory("player1")
            index, texts = build_vector_store(p1, sqlite_memory)
            context = retrieve_context(index, texts)

            summary = generate_summary(context, style)
            image = generate_image(summary)

            save_json_memory(p1)
            save_sqlite_memory("player1", p1)

        st.write(summary)
        st.image(image, use_container_width=True)
