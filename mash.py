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
st.caption("A quiet glimpse into your future")

st.markdown("""
<style>

/* Background */
body {
    background-color: #f7f3ea;
}

/* Page animation */
.page {
    animation: fadeIn 0.45s ease both;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Book container */
.book {
    background: #fffdf8;
    padding: 1.75rem 2rem;
    border-radius: 18px;
    box-shadow: 0 14px 32px rgba(0,0,0,0.08);
    margin-bottom: 2rem;
}

/* Chapter labels */
.chapter {
    font-family: "Georgia", serif;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-size: 0.8rem;
    color: #8b6f47;
    margin-bottom: 0.25rem;
}

/* Story text */
.story-text {
    font-family: "Georgia", serif;
    font-size: 1.05rem;
    line-height: 1.7;
    color: #2f2f2f;
    margin-bottom: 0.6rem;
}

/* Cards */
.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
}

.result-card {
    background: #faf7f1;
    border-radius: 14px;
    padding: 1rem 1.25rem;
    box-shadow: 0 6px 14px rgba(0,0,0,0.06);
    border-left: 5px solid #c2a76d;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.result-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 24px rgba(0,0,0,0.12);
}

.card-label {
    font-size: 0.7rem;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: #8b6f47;
}

.card-value {
    font-size: 1.05rem;
    font-weight: 600;
}

/* Dice */
.dice {
    font-size: 3rem;
    text-align: center;
}

/* Footer */
.footer {
    text-align: center;
    font-size: 0.75rem;
    color: #8b6f47;
    margin-top: 2rem;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# HELPERS
# -----------------------------
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
# PROLOGUE — CATEGORIES
# -----------------------------
if st.session_state.stage == "categories":
    st.markdown('<div class="page book">', unsafe_allow_html=True)
    st.markdown('<div class="chapter">Prologue</div>', unsafe_allow_html=True)
    st.subheader("Choose the pieces of your future")

    cats = st.text_input(
        "Separate them with commas",
        "House, Job, Spouse, Kids, Car, City"
    )

    if st.button("✨ Begin Your Story"):
        st.session_state.categories = [c.strip() for c in cats.split(",")]
        st.session_state.answers = {c: [] for c in st.session_state.categories}
        st.session_state.stage = "answers"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# CHAPTER I — ANSWERS
# -----------------------------
if st.session_state.stage == "answers":
    st.markdown('<div class="page book">', unsafe_allow_html=True)
    st.markdown('<div class="chapter">Chapter I</div>', unsafe_allow_html=True)
    st.subheader("Fill the possibilities")

    for cat in st.session_state.categories:
        st.markdown(f"**{cat}**")
        for i in range(3):
            v = st.text_input(f"Option {i+1}", key=f"{cat}_{i}")
            if v and v not in st.session_state.answers[cat]:
                st.session_state.answers[cat].append(v)

    if st.button("📜 Seal Your Fate"):
        st.session_state.stage = "count"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# CHAPTER II — DICE COUNT
# -----------------------------
if st.session_state.stage == "count":
    st.markdown('<div class="page book">', unsafe_allow_html=True)
    st.markdown('<div class="chapter">Chapter II</div>', unsafe_allow_html=True)
    st.subheader("Let chance decide")

    st.caption("Watch the die roll… when it feels right, let fate stop it.")

    if "rolling" not in st.session_state:
        st.session_state.rolling = True
        st.session_state.start = time.time()

    dice = random.randint(1, 6)
    st.markdown(f'<div class="dice">🎲 {dice}</div>', unsafe_allow_html=True)

    if st.button("🕯️ Let Fate Decide"):
        st.session_state.count = dice
        st.session_state.stage = "result"
        st.rerun()

    time.sleep(0.4)
    st.rerun()

# -----------------------------
# FINAL — STORY
# -----------------------------
if st.session_state.stage == "result":
    st.markdown('<div class="page book">', unsafe_allow_html=True)
    st.markdown('<div class="chapter">Chapter III</div>', unsafe_allow_html=True)
    st.subheader("Your MASH Future")

    results = {
        cat: eliminate_to_one(st.session_state.answers[cat], st.session_state.count)
        for cat in st.session_state.categories
    }

    st.markdown('<div class="card-grid">', unsafe_allow_html=True)
    for k, v in results.items():
        st.markdown(f"""
        <div class="result-card">
            <div class="card-label">{k}</div>
            <div class="card-value">{v}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("📖 Turn the Page"):
        story = " ".join([
            "At first, life settles gently into place.",
            f"You live in {results.get('House','somewhere')}.",
            f"You work as {results.get('Job','something')}.",
            "In time, things grow complicated.",
            "Eventually, you find your balance again."
        ])
        st.session_state.story = story

    if st.session_state.story:
        st.markdown('<div class="chapter">Chapter IV</div>', unsafe_allow_html=True)
        st.subheader("A Day in the Life")

        for sentence in st.session_state.story.split(". "):
            st.markdown(f'<div class="story-text">{sentence}.</div>', unsafe_allow_html=True)
            time.sleep(0.15)

    st.markdown('<div class="footer">☕ Take your time. Futures are fragile things.</div>', unsafe_allow_html=True)

    if st.button("🔁 Start a New Life"):
        reset_game()

    st.markdown('</div>', unsafe_allow_html=True)
