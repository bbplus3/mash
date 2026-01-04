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
    return [
        {
            "role": "setting",
            "text": (
                f"Their life takes shape in a {results.get('House','home')} "
                f"in {results.get('City','a quiet place')}."
            )
        },
        {
            "role": "identity",
            "text": (
                f"They are known for being {madlibs.get('trait','steadfast')}, "
                f"balancing work as a {results.get('Job','professional')} "
                f"with a full home life."
            )
        },
        {
            "role": "relationships",
            "text": (
                f"Life is shared with {results.get('Spouse','a partner')} "
                f"and shaped by raising {results.get('Kids','no')} children."
            )
        },
        {
            "role": "disruption",
            "text": (
                f"At some point, {madlibs.get('twist','something unexpected shifts their rhythm')}."
            )
        },
        {
            "role": "daily texture",
            "text": (
                f"Simple routines—like {madlibs.get('habit','small daily rituals')}—"
                f"become grounding moments."
            )
        },
        {
            "role": "resolution",
            "text": (
                f"Over time, they find contentment in {madlibs.get('favorite','the life they built')}, "
                f"moving forward together."
            )
        },
    ]


# -----------------------------
# FALLBACK STORY (NO LLM)
# -----------------------------
def build_fallback_story(outline):
    #return "\n\n".join(outline.values())
    return "\n\n".join(outline)

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
        context_so_far = ""   # 🔹 STEP 3: rolling memory

        facts = "\n".join([f"{k}: {v}" for k, v in results.items()])

        for section in outline:
            prompt = f"""
You are expanding ONE paragraph of a cozy life story.

Story so far (do NOT repeat this content):
{context_so_far}

Paragraph role: {section['role']}

STRICT RULES:
- Do NOT mention the town, state, or house unless role == "setting"
- Do NOT restate family size unless role == "relationships"
- Do NOT reuse phrases like "in the heart of", "humble", "filled with laughter", "sanctuary"
- Assume the reader already knows the setting
- Write 2–3 sentences MAX
- Focus ONLY on this paragraph’s role
- Third-person, past or present tense
- Tone: {STYLE_DESCRIPTORS.get(style)}

Facts (do not change):
{facts}

Base paragraph:
{section['text']}

Rewrite with variation and specificity.
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.55,
            )

            paragraph = response.choices[0].message.content.strip()

            expanded_sections.append(paragraph)

            # 🔹 STEP 3: accumulate memory
            context_so_far += paragraph + "\n\n"

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
