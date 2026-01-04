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
st.caption("A look into your future")
st.markdown("""
<style>

/* Page background */
body {
    background-color: #f7f3ea;
}

/* Main book container */
.book {
    background: #fffdf8;
    padding: 1.5rem 2rem;
    border-radius: 16px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.08);
    margin-bottom: 2rem;
}

/* Chapter headers */
.chapter {
    font-family: "Georgia", serif;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    font-size: 0.85rem;
    color: #8b6f47;
    margin-bottom: 0.3rem;
}

/* Story text */
.story-text {
    font-family: "Georgia", serif;
    font-size: 1.05rem;
    line-height: 1.7;
    color: #2f2f2f;
}

/* Card layout */
.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
    margin-top: 0.5rem;
}

.result-card {
    background: #faf7f1;
    border-radius: 14px;
    padding: 1rem 1.25rem;
    box-shadow: 0 6px 14px rgba(0,0,0,0.06);
    border-left: 5px solid #c2a76d;
}

.card-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #8b6f47;
    margin-bottom: 0.2rem;
}

.card-value {
    font-size: 1.05rem;
    font-weight: 600;
    color: #2f2f2f;
}


/* Buttons */
button {
    border-radius: 8px !important;
}

/* Image frame */
.illustration {
    border-radius: 14px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}

</style>
""", unsafe_allow_html=True)

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
INTRO_TEMPLATES = {
    "Neutral": [
        "Your life takes shape in {House}, setting the tone for everything that follows.",
        "You find yourself living in {House}, a place that quietly defines your days."
    ],
    "Whimsical": [
        "Somehow, you end up in {House}, and honestly, it feels exactly right.",
        "Against all odds, your story begins in {House}."
    ],
    "Romantic": [
        "Your story unfolds gently in {House}, where comfort and meaning intertwine.",
        "You build your life within {House}, a place filled with promise."
    ],
    "Chaotic": [
        "Nothing makes sense, yet there you are in {House}.",
        "Your life launches straight into madness from {House}."
    ],
    "Serious": [
        "Your life is firmly established in {House}.",
        "Everything begins with {House}, chosen with purpose."
    ],
}

WORK_TEMPLATES = {
    "default": [
        "Your days are shaped by working as {Job}.",
        "Much of your time is devoted to your work as {Job}."
    ]
}

RELATIONSHIP_TEMPLATES = {
    "spouse": [
        "You share your life with {Spouse}.",
        "{Spouse} stands beside you through it all."
    ],
    "kids_none": [
        "The household remains quiet, without children.",
        "It’s a life without kids, leaving room for other pursuits."
    ],
    "kids_some": [
        "Together, you raise {Kids} kids.",
        "Life stays busy with {Kids} kids in the mix."
    ]
}

CLOSING_TEMPLATES = {
    "Neutral": [
        "Altogether, this is the rhythm of your life.",
        "This is how your days ultimately unfold."
    ],
    "Whimsical": [
        "Strangely enough, it all works out.",
        "And somehow, it feels like exactly the right story."
    ],
    "Romantic": [
        "It’s a life rich with meaning and quiet joy.",
        "In the end, it feels deeply fulfilling."
    ],
    "Chaotic": [
        "Somehow, you survive it all.",
        "Whether it makes sense or not, this is your life."
    ],
    "Serious": [
        "It is a life built with intention.",
        "Everything follows a deliberate path."
    ],
}

def choose(template_list):
    return random.choice(template_list)

# STORY HELPER FUNCTIONS
def normalize_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def pluralize(word, count):
    if count == 1:
        return word
    return word + "s"

def kids_phrase(value):
    n = normalize_int(value)
    if n is None:
        return f"{value} kids"
    if n == 0:
        return "no kids"
    if n == 1:
        return "one kid"
    return f"{n} kids"

def pet_future_phrase(animal, number, style):
    n = normalize_int(number)

    if not animal:
        return None

    # Unknown or invalid number
    if n is None:
        return f"A {animal} enters your life and leaves a lasting impression."

    # Zero pets
    if n == 0:
        if style == "Chaotic":
            return f"You briefly consider getting a {animal}, but chaos intervenes."
        return f"For now, life continues without a pet."

    # One pet
    if n == 1:
        if style == "Romantic":
            return f"A single {animal} becomes a beloved companion."
        if style == "Chaotic":
            return f"One {animal} appears and immediately causes trouble."
        return f"A {animal} soon becomes part of your household."

    # Multiple pets
    pet_word = pluralize(animal, n)

    if style == "Whimsical":
        return f"You somehow end up caring for {n} {pet_word}, each with a personality of their own."
    if style == "Chaotic":
        return f"{n} {pet_word} take over your life in the most unpredictable way."
    if style == "Serious":
        return f"You take on responsibility for {n} {pet_word}, adjusting your routine accordingly."

    return f"You soon find yourself living alongside {n} {pet_word}."


# GRAMMAR HELPERS
def normalize_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def pluralize(word, n):
    if n == 1:
        return word
    if word.endswith("y"):
        return word[:-1] + "ies"
    return word + "s"


