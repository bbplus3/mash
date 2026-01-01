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

def reset_game():
    st.session_state.clear()
    st.rerun()

# --------------------------------------------------
# SESSION STATE INIT
# --------------------------------------------------

if "stage" not in st.session_state:
    st.session_state.stage = "categories"
    st.session_state.categories = []
    st.session_state.answers_p1 = {}
    st.session_state.answers_p2 = {}
    st.session_state.two_player = False
    st.session_state.count = None
    st.session_state.start_time = None
    st.session_state.tally = 0

# --------------------------------------------------
# STAGE 1 — CATEGORIES
# --------------------------------------------------

if st.session_state.stage == "categories":
    st.header("Step 1: Choose Categories")

    st.session_state.two_player = st.checkbox("Enable Player 2 (Two-Player Mode)")

    cats = st.text_input(
        "Enter categories (comma-separated)",
        "House, Spouse, Kids, Job, Car"
    )

    if st.button("Confirm Categories"):
        st.session_state.categories = [c.strip() for c in cats.split(",")]
        for c in st.session_state.categories:
            st.session_state.answers_p1[c] = []
            st.session_state.answers_p2[c] = []
        st.session_state.stage = "answers"
        st.rerun()

# --------------------------------------------------
# STAGE 2 — ANSWERS
# --------------------------------------------------

if st.session_state.stage == "answers":
    st.header("Step 2: Enter Answers")

    for cat in st.session_state.categories:
        st.subheader(cat)

        if st.session_state.two_player:
            col1, col2 = st.columns(2)
        else:
            col1 = st.container()
            col2 = None

        with col1:
            st.markdown("**Player 1** (2 good, 1 bad)")
            for i in range(3):
                v = st.text_input(
                    f"{cat} – Player 1 Option {i+1}",
                    key=f"p1_{cat}_{i}"
                )
                if v and v not in st.session_state.answers_p1[cat]:
                    st.session_state.answers_p1[cat].append(v)

        if st.session_state.two_player and col2:
            with col2:
                st.markdown("**Player 2** (2 good, 1 bad)")
                for i in range(3):
                    v = st.text_input(
                        f"{cat} – Player 2 Option {i+1}",
                        key=f"p2_{cat}_{i}"
                    )
                    if v and v not in st.session_state.answers_p2[cat]:
                        st.session_state.answers_p2[cat].append(v)

    if st.button("Lock Answers"):
        st.session_state.stage = "count_method"
        st.rerun()

# --------------------------------------------------
# STAGE 3 — COUNT METHOD
# --------------------------------------------------

if st.session_state.stage == "count_method":
    st.header("Step 3: Choose Counting Method")

    col1, col2 = st.columns(2)

    if col1.button("📱 Touch Tally"):
        st.session_state.stage = "tally"
        st.session_state.start_time = time.time()

    if col2.button("🎨 Swirl"):
        st.session_state.stage = "swirl"
        st.session_state.start_time = time.time()

# --------------------------------------------------
# TALLY MODE
# --------------------------------------------------

if st.session_state.stage == "tally":
    st.header("📱 Touch Tally Counter")

    st.write("Tap to add tally marks. Wait at least 3 seconds.")

    if st.button("➕ ADD TALLY", use_container_width=True):
        st.session_state.tally += 1

    st.metric("Current Count", st.session_state.tally)
    st.write("｜" * st.session_state.tally)

    if time.time() - st.session_state.start_time >= 3:
        if st.button("STOP"):
            st.session_state.count = max(1, st.session_state.tally)
            st.session_state.stage = "result"
            st.rerun()

# --------------------------------------------------
# SWIRL MODE (SIMULATED)
# --------------------------------------------------

if st.session_state.stage == "swirl":
    st.header("🎨 Drawing a Swirl")

    elapsed = time.time() - st.session_state.start_time
    radius = min(10, int(elapsed * 1.5))

    swirl_lines = []
    for y in range(-radius, radius + 1):
        line = ""
        for x in range(-radius * 2, radius * 2 + 1):
            if radius > 0 and abs(math.sqrt((x / 2) ** 2 + y ** 2) - radius) < 0.6:
                line += "●"
            else:
                line += " "
        swirl_lines.append(line)

    st.code("\n".join(swirl_lines))

    if elapsed < 3:
        st.warning("⏳ Wait at least 3 seconds")

    if elapsed >= 3 and st.button("STOP"):
        st.session_state.count = max(3, int(elapsed * random.randint(2, 4)))
        st.session_state.stage = "result"
        st.rerun()

# --------------------------------------------------
# FINAL RESULT
# --------------------------------------------------

#if st.session_state.stage == "result":
#    st.header("🎉 Your MASH Future")

#    count = st.session_state.count

    # MASH result
#    mash = eliminate_to_one(list("MASH"), count)
#    HOUSE_MAP = {"A": "Apartment", "S": "Shack", "H": "House"}

#    if mash in HOUSE_MAP:
#        st.success(f"🏠 House Type: {HOUSE_MAP[mash]}")

#    st.subheader("👤 Player 1")
#    for cat in st.session_state.categories:
#        result = eliminate_to_one(st.session_state.answers_p1[cat], count)
#        st.write(f"**{cat}:** {result}")

#    if st.session_state.two_player:
#        st.subheader("👤 Player 2")
#        for cat in st.session_state.categories:
#            result = eliminate_to_one(st.session_state.answers_p2[cat], count)
#            st.write(f"**{cat}:** {result}")

#    if st.button("Play Again"):
#        reset_game()

# --------------------------------------------------
# PERSISTENT MEMORY (JSON + SQLITE)
# --------------------------------------------------
MEMORY_DIR = "mash_memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

JSON_PATH = f"{MEMORY_DIR}/snapshots.json"
DB_PATH = f"{MEMORY_DIR}/mash_memory.db"

# JSON (quick snapshot history)
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

# SQLITE (long-term structured memory)
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

    if st.button("Play Again"):
        reset_game()
