import os
os.environ["STREAMLIT_SERVER_ENABLE_FILE_WATCHER"] = "false"

import streamlit as st
import time
import random

# -----------------------------
# PAGE SETUP
# -----------------------------
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
    st.session_state.story = None
    st.session_state.expanded_story = None

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
STYLE_DESCRIPTORS = {
    "Neutral": "gentle and grounded",
    "Whimsical": "lighthearted and storybook-like",
    "Romantic": "warm, reflective, and emotional",
    "Chaotic": "energetic, unpredictable, and playful",
    "Serious": "measured, thoughtful, and calm",
}

# -----------------------------
# STORY OUTLINE (DETERMINISTIC)
# -----------------------------
def build_story_outline(results, madlibs):
    animal = madlibs.get("animal")
    number = madlibs.get("number")

    outline = {}

    outline["opening"] = (
        f"Your life unfolds in a {results.get('House','home')} "
        f"located in {results.get('City','a place')}. "
        f"You are known for being {madlibs.get('trait','yourself')}."
    )

    outline["routine"] = (
        f"Your days are shaped by working as {results.get('Job','something')} "
        f"and sharing life with {results.get('Spouse','someone')}. "
        f"A familiar part of your routine includes {madlibs.get('habit','simple comforts')}."
    )

    outline["conflict"] = (
        f"Life doesn’t stay predictable for long, when "
        f"{madlibs.get('twist','something unexpected happens')}."
    )

    if animal and number:
        outline["growth"] = (
            f"During this time, you find yourself caring for {number} {animal}"
            f"{'' if str(number)=='1' else 's'}, adjusting to the added responsibility."
        )
    else:
        outline["growth"] = (
            f"You slowly adapt, learning how to balance change with stability."
        )

    outline["resolution"] = (
        f"Eventually, things settle. With {results.get('Kids','no')} kids, "
        f"daily life moves forward, often traveling by {results.get('Car','your own means')}, "
        f"and finding comfort in {madlibs.get('favorite','the small things')}."
    )

    return outline

# -----------------------------
# FALLBACK STORY (NO LLM)
# -----------------------------
def build_fallback_story(outline):
    return "\n\n".join(outline.values())

# -----------------------------
# LLM EXPANSION (OPTIONAL)
# -----------------------------
def expand_with_llm(outline, style, results):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        expanded_sections = []

        facts = "\n".join([f"{k}: {v}" for k, v in results.items()])

        for section in outline.values():
            prompt = f"""
You are expanding a cozy life story.

Rules:
- Do NOT add or change facts
- Do NOT repeat phrases
- Write 2–3 sentences
- Third-person perspective
- Tone: {STYLE_DESCRIPTORS.get(style)}

Facts:
{facts}

Base text:
{section}

Expand gently.
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.65,
            )

            expanded_sections.append(
                response.choices[0].message.content.strip()
            )

        return "\n\n".join(expanded_sections)

    except Exception:
        return None

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
    st.subheader("Story Extras")

    madlibs = {
        "trait": st.text_input("Defining personality trait"),
        "habit": st.text_input("Recurring habit"),
        "twist": st.text_input("Unexpected twist"),
        "favorite": st.text_input("Favorite thing or place"),
        "animal": st.text_input("Pet animal"),
        "number": st.text_input("How many of them"),
    }

    style = st.selectbox(
        "Narrative Style",
        list(STYLE_DESCRIPTORS.keys())
    )

    if st.button("📖 Tell My Story"):
        outline = build_story_outline(results, madlibs)
        st.session_state.story = build_fallback_story(outline)

        expanded = expand_with_llm(outline, style, results)
        st.session_state.expanded_story = expanded

    if st.session_state.expanded_story:
        st.subheader("📖 A Day in the Life")
        st.write(st.session_state.expanded_story)
    elif st.session_state.story:
        st.subheader("📖 A Day in the Life")
        st.write(st.session_state.story)

    if st.button("Play Again"):
        reset_game()