# NARRATIVE ARC TEMPLATES
ARC_TEMPLATES = {
    "rise": {
        "Neutral": [
            "At first, everything feels steady and predictable.",
            "Early on, life seems to settle into a comfortable rhythm."
        ],
        "Whimsical": [
            "At the beginning, everything feels oddly delightful.",
            "Early on, life feels like it’s humming along just fine."
        ],
        "Romantic": [
            "At first, life feels full of promise.",
            "In the beginning, everything feels gently aligned."
        ],
        "Chaotic": [
            "At first, things seem manageable—somehow.",
            "Early on, the chaos hasn’t fully revealed itself."
        ],
        "Serious": [
            "At the outset, everything appears well planned.",
            "In the beginning, the structure holds firm."
        ],
    },
    "conflict": {
        "Neutral": [
            "Over time, challenges begin to surface.",
            "Eventually, complications make themselves known."
        ],
        "Whimsical": [
            "Eventually, things get a little strange.",
            "Before long, reality throws in a curveball."
        ],
        "Romantic": [
            "In time, difficulties test this carefully built life.",
            "Eventually, not everything goes as smoothly as hoped."
        ],
        "Chaotic": [
            "Then things spiral—fast.",
            "Suddenly, nothing goes according to plan."
        ],
        "Serious": [
            "Inevitably, pressure begins to build.",
            "Over time, the cracks start to show."
        ],
    },
    "resolution": {
        "Neutral": [
            "In the end, you adapt and move forward.",
            "Ultimately, you find a way to make it work."
        ],
        "Whimsical": [
            "Somehow, it all comes together.",
            "Against all odds, things land on their feet."
        ],
        "Romantic": [
            "In the end, meaning emerges from it all.",
            "Ultimately, love and purpose prevail."
        ],
        "Chaotic": [
            "Somehow, you survive the madness.",
            "Whether it makes sense or not, this becomes your life."
        ],
        "Serious": [
            "In the end, stability is restored.",
            "Ultimately, discipline and resolve carry you through."
        ],
    }
}


def choose(options):
    return random.choice(options)

def build_story(results, style, madlibs):
    adj = STYLE_ADJECTIVES.get(style, {})
    story = []

    def decorate(cat):
        return f"{adj.get(cat, '')} {results[cat]}".strip()

    # =====================
    # RISE — Setup
    # =====================
    story.append(choose(ARC_TEMPLATES["rise"][style]))

    if "House" in results:
        story.append(f"You live in {decorate('House')}.")

    if "City" in results:
        story.append(f"Much of your life unfolds in {decorate('City')}.")

    if "Job" in results:
        story.append(f"Your days revolve around working as {decorate('Job')}.")

    # =====================
    # CONFLICT — Tension
    # =====================
    story.append(choose(ARC_TEMPLATES["conflict"][style]))

    if "Spouse" in results:
        story.append(f"You share this life with {results['Spouse']}.")

    if "Kids" in results:
        phrase = kids_phrase(results["Kids"])
        story.append(f"Your household includes {phrase}.")

    if madlibs.get("twist"):
        if style == "Chaotic":
            story.append(f"Without warning, {madlibs['twist']}.")
        else:
            story.append(f"Over time, {madlibs['twist']}.")

    # =====================
    # RESOLUTION — Meaning
    # =====================
    story.append(choose(ARC_TEMPLATES["resolution"][style]))

    if "Car" in results:
        story.append(f"You get around using {results['Car']}.")

    if madlibs.get("trait"):
        story.append(f"You are known for being {madlibs['trait']}.")

    if madlibs.get("habit"):
        story.append(f"A familiar habit of yours is {madlibs['habit']}.")

    if madlibs.get("favorite"):
        story.append(f"You hold a lasting fondness for {madlibs['favorite']}.")

    pet_line = pet_future_phrase(
        madlibs.get("animal"),
        madlibs.get("number"),
        style
    )

    if pet_line:
        story.append(pet_line)


    return " ".join(story).replace("..", ".")

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
    st.markdown('<div class="book">', unsafe_allow_html=True)
    st.markdown('<div class="chapter">Chapter I</div>', unsafe_allow_html=True)
    st.header("Your MASH Future")


    results = {
        cat: eliminate_to_one(st.session_state.answers[cat], st.session_state.count)
        for cat in st.session_state.categories
    }

    with st.container():
        st.markdown('<div class="card-grid">', unsafe_allow_html=True)

        for k, v in results.items():
            st.markdown(
                f"""
                <div class="result-card">
                    <div class="card-label">{k}</div>
                    <div class="card-value">{v}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown('</div>', unsafe_allow_html=True)




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
        st.markdown('<div class="chapter">Chapter II</div>', unsafe_allow_html=True)
        st.subheader("A Day in the Life")

        st.markdown(
            f'<div class="story-text">{st.session_state.story}</div>',
            unsafe_allow_html=True
        )


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
                st.markdown('<div class="chapter">Illustration</div>', unsafe_allow_html=True)
                st.image(image, use_container_width=True, output_format="PNG")

        except Exception:
            st.warning("Image generation unavailable.")

    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("Play Again"):
        reset_game()
