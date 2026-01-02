import os
os.environ["STREAMLIT_SERVER_ENABLE_FILE_WATCHER"] = "false"

import streamlit as st
import time

# PAGE SETUP
st.set_page_config(page_title="MASH", layout="centered")
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

if "story" not in st.session_state:
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
        "Job": "a deeply fulfilling",
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

STYLE_MADLIB_TONE = {
    "Neutral": lambda x: x,
    "Whimsical": lambda x: f"delightfully {x}",
    "Romantic": lambda x: f"deeply {x}",
    "Chaotic": lambda x: f"alarmingly {x}",
    "Serious": lambda x: f"notably {x}",
}

# -----------------------------
# STORY BUILDER
# -----------------------------
def build_story(results, style, madlibs):
    adj = STYLE_ADJECTIVES.get(style, {})
    tone = STYLE_MADLIB_TONE.get(style, lambda x: x)
    parts = []

    def styled(cat, val):
        return f"{adj.get(cat,'')} {val}".strip()

    if "House" in results and "City" in results:
        parts.append(
            f"Your life unfolds in {styled('House', results['House'])}, "
            f"set within {styled('City', results['City'])} surroundings."
        )

    if "Job" in results:
        parts.append(f"Your days revolve around {styled('Job', results['Job'])} work.")

    if "Spouse" in results:
        parts.append(f"You share this life with {results['Spouse']}.")

    if "Kids" in results:
        parts.append(f"Your household includes {results['Kids']} kids.")

    if "Car" in results:
        parts.append(f"You get around by {results['Car']}.")

    for k, v in results.items():
        if k not in {"House", "City", "Job", "Spouse", "Kids", "Car"}:
            parts.append(f"{k} plays a role through {v}.")

    if madlibs.get("trait"):
        parts.append(f"You are known for being {tone(madlibs['trait'])}.")
    if madlibs.get("habit"):
        parts.append(f"You have a habit of {tone(madlibs['habit'])}.")
    if madlibs.get("twist"):
        parts.append(f"Unexpectedly, {tone(madlibs['twist'])}.")
    if madlibs.get("favorite"):
        parts.append(f"You especially treasure {tone(madlibs['favorite'])}.")
    if madlibs.get("animal"):
        parts.append(f"A {tone(madlibs['animal'])} has become part of your life.")
    if madlibs.get("number"):
        parts.append(f"There are now {madlibs['number']} of them.")

    return " ".join(parts)

# -----------------------------
# IMAGE PROMPT BUILDER
# -----------------------------
def build_image_prompt(results, style, madlibs):
    core_scene = ", ".join(results.values())
    extras = []

    for v in madlibs.values():
        if v:
            extras.append(v)

    return (
        f"storybook illustration, {style.lower()} tone, "
        f"{core_scene}, "
        f"{', '.join(extras)}, "
        "cinematic lighting, soft focus, digital art"
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
    st.subheader("Mad-Lib Story Extras (Optional)")

    madlibs = {
        "trait": st.text_input("Defining personality trait"),
        "habit": st.text_input("Recurring habit"),
        "twist": st.text_input("Unexpected twist"),
        "favorite": st.text_input("Favorite thing or place"),
        "animal": st.text_input("Choose an animal"),
        "number": st.text_input("Type any number"),
    }

    style = st.selectbox(
        "Narrative Style",
        ["Neutral", "Whimsical", "Romantic", "Chaotic", "Serious"]
    )

    if st.button("📖 A Day in the Life"):
        st.session_state.story = build_story(results, style, madlibs)

    if st.button("🖼️ Show Me"):
        try:
            from diffusers import StableDiffusionPipeline
            import torch

            with st.spinner("Generating image..."):
                pipe = StableDiffusionPipeline.from_pretrained(
                    "runwayml/stable-diffusion-v1-5",
                    torch_dtype=torch.float32
                ).to("cpu")

                prompt = build_image_prompt(results, style, madlibs)
                image = pipe(prompt, num_inference_steps=20).images[0]
                st.image(image)

        except Exception:
            st.warning("Image generation is unavailable in this environment.")

    if st.session_state.story:
        st.subheader("📖 A Day in the Life")
        st.write(st.session_state.story)

    if st.button("Play Again"):
        reset_game()


