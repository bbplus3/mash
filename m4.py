import os
os.environ["STREAMLIT_SERVER_ENABLE_FILE_WATCHER"] = "false"

import streamlit as st
import time, random, sqlite3
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
def load_llm():
    return pipeline("text2text-generation", model="google/flan-t5-base")

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
        return "Unknown"

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
        "House, Job, Spouse, Kids, Car"
    )

    if st.button("Confirm Categories"):
        st.session_state.categories = [c.strip() for c in cats.split(",") if c.strip()]
        st.session_state.answers = {c: [] for c in st.session_state.categories}
        st.session_state.stage = "answers"
        st.rerun()

# --------------------------------------------------
# STAGE 2 — ANSWERS
# --------------------------------------------------
if st.session_state.stage == "answers":
    st.header("Step 2: Enter Your Answers")

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
# NARRATIVE STYLES
# --------------------------------------------------
NARRATIVE_STYLES = {
    "Neutral": "objective and descriptive",
    "Whimsical": "playful and imaginative",
    "Romantic": "warm and emotional",
    "Chaotic": "absurd and surreal",
    "Serious": "grounded and realistic"
}

# --------------------------------------------------
# STORY GENERATION (DETERMINISTIC)
# --------------------------------------------------
def build_base_story(results):
    """
    Deterministically constructs a complete paragraph
    using ALL categories with NO omissions.
    """
    sentences = []

    for cat, val in results.items():
        c = cat.lower()

        if c in ["house", "home", "housing"]:
            sentences.append(f"Life unfolds in a {val}.")
        elif c in ["job", "career", "work"]:
            sentences.append(f"Daily life is shaped by working as {val}.")
        elif c in ["spouse", "partner", "relationship"]:
            sentences.append(f"Days are shared with {val}.")
        elif c in ["kids", "children"]:
            sentences.append(f"The household includes {val} kids.")
        elif c in ["car", "vehicle", "transportation"]:
            sentences.append(f"Getting around is done using {val}.")
        else:
            sentences.append(f"{cat} plays a role in the future as {val}.")

    return " ".join(sentences)

def polish_story(story, style):
    prompt = f"""
Rewrite the following paragraph in a {style.lower()} tone.
Do not add, remove, or alter facts.
Do not repeat phrases.
One paragraph only.

Paragraph:
{story}
"""
    out = llm(prompt, max_new_tokens=160, temperature=0.5)
    return out[0]["generated_text"].strip()

# --------------------------------------------------
# IMAGE PROMPT
# --------------------------------------------------
def build_image_prompt(results, style):
    details = ", ".join(f"{k.lower()} {v}" for k, v in results.items())
    return (
        f"illustrated life scene, {style.lower()} tone, "
        f"{details}, soft lighting, cinematic, digital art"
    )

# --------------------------------------------------
# FINAL RESULT
# --------------------------------------------------
if st.session_state.stage == "result":
    st.header("🎉 Your MASH Future")

    results = {}
    for cat in st.session_state.categories:
        results[cat] = eliminate_to_one(
            st.session_state.answers[cat],
            st.session_state.count
        )
        st.write(f"**{cat}:** {results[cat]}")

    style = st.selectbox("Narrative Style", list(NARRATIVE_STYLES.keys()))

    if st.button("📖 Generate Summary"):
        with st.spinner("Writing your story..."):
            base_story = build_base_story(results)
            summary = polish_story(base_story, style)

        st.subheader("Your Story")
        st.write(summary)

    st.divider()

    if st.button("🖼️ Generate Image (Optional)"):
        with st.spinner("Loading image model (first time only)..."):
            pipe = load_image_model()
            prompt = build_image_prompt(results, style)
            image = pipe(prompt, num_inference_steps=20).images[0]
            st.image(image, caption="Your MASH Future")

    if st.button("Play Again"):
        reset_game()
