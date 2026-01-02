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
    house = results.get("House", "")
    job = results.get("Job", "")
    spouse = results.get("Spouse", "")
    kids = results.get("Kids", "")
    car = results.get("Car", "")
    city = results.get("City", "")

    parts = []

    if house and city:
        parts.append(f"Life unfolds in a {house} located in {city}.")
    elif house:
        parts.append(f"Life unfolds in a {house}.")
    elif city:
        parts.append(f"Life unfolds in {city}.")

    if job:
        parts.append(f"Work centers around a career as a {job}.")

    if spouse:
        parts.append(f"Life is shared with {spouse}.")

    if kids:
        parts.append(f"The household includes {kids} kids.")

    if car:
        parts.append(f"Daily travel happens by {car}.")

    # Handle any EXTRA categories gracefully
    handled = {"House", "Job", "Spouse", "Kids", "Car", "City"}
    for cat, val in results.items():
        if cat not in handled:
            parts.append(f"{cat} is defined by {val}.")

    return " ".join(parts)


STYLE_DECORATORS = {
    "Neutral": "",
    "Whimsical": " The days feel slightly magical, as if the universe is in on the joke.",
    "Romantic": " There is a sense of warmth and connection woven through everyday moments.",
    "Chaotic": " Nothing about this life follows a predictable pattern, and that feels exactly right.",
    "Serious": " The life is steady, deliberate, and built on clear choices."
}

def apply_style(story, style):
    return story + STYLE_DECORATORS.get(style, "")

# --------------------------------------------------
# IMAGE PROMPT
# --------------------------------------------------
def build_image_prompt(results, style):
    core = []

    if "House" in results:
        core.append(results["House"])
    if "City" in results:
        core.append(results["City"])
    if "Job" in results:
        core.append(results["Job"])
    if "Car" in results:
        core.append(results["Car"])

    extras = [f"{k.lower()} {v}" for k, v in results.items()
              if k not in {"House", "City", "Job", "Car"}]

    return (
        f"whimsical illustrated life scene, "
        f"{style.lower()} tone, "
        + ", ".join(core + extras)
        + ", soft lighting, storybook style, digital art"
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
