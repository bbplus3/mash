import os
os.environ["STREAMLIT_SERVER_ENABLE_FILE_WATCHER"] = "false"

import streamlit as st
import time
import random

# -----------------------------
# PAGE SETUP
# -----------------------------
st.set_page_config(page_title="MASH-LIBS", layout="centered")
st.title("🏠 MASH-LIBS")

# -----------------------------
# HELPERS
# -----------------------------
def eliminate_to_one(options, count):
    if not options:
        return "unknown"
    count = max(1, count)
    idx = 0
    opts = options.copy()
    while len(opts) > 1:
        idx = (idx + count - 1) % len(opts)
        opts.pop(idx)
    return opts[0]

def reset_game():
    st.session_state.clear()
    st.rerun()

# -----------------------------
# SESSION INIT
# -----------------------------
if "stage" not in st.session_state:
    st.session_state.stage = "categories"
    st.session_state.categories = []
    st.session_state.answers = {}
    st.session_state.count = None
    st.session_state.story = None

# -----------------------------
# STAGE 1 — CATEGORIES
# -----------------------------
if st.session_state.stage == "categories":
    st.header("Step 1: Choose Categories")

    cats = st.text_input(
        "Enter categories (comma-separated)",
        "House, Job, Spouse, Kids, Car, City"
    )

    if st.button("Confirm Categories"):
        st.session_state.categories = [c.strip() for c in cats.split(",")]
        st.session_state.answers = {c: [] for c in st.session_state.categories}
        st.session_state.stage = "answers"
        st.rerun()

# -----------------------------
# STAGE 2 — ANSWERS
# -----------------------------
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

# -----------------------------
# STAGE 3 — COUNT
# -----------------------------
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

# -----------------------------
# STYLE SYSTEM
# -----------------------------
STYLE_ADJECTIVES = {
    "Neutral": {},
    "Whimsical": {
        "House": "a delightfully impractical",
        "Job": "an oddly charming",
        "City": "a storybook-like",
    },
    "Romantic": {
        "House": "a warm, inviting",
        "Job": "a fulfilling",
        "City": "a quietly beautiful",
    },
    "Chaotic": {
        "House": "a questionably stable",
        "Job": "a wildly unpredictable",
        "City": "a barely contained",
    },
    "Serious": {
        "House": "a well-established",
        "Job": "a demanding",
        "City": "a structured",
    },
}

# -----------------------------
# MAD-LIB SUGGESTIONS
# -----------------------------
MADLIB_SUGGESTIONS = {
    "trait": ["fearlessly optimistic", "quietly brilliant", "chaotically creative"],
    "habit": ["journaling at night", "talking to plants", "midnight brainstorming"],
    "twist": ["everything changes overnight", "a secret finally emerges"],
    "favorite": ["a quiet café", "stormy afternoons", "old books"],
    "animal": ["black cat", "golden retriever", "horse"],
    "number": ["three", "seven", "too many"],
}

def random_madlib(key):
    return random.choice(MADLIB_SUGGESTIONS.get(key, ["something unexpected"]))

# -----------------------------
# STORY BUILDER (LOCAL)
# -----------------------------
def build_story(results, style, madlibs):
    adj = STYLE_ADJECTIVES.get(style, {})
    parts = []

    def decorate(cat, val):
        return f"{adj.get(cat,'')} {val}".strip()

    if "House" in results:
        parts.append(f"You live in {decorate('House', results['House'])}.")

    if "City" in results:
        parts.append(f"Life unfolds in {decorate('City', results['City'])}.")

    if "Job" in results:
        parts.append(f"Your days revolve around working as {decorate('Job', results['Job'])}.")

    if "Spouse" in results:
        parts.append(f"You share your life with {results['Spouse']}.")

    if "Kids" in results:
        parts.append(f"Your household includes {results['Kids']} kids.")

    if "Car" in results:
        parts.append(f"You get around using {results['Car']}.")

    for k, v in results.items():
        if k not in {"House", "City", "Job", "Spouse", "Kids", "Car"}:
            parts.append(f"{k} continues to shape your life through {v}.")

    if madlibs.get("trait"):
        parts.append(f"You are known for being {madlibs['trait']}.")

    if madlibs.get("habit"):
        parts.append(f"A recurring part of your routine involves {madlibs['habit']}.")

    if madlibs.get("twist"):
        parts.append(f"Over time, {madlibs['twist']}.")

    if madlibs.get("favorite"):
        parts.append(f"You hold a particular fondness for {madlibs['favorite']}.")

    if madlibs.get("animal"):
        parts.append(f"Life is further complicated by the presence of a {madlibs['animal']}.")

    if madlibs.get("number"):
        parts.append(f"This chapter of your life seems destined to repeat itself {madlibs['number']} times.")

    return " ".join(parts).replace("..", ".")

# -----------------------------
# IMAGE PROMPT
# -----------------------------
def build_image_prompt(results, style, madlibs):
    core = ", ".join(results.values())
    extras = ", ".join(v for v in madlibs.values() if v)
    return (
        f"illustrated life scene, {style.lower()} tone, "
        f"{core}, {extras}, soft lighting, storybook digital art"
    )

# -----------------------------
# FINAL RESULT
# -----------------------------
if st.session_state.stage == "result":
    st.header("🎉 Your MASH Future")

    results = {
        cat: eliminate_to_one(st.session_state.answers[cat], st.session_state.count)
        for cat in st.session_state.categories
    }

    for k, v in results.items():
        st.write(f"**{k}:** {v}")

    st.divider()
    st.subheader("Mad-Lib Extras")

    madlibs = {}
    for key in MADLIB_SUGGESTIONS:
        col1, col2 = st.columns([4, 1])
        with col1:
            madlibs[key] = st.text_input(key.capitalize(), key=f"ml_{key}")
        with col2:
            if st.button("🎲", key=f"rand_{key}"):
                st.session_state[f"ml_{key}"] = random_madlib(key)
                st.rerun()

    style = st.selectbox(
        "Narrative Style",
        ["Neutral", "Whimsical", "Romantic", "Chaotic", "Serious"]
    )

    if st.button("📖 Generate Story"):
        st.session_state.story = build_story(results, style, madlibs)

    if st.session_state.story:
        st.subheader("📖 A Day in the Life")
        st.write(st.session_state.story)

    if st.button("🖼️ Generate Image"):
        try:
            from diffusers import StableDiffusionPipeline
            import torch

            with st.spinner("Generating image..."):
                pipe = StableDiffusionPipeline.from_pretrained(
                    "runwayml/stable-diffusion-v1-5",
                    torch_dtype=torch.float32
                )
                pipe.to("cpu")

                prompt = build_image_prompt(results, style, madlibs)
                image = pipe(prompt, num_inference_steps=20).images[0]
                st.image(image)

        except Exception:
            st.warning("Image generation unavailable.")

    if st.button("Play Again"):
        reset_game()
