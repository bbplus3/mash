import os
os.environ["STREAMLIT_SERVER_ENABLE_FILE_WATCHER"] = "false"

import streamlit as st
import time, random, sqlite3, json
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import pipeline

# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------
st.set_page_config(page_title="MASH", layout="centered")
st.title("🏠 MASH")

# --------------------------------------------------
# MODELS (CPU SAFE)
# --------------------------------------------------
@st.cache_resource
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")

@st.cache_resource
def load_llm():
    return pipeline("text2text-generation", model="google/flan-t5-base")

embedder = load_embedder()
llm = load_llm()

# --------------------------------------------------
# IMAGE MODEL (LAZY LOADED)
# --------------------------------------------------
@st.cache_resource
def load_image_model():
    from diffusers import StableDiffusionPipeline
    import torch

    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float32,
        safety_checker=None
    )
    pipe.to("cpu")
    return pipe

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def eliminate_to_one(options, count):
    if not options:
        return "❌ No answer provided"
    if count <= 0:
        count = 1

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
# SESSION INIT
# --------------------------------------------------
if "stage" not in st.session_state:
    st.session_state.stage = "categories"
    st.session_state.categories = []
    st.session_state.answers = {}
    st.session_state.count = None

# --------------------------------------------------
# STAGE 1 — CATEGORIES
# --------------------------------------------------
if st.session_state.stage == "categories":
    st.header("Step 1: Choose Categories")

    cats = st.text_input(
        "Enter categories (comma-separated)",
        "House, Spouse, Job, Kids, Car"
    )

    if st.button("Confirm Categories"):
        st.session_state.categories = [c.strip() for c in cats.split(",")]
        st.session_state.answers = {c: [] for c in st.session_state.categories}
        st.session_state.stage = "answers"
        st.rerun()

# --------------------------------------------------
# STAGE 2 — ANSWERS
# --------------------------------------------------
if st.session_state.stage == "answers":
    st.header("Step 2: Enter Answers (3 per category)")

    for cat in st.session_state.categories:
        st.subheader(cat)
        for i in range(3):
            v = st.text_input(f"{cat} – Option {i+1}", key=f"{cat}_{i}")
            if v and v not in st.session_state.answers[cat]:
                st.session_state.answers[cat].append(v)

    if st.button("Lock Answers"):
        missing = [c for c, v in st.session_state.answers.items() if not v]
        if missing:
            st.error(f"Missing answers for: {', '.join(missing)}")
        else:
            st.session_state.stage = "count"
            st.rerun()

# --------------------------------------------------
# STAGE 3 — COUNT
# --------------------------------------------------
if st.session_state.stage == "count":
    st.header("Step 3: Counting")

    if "tally" not in st.session_state:
        st.session_state.tally = 0
        st.session_state.start_time = time.time()

    if st.button("➕ Add Tally"):
        st.session_state.tally += 1

    st.metric("Current Count", st.session_state.tally)

    if time.time() - st.session_state.start_time >= 3:
        if st.button("STOP"):
            st.session_state.count = max(1, st.session_state.tally)
            st.session_state.stage = "result"
            st.rerun()

# --------------------------------------------------
# MEMORY (SQLITE)
# --------------------------------------------------
DB_PATH = "mash_memory.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            category TEXT,
            value TEXT
        )
        """)

def save_memory(results):
    with sqlite3.connect(DB_PATH) as conn:
        for k, v in results.items():
            conn.execute(
                "INSERT INTO memory (category, value) VALUES (?, ?)",
                (k, v)
            )

def load_memory(limit=6):
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            "SELECT category, value FROM memory"
        ).fetchall()[-limit:]

init_db()

# --------------------------------------------------
# RAG CONTEXT
# --------------------------------------------------
def retrieve_context(results):
    texts = [f"{k}: {v}" for k, v in results.items()]
    for k, v in load_memory():
        texts.append(f"Past {k}: {v}")

    emb = embedder.encode(texts)
    scores = np.dot(emb, emb[-1])
    top = np.argsort(scores)[-5:]
    return "\n".join(texts[i] for i in top)

# --------------------------------------------------
# NARRATIVE STYLES
# --------------------------------------------------
NARRATIVE_STYLES = {
    "Neutral": "Objective and factual",
    "Whimsical": "Playful and imaginative",
    "Romantic": "Warm and emotional",
    "Chaotic": "Absurd and surreal",
    "Serious": "Grounded and realistic"
}

# --------------------------------------------------
# JSON-STRUCTURED GENERATION (LLM)
# --------------------------------------------------
def generate_structured_future(context, style):
    prompt = f"""
Return ONLY valid JSON.

Schema:
{{
  "housing": "",
  "job": "",
  "spouse": "",
  "kids": "",
  "car": ""
}}

Rules:
- Use ONLY the facts below
- One short phrase per field
- No extra text
- Tone: {NARRATIVE_STYLES[style]}

Facts:
{context}
"""

    output = llm(
        prompt,
        max_new_tokens=180,
        temperature=0.3,
        do_sample=False
    )[0]["generated_text"]

    try:
        return json.loads(output[output.find("{"):output.rfind("}")+1])
    except Exception:
        return {
            "housing": "unknown housing",
            "job": "unknown job",
            "spouse": "unknown partner",
            "kids": "no kids",
            "car": "unknown transportation"
        }

# --------------------------------------------------
# JSON → STORY (NO LLM)
# --------------------------------------------------
def structured_json_to_story(data, style):
    return (
        f"Life unfolds in a {data['housing']}, shaped by working as a {data['job']}. "
        f"Days are shared with {data['spouse']}, while {data['kids']} kids bring rhythm "
        f"to the household. Getting around in a {data['car']} fits naturally into this "
        f"{style.lower()} future."
    )

# --------------------------------------------------
# IMAGE PROMPT
# --------------------------------------------------
def build_image_prompt(data, style):
    return (
        f"illustrated life scene, {style.lower()} tone, "
        f"{data['housing']}, {data['job']}, "
        f"{data['spouse']}, {data['kids']} kids, "
        f"{data['car']}, soft lighting, digital art, no text"
    )

# --------------------------------------------------
# FINAL RESULT
# --------------------------------------------------
if st.session_state.stage == "result":
    st.header("🎉 Your MASH Future")

    results = {
        cat: eliminate_to_one(st.session_state.answers[cat], st.session_state.count)
        for cat in st.session_state.categories
    }

    for k, v in results.items():
        st.write(f"**{k}:** {v}")

    style = st.selectbox("Narrative Style", list(NARRATIVE_STYLES.keys()))

    if st.button("📖 Generate Story"):
        with st.spinner("Writing your story..."):
            context = retrieve_context(results)
            structured = generate_structured_future(context, style)
            story = structured_json_to_story(structured, style)
            save_memory(results)

        st.subheader("Your Story")
        st.write(story)

    if st.button("🖼️ Generate Image (Optional)"):
        with st.spinner("Loading image model (first time only)..."):
            pipe = load_image_model()
            prompt = build_image_prompt(structured, style)
            image = pipe(prompt, num_inference_steps=20).images[0]
            st.image(image, caption="Your MASH Future")

    if st.button("Play Again"):
        reset_game()
