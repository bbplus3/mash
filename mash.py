import os
os.environ["STREAMLIT_SERVER_ENABLE_FILE_WATCHER"] = "false"

import streamlit as st
import time
import random

# -----------------------------
# SESSION STATE INITIALIZATION
# -----------------------------
DEFAULT_STATE = {
    "stage": "name",
    "player_name": "",
    "categories": [],
    "answers": {},
    "count": None,
    "story": None,
    "expanded_story": None,
    "tally": 0,
    "start_time": None,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

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
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def pluralize(word, count):
    try:
        count = int(count)
    except:
        return word
    if count == 1:
        return word
    if word.endswith("y"):
        return word[:-1] + "ies"
    return word + "s"

def nameize(text, name):
    return text.replace("they", name).replace("their", f"{name}'s")

# -----------------------------
# STAGE 0 — PLAYER NAME
# -----------------------------
if st.session_state.stage == "name":
    st.header("✨ Welcome to MASH-LIBS")
    st.write("Before we begin, tell us who this future belongs to.")

    name = st.text_input("Your name")

    if st.button("Begin"):
        if name.strip():
            st.session_state.player_name = name.strip()
            st.session_state.stage = "categories"
            st.rerun()
        else:
            st.error("Please enter a name to continue.")

# -----------------------------
# SESSION INIT
# -----------------------------
if "stage" not in st.session_state:
    st.session_state.stage = "name"
    st.session_state.player_name = ""
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
# STAGE 3 — DICE ROLL
# -----------------------------
if st.session_state.stage == "count":
    st.header("🎲 Fate Decides")

    if st.button("Roll the Dice"):
        st.session_state.count = random.randint(1, 6)
        st.success(f"You rolled a {st.session_state.count}!")
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

STYLE_TEMPLATES = {
    "Neutral": {
        "setting": [
            "{name} lives in a {House} in {City}.",
            "Life unfolds for {name} in a {House} located in {City}."
        ],
        "identity": [
            "Working as a {Job}, {name} balances responsibility with routine.",
            "{name} earns a living as a {Job}, shaping each day with intention."
        ],
        "relationships": [
            "{name} shares life with {Spouse} and raises {Kids} children.",
            "Family life centers around {Spouse} and {Kids} children."
        ],
    },
    "Whimsical": {
        "setting": [
            "Somehow, fate dropped {name} into a {House} in {City}.",
            "Of all places, {name} ended up in a charming {House} in {City}."
        ],
        "identity": [
            "As a {Job}, {name} navigates life with a {trait} streak.",
            "{name}'s days as a {Job} are anything but ordinary."
        ],
        "relationships": [
            "Life buzzes with {Kids} kids and the steady presence of {Spouse}.",
            "{Spouse} and {Kids} kids turn every day into an adventure."
        ],
    },
    "Serious": {
        "setting": [
            "{City} became home, with a {House} chosen carefully.",
            "{name} settled into a {House} in {City} after thoughtful decisions."
        ],
        "identity": [
            "{name}'s work as a {Job} demands focus and discipline.",
            "Professional life as a {Job} shapes much of {name}'s days."
        ],
        "relationships": [
            "{Spouse} and {Kids} children form the foundation of {name}'s life.",
            "Family responsibilities anchor each day."
        ],
    },
}

# -----------------------------
# STORY OUTLINE (DETERMINISTIC)
# -----------------------------
def build_story_outline(results, madlibs, name):
    return [
        {
            "role": "setting",
            "text": (
                f"{name}'s life takes shape in a {results.get('House','home')} "
                f"in {results.get('City','a quiet place')}."
            )
        },
        {
            "role": "identity",
            "text": (
                f"Known for being {madlibs.get('trait','steadfast')}, "
                f"{name} balances work as a {results.get('Job','professional')} "
                f"with a full home life."
            )
        },
        {
            "role": "relationships",
            "text": (
                f"Life is shared with {results.get('Spouse','a partner')}, "
                f"while raising {results.get('Kids','no')} children together."
            )
        },
        {
            "role": "disruption",
            "text": (
                f"At some point, {madlibs.get('twist','something unexpected shifts the rhythm of life')}."
            )
        },
        {
            "role": "daily texture",
            "text": (
                f"Simple routines—like {madlibs.get('habit','small daily rituals')}—"
                f"become grounding moments for {name}."
            )
        },
        {
            "role": "resolution",
            "text": (
                f"Over time, {name} finds contentment in "
                f"{madlibs.get('favorite','the life that has been built')}."
            )
        },
    ]

# -----------------------------
# FALLBACK STORY (NO LLM)
# -----------------------------
def build_refactored_summary(results, madlibs, style, name):
    sections = []

    templates = STYLE_TEMPLATES.get(style, STYLE_TEMPLATES["Neutral"])

    # --- Core Arc ---
    for role in ["setting", "identity", "relationships"]:
        if role in templates:
            sentence = random.choice(templates[role])
            sections.append(sentence.format(
                name=name,
                **results,
                **madlibs
            ))

    # --- Extra MASH Parameters (Car, custom categories, etc.) ---
    extras = []
    for k, v in results.items():
        if k not in ["House", "City", "Job", "Spouse", "Kids"]:
            extras.append(f"{name} ends up with {v} when it comes to {k.lower()}.")

    random.shuffle(extras)
    sections.extend(extras[:2])

    # --- Madlib Texture ---
    if madlibs.get("habit"):
        sections.append(
            f"A defining habit—{madlibs['habit']}—becomes part of everyday life."
        )

    if madlibs.get("animal") and madlibs.get("number"):
        animal = pluralize(madlibs["animal"], madlibs["number"])
        sections.append(
            f"Before long, {name} is caring for {madlibs['number']} {animal}, treating them like family."
        )

    # --- Resolution ---
    if madlibs.get("favorite"):
        sections.append(
            f"In the end, {name} finds the most joy in {madlibs['favorite']}."
        )

    return "\n\n".join(sections)

#def build_fallback_story(outline):
#    return "\n\n".join(
#        section.get("text", "")
#        for section in outline
#        if isinstance(section, dict)
#    )

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
        "trait": st.text_input("Personality trait"),
        "habit": st.text_input("Hobby or habit"),
        "twist": st.text_input("Plot twist"),
        "favorite": st.text_input("Favorite thing or place"),
        "animal": st.text_input("Name an animal"),
        "number": st.text_input("Pick a number"),
    }

    style = st.selectbox(
        "Narrative Style",
        list(STYLE_DESCRIPTORS.keys())
    )

    if st.button("📖 Tell My Story"):
        outline = build_story_outline(
            results,
            madlibs,
            st.session_state.player_name
        )
        #st.session_state.story = build_fallback_story(outline)
        st.session_state.story = build_refactored_summary(
            results,
            madlibs,
            style,
            st.session_state.player_name
        )

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
