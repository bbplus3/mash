import os
os.environ["STREAMLIT_SERVER_ENABLE_FILE_WATCHER"] = "false"

import streamlit as st
import time, random, sqlite3

# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------
st.set_page_config(page_title="MASH", layout="centered")
st.title("🏠 MASH")

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
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

# --------------------------------------------------
# SESSION INIT
# --------------------------------------------------
if "stage" not in st.session_state:
    st.session_state.stage = "categories"
    st.session_state.categories = []
    st.session_state.answers = {}
    st.session_state.count = None

if "story" not in st.session_state:
    st.session_state.story = None
# --------------------------------------------------
# STAGE 1 — CATEGORIES
# --------------------------------------------------
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
# STYLE SYSTEM
# --------------------------------------------------
STYLE_ADJECTIVES = {
    "Neutral": {
        "House": "a",
        "Job": "",
        "City": "",
    },
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

# --------------------------------------------------
# STORY BUILDER
# --------------------------------------------------
def build_story(results, style, madlibs):
    adj = STYLE_ADJECTIVES.get(style, {})
    parts = []

    def a(cat, val):
        return f"{adj.get(cat,'')} {val}".strip()

    if "House" in results and "City" in results:
        parts.append(f"Life unfolds in {a('House', results['House'])} located in {a('City', results['City'])}.")
    elif "House" in results:
        parts.append(f"Life unfolds in {a('House', results['House'])}.")
    elif "City" in results:
        parts.append(f"Life unfolds in {a('City', results['City'])}.")

    if "Job" in results:
        parts.append(f"Work centers around {a('Job', results['Job'])} career.")

    if "Spouse" in results:
        parts.append(f"Life is shared with {results['Spouse']}.")

    if "Kids" in results:
        parts.append(f"The household includes {results['Kids']} kids.")

    if "Car" in results:
        parts.append(f"Daily travel happens by {results['Car']}.")

    # Extra categories
    for k, v in results.items():
        if k not in {"House", "City", "Job", "Spouse", "Kids", "Car"}:
            parts.append(f"{k} plays a role through {v}.")

    # Mad-lib bonuses
    if madlibs.get("trait"):
        parts.append(f"This person is known for being {madlibs['trait']}.")
    if madlibs.get("habit"):
        parts.append(f"A defining habit involves {madlibs['habit']}.")
    if madlibs.get("twist"):
        parts.append(f"Unexpectedly, {madlibs['twist']}.")
    if madlibs.get("favorite"):
        parts.append(f"They especially value {madlibs['favorite']}.")

    return " ".join(parts)

# --------------------------------------------------
# IMAGE PROMPT
# --------------------------------------------------
def build_image_prompt(results, style, madlibs):
    core = list(results.values())
    extras = ", ".join(v for v in madlibs.values() if v)
    return (
        f"illustrated life scene, {style.lower()} tone, "
        + ", ".join(core)
        + (f", {extras}" if extras else "")
        + ", soft lighting, storybook digital art"
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

    st.divider()
    st.subheader("✏️ Mad-Lib Story Extras (Optional)")

    madlibs = {
        "trait": st.text_input("Defining personality trait"),
        "habit": st.text_input("Recurring habit"),
        "twist": st.text_input("Unexpected twist"),
        "favorite": st.text_input("Favorite thing or place"),
    }

    style = st.selectbox(
        "Narrative Style",
        ["Neutral", "Whimsical", "Romantic", "Chaotic", "Serious"]
    )

    if st.button("📖 A Day in the Life"):
        #story = build_story(results, style, madlibs)
        #st.subheader("Your Story")
        #st.write(story)
        st.session_state.story = build_story(results, style, madlibs)

    if st.button("🖼️ Show Me"):
        from diffusers import StableDiffusionPipeline
        import torch

        with st.spinner("Loading image model..."):
            pipe = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch.float32,
                safety_checker=None
            )
            pipe.to("cpu")

        prompt = build_image_prompt(results, style, madlibs)
        image = pipe(prompt, num_inference_steps=20).images[0]
        st.image(image)

    if st.session_state.story:
        st.subheader("📖 A Day in the Life")
        st.write(st.session_state.story) 

    if st.button("Play Again"):
        reset_game()
