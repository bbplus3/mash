import os
os.environ["STREAMLIT_SERVER_ENABLE_FILE_WATCHER"] = "false"

import streamlit as st
import time
import random

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(
    page_title="MASH-LIBS",
    page_icon="🏠",
    layout="centered"
)

# =============================
# GLOBAL STYLES
# =============================
st.markdown("""
<style>
body {
    background-color: #f4f6f8;
}
h1 {
    color: #2b6777;
}
h2, h3 {
    color: #355f6b;
}
.card {
    padding: 1.25rem;
    border-radius: 14px;
    background-color: #ffffff;
    box-shadow: 0 6px 18px rgba(0,0,0,0.08);
    margin-bottom: 1.2rem;
}
.soft {
    color: #6c757d;
    font-size: 0.9rem;
}
.result-box {
    background-color: #f8fafc;
    border-left: 6px solid #2b6777;
    padding: 1rem;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# =============================
# HELPERS
# =============================
def card(title, subtitle=None):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)

def end_card():
    st.markdown('</div>', unsafe_allow_html=True)

def eliminate_to_one(options, count):
    if not options:
        return "unknown"
    idx = 0
    opts = options.copy()
    while len(opts) > 1:
        idx = (idx + count - 1) % len(opts)
        opts.pop(idx)
    return opts[0]

def reset_game():
    st.session_state.clear()
    st.rerun()

# =============================
# SESSION INIT
# =============================
if "stage" not in st.session_state:
    st.session_state.stage = "categories"
    st.session_state.categories = []
    st.session_state.answers = {}
    st.session_state.story = None
    st.session_state.count = 1

STAGES = ["categories", "answers", "count", "result"]
st.progress((STAGES.index(st.session_state.stage)+1)/len(STAGES))

st.title("🏠 MASH-LIBS")
st.caption("A playful glimpse into your wildly specific future")

# =============================
# STAGE 1 — CATEGORIES
# =============================
if st.session_state.stage == "categories":
    card("🧩 Step 1: Choose Your Life Categories",
         "These define the dimensions of your future")

    cats = st.text_input(
        "Categories (comma-separated)",
        "House, Job, Spouse, Kids, Car, City"
    )

    if st.button("✨ Lock Categories"):
        st.session_state.categories = [c.strip() for c in cats.split(",")]
        st.session_state.answers = {c: [] for c in st.session_state.categories}
        st.session_state.stage = "answers"
        st.rerun()

    end_card()

# =============================
# STAGE 2 — ANSWERS
# =============================
if st.session_state.stage == "answers":
    card("✍️ Step 2: Fill In the Possibilities",
         "Three options per category works best")

    for cat in st.session_state.categories:
        st.markdown(f"**{cat}**")
        cols = st.columns(3)
        for i in range(3):
            with cols[i]:
                v = st.text_input(
                    f"Option {i+1}",
                    key=f"{cat}_{i}"
                )
                if v and v not in st.session_state.answers[cat]:
                    st.session_state.answers[cat].append(v)

    if st.button("🔒 Finalize Options"):
        if any(not v for v in st.session_state.answers.values()):
            st.error("Every category needs at least one option.")
        else:
            st.session_state.stage = "count"
            st.rerun()

    end_card()

# =============================
# STAGE 3 — COUNTING
# =============================
if st.session_state.stage == "count":
    card("🔢 Step 3: The Count",
         "Tap rhythmically… then stop")

    if "tally" not in st.session_state:
        st.session_state.tally = 0
        st.session_state.start = time.time()

    if st.button("➕ Count"):
        st.session_state.tally += 1

    st.metric("Current Count", st.session_state.tally)

    if time.time() - st.session_state.start > 2:
        if st.button("🛑 STOP"):
            st.session_state.count = max(1, st.session_state.tally)
            st.session_state.stage = "result"
            st.rerun()

    end_card()

# =============================
# STORY GENERATION
# =============================
def build_story(results, style, madlibs):
    lines = []

    lines.append(f"You live in a {results.get('House','place')}.")

    if "City" in results:
        lines.append(f"Life unfolds in {results['City']}.")

    if "Job" in results:
        lines.append(f"Your days revolve around working as {results['Job']}.")

    if "Spouse" in results:
        lines.append(f"You share your life with {results['Spouse']}.")

    if "Kids" in results:
        lines.append(f"Your household includes {results['Kids']} kids.")

    if madlibs.get("animal"):
        n = madlibs.get("number","1")
        lines.append(f"In the near future, you welcome {n} {madlibs['animal']} as a pet.")

    return " ".join(lines)

# =============================
# FINAL RESULT
# =============================
if st.session_state.stage == "result":
    card("🎉 Your Future Revealed")

    results = {
        cat: eliminate_to_one(st.session_state.answers[cat], st.session_state.count)
        for cat in st.session_state.categories
    }

    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    cols = st.columns(2)
    for i,(k,v) in enumerate(results.items()):
        cols[i%2].markdown(f"**{k}** → *{v}*")
    st.markdown('</div>', unsafe_allow_html=True)

    end_card()

    # MADLIBS
    card("🧩 Story Extras", "Optional details that enrich the narrative")
    madlibs = {}
    for key in ["animal","number"]:
        madlibs[key] = st.text_input(key.capitalize())
    end_card()

    style = st.selectbox(
        "🎭 Narrative Style",
        ["Neutral","Whimsical","Romantic","Chaotic","Serious"]
    )

    if st.button("📖 Generate Story"):
        with st.spinner("Writing your story…"):
            st.session_state.story = build_story(results, style, madlibs)

    if st.session_state.story:
        card("📖 A Day in the Life")
        st.write(st.session_state.story)
        end_card()

    if st.button("🔁 Play Again"):
        reset_game()
