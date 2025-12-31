import streamlit as st
import time
import random
import math

st.set_page_config(page_title="MASH", layout="centered")
st.title("🏠 MASH")

# HELPERS

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

EVIL_ANSWERS = {
    "House": ["Living in a cave", "Abandoned mall", "Haunted shed"],
    "Spouse": ["Marry a raccoon", "Sentient fog", "Unpaid wizard"],
    "Kids": ["47", "0", "99"],
    "Job": ["Unpaid wizard", "Professional toe model", "Dragon feeder"],
    "Car": ["Rusty shopping cart", "Unicycle", "Invisible car"]
}

# SESSION STATE INIT

if "stage" not in st.session_state:
    st.session_state.stage = "categories"
    st.session_state.categories = []
    st.session_state.answers_p1 = {}
    st.session_state.answers_ai = {}
    st.session_state.count = None
    st.session_state.start_time = None
    st.session_state.tally = 0

# STAGE 1 — CATEGORIES

if st.session_state.stage == "categories":
    st.header("Step 1: Choose Categories")

    cats = st.text_input(
        "Enter categories (comma-separated)",
        "House, Spouse, Kids, Job, Car"
    )

    if st.button("Confirm Categories"):
        st.session_state.categories = [c.strip() for c in cats.split(",")]
        for c in st.session_state.categories:
            st.session_state.answers_p1[c] = []
            st.session_state.answers_ai[c] = []
        st.session_state.stage = "answers"
        st.rerun()

# STAGE 2 — ANSWERS

if st.session_state.stage == "answers":
    st.header("Step 2: Enter Answers")

    for cat in st.session_state.categories:
        st.subheader(cat)
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Player 1 (2 good, 1 bad 😇)**")
            for i in range(3):
                v = st.text_input(f"{cat} – Option {i+1}", key=f"p1_{cat}_{i}")
                if v and v not in st.session_state.answers_p1[cat]:
                    st.session_state.answers_p1[cat].append(v)

        with col2:
            st.markdown("**Player 2 (AI 😈)**")
            if len(st.session_state.answers_ai[cat]) < 3:
                evil = EVIL_ANSWERS.get(cat, ["Chaos", "More chaos", "Ultimate chaos"])
                choice = random.choice(evil)
                st.session_state.answers_ai[cat].append(choice)
            for a in st.session_state.answers_ai[cat]:
                st.write(a)

    if st.button("Lock Answers"):
        st.session_state.stage = "count_method"
        st.rerun()

# STAGE 3 — COUNT METHOD

if st.session_state.stage == "count_method":
    st.header("Step 3: Choose Counting Method")

    col1, col2 = st.columns(2)

    if col1.button("📱 Touch Tally"):
        st.session_state.stage = "tally"
        st.session_state.start_time = time.time()

    if col2.button("🎨 Draw Swirl"):
        st.session_state.stage = "swirl"
        st.session_state.start_time = time.time()

# TALLY MODE

if st.session_state.stage == "tally":
    st.header("📱 Touch Tally Counter")

    st.write("Tap to add tally marks. Wait at least 3 seconds.")

    if st.button("➕ ADD TALLY", use_container_width=True):
        st.session_state.tally += 1

    st.metric("Current Count", st.session_state.tally)
    st.write("｜" * st.session_state.tally)

    if time.time() - st.session_state.start_time >= 3:
        if st.button("STOP"):
            st.session_state.count = max(1, st.session_state.tally)
            st.session_state.stage = "result"
            st.rerun()

# SWIRL MODE

if st.session_state.stage == "swirl":
    st.header("🎨 Drawing a Swirl...")

    if st.session_state.start_time is None:
        st.session_state.start_time = time.time()

    elapsed = time.time() - st.session_state.start_time

    st.write("Watch the swirl grow. Wait at least 3 seconds, then press STOP.")

    # Size grows with time
    radius = min(10, int(elapsed * 1.5))

    swirl_lines = []
    for y in range(-radius, radius + 1):
        line = ""
        for x in range(-radius * 2, radius * 2 + 1):
            if radius > 0 and abs(math.sqrt((x / 2) ** 2 + y ** 2) - radius) < 0.6:
                line += "●"
            else:
                line += " "
        swirl_lines.append(line)

    st.code("\n".join(swirl_lines))

    if elapsed < 3:
        st.warning("⏳ Wait at least 3 seconds before stopping")

    if elapsed >= 3 and st.button("STOP"):
        # Convert elapsed time to a reasonable count
        st.session_state.count = max(3, int(elapsed * random.randint(2, 4)))
        st.session_state.stage = "result"
        st.rerun()

# FINAL RESULT (RULE-CORRECT)

if st.session_state.stage == "result":
    st.header("🎉 Your MASH Future")

    count = st.session_state.count

    # MASH result
    mash = eliminate_to_one(list("MASH"), count)

    HOUSE_MAP = {
        "A": "Apartment",
        "S": "Shack",
        "H": "House"
    }

    if mash in HOUSE_MAP:
        st.success(f"🏠 House Type: {HOUSE_MAP[mash]}")

    # Category results
    for cat in st.session_state.categories:
        options = (
            st.session_state.answers_p1[cat]
            + st.session_state.answers_ai[cat]
        )
        result = eliminate_to_one(options, count)
        st.success(f"{cat}: {result}")

    # Sound effect
    st.markdown(
        """
        <audio autoplay>
            <source src="https://actions.google.com/sounds/v1/cartoon/wood_plank_flicks.ogg" type="audio/ogg">
        </audio>
        """,
        unsafe_allow_html=True
    )

    if st.button("Play Again"):
        reset_game()

