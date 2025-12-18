import streamlit as st
import random
import os
from math import pi
from owlready2 import World

# ==========================================================
# CONFIG
# ==========================================================
st.set_page_config(page_title="Ontology-Powered Area ITS", layout="wide")
SVG_DIR = "diagrams"
ONTOLOGY_PATH = "AreaTutorII.owl"

# ==========================================================
# ONTOLOGY LOAD
# ==========================================================
world = World()
onto = world.get_ontology(ONTOLOGY_PATH).load()

def format_dims(dims):
    # Join key-value pairs with proper spacing
    return ", ".join(f"{k}: {v}" for k, v in dims.items())


def get_lesson_from_ontology(shape_name: str):
    # Map shape_name to Lesson individual
    lesson_map = {
        "square": "SquareLesson",
        "rectangle": "RectangleLesson",
        "triangle": "TriangleLesson",
        "parallelogram": "ParallelogramLesson",
        "trapezium": "TrapeziumLesson",
        "circle": "CircleLesson"
    }
    lesson_ind_name = lesson_map.get(shape_name.lower())
    if not lesson_ind_name:
        return None

    lesson_ind = onto.search_one(iri="*" + lesson_ind_name)
    if not lesson_ind:
        return None

    # Lesson text
    lesson_text = lesson_ind.lessonText[0] if lesson_ind.lessonText else "Lesson description not found."

    # Formula
    formula_ind = lesson_ind.explainsFormula[0] if lesson_ind.explainsFormula else None
    formula_text = formula_ind.formulaText[0] if formula_ind and formula_ind.formulaText else "Formula not found."

    # Worked examples
    worked_steps = []
    if lesson_ind.hasWorkedExample:
        for example in lesson_ind.hasWorkedExample:
            if example.stepText:
                worked_steps.append(example.stepText[0])
    if not worked_steps:
        worked_steps = ["No worked examples available."]

    return {
        "lesson_text": lesson_text,
        "formula_text": formula_text,
        "worked_steps": worked_steps
    }



# ==========================================================
# SESSION STATE INITIALISATION
# ==========================================================
if "student_mastery" not in st.session_state:
    st.session_state.student_mastery = {
        "square": 0,
        "rectangle": 0,
        "triangle": 0,
        "parallelogram": 0,
        "trapezium": 0,
        "circle": 0
    }

if "current_shape" not in st.session_state:
    st.session_state.current_shape = None

if "displayed_problem" not in st.session_state:
    st.session_state.displayed_problem = None

if "feedback" not in st.session_state:
    st.session_state.feedback = ""

if "hint_index" not in st.session_state:
    st.session_state.hint_index = 0

if "answered" not in st.session_state:
    st.session_state.answered = False

if "initialized" not in st.session_state:
    st.session_state.initialized = False

# --- Diagnostic mode state ---
if "diagnostic_mode" not in st.session_state:
    st.session_state.diagnostic_mode = False
if "diagnostic_questions" not in st.session_state:
    st.session_state.diagnostic_questions = []
if "diagnostic_index" not in st.session_state:
    st.session_state.diagnostic_index = 0
if "diagnostic_results" not in st.session_state:
    st.session_state.diagnostic_results = []

# ==========================================================
# PROBLEM GENERATION
# ==========================================================
def generate_problem(shape):
    dims = {}
    expected = 0.0

    if shape == "square":
        s = random.randint(3, 12)
        dims = {"side": s}
        expected = s * s

    elif shape == "rectangle":
        l = random.randint(5, 15)
        w = random.randint(3, 10)
        dims = {"length": l, "width": w}
        expected = l * w

    elif shape == "triangle":
        b = random.randint(5, 15)
        h = random.randint(3, 10)
        dims = {"base": b, "height": h}
        expected = 0.5 * b * h

    elif shape == "parallelogram":
        b = random.randint(5, 15)
        h = random.randint(3, 10)
        dims = {"base": b, "height": h}
        expected = b * h

    elif shape == "trapezium":
        a = random.randint(4, 10)
        b2 = random.randint(a + 2, a + 10)
        h = random.randint(3, 10)
        dims = {"a": a, "b": b2, "height": h}
        expected = 0.5 * (a + b2) * h

    elif shape == "circle":
        r = random.randint(3, 10)
        dims = {"radius": r}
        expected = pi * r * r

    return {
        "shape": shape,
        "dims": dims,
        "expected": round(expected, 2),
        "text": f"Find the area of {shape} with dimensions: {format_dims(dims)}"
    }

# ==========================================================
# DIAGNOSTIC SESSION INITIALIZATION
# ==========================================================
def start_diagnostic():
    st.session_state.diagnostic_mode = True
    st.session_state.diagnostic_index = 0
    st.session_state.diagnostic_results = []

    # Create 2 questions per shape and shuffle
    questions = []
    for shape in st.session_state.student_mastery.keys():
        for _ in range(2):
            questions.append(generate_problem(shape))
    random.shuffle(questions)
    st.session_state.diagnostic_questions = questions

    load_diagnostic_question()

# ==========================================================
# LOAD QUESTION
# ==========================================================
def load_new_problem():
    if st.session_state.diagnostic_mode:
        load_diagnostic_question()
        return

    shape = min(
        st.session_state.student_mastery,
        key=lambda s: st.session_state.student_mastery[s]
    )
    st.session_state.current_shape = shape
    st.session_state.displayed_problem = generate_problem(shape)
    st.session_state.feedback = ""
    st.session_state.answered = False
    st.session_state.hint_index = 0

def load_diagnostic_question():
    idx = st.session_state.diagnostic_index
    if idx >= len(st.session_state.diagnostic_questions):
        st.session_state.feedback = "📊 Diagnostic complete! See results below."
        st.session_state.current_shape = None
        st.session_state.displayed_problem = None
        st.session_state.answered = True
        return

    q = st.session_state.diagnostic_questions[idx]
    st.session_state.displayed_problem = q
    st.session_state.current_shape = q["shape"]
    st.session_state.feedback = ""
    st.session_state.answered = False
    st.session_state.hint_index = 0

# ==========================================================
# SKIP
# ==========================================================
def skip_question():
    if st.session_state.diagnostic_mode:
        st.session_state.diagnostic_results.append((st.session_state.current_shape, None))
        st.session_state.diagnostic_index += 1
        load_diagnostic_question()
    else:
        st.session_state.feedback = "⏭️ Question skipped."
        st.session_state.answered = False
        st.session_state.hint_index = 0
        load_new_problem()

# ==========================================================
# ANSWER CHECKING
# ==========================================================
def check_answer(user_input):
    if st.session_state.answered:
        return

    try:
        user_input = float(user_input)
    except:
        st.session_state.feedback = "⚠️ Please enter a valid number."
        return

    expected = st.session_state.displayed_problem["expected"]
    shape = st.session_state.current_shape

    correct = abs(user_input - expected) < 0.01

    if st.session_state.diagnostic_mode:
        st.session_state.diagnostic_results.append((shape, correct))
        st.session_state.feedback = "✅ Correct!" if correct else "❌ Incorrect."
        st.session_state.answered = True
    else:
        if correct:
            st.session_state.feedback = f"✅ Correct! {shape} area is right."
            st.session_state.student_mastery[shape] = min(
                100, st.session_state.student_mastery[shape] + 10
            )
            st.session_state.answered = True
        else:
            st.session_state.feedback = "❌ Incorrect. Try again or use a hint."

# ==========================================================
# DIAGNOSTIC FEEDBACK
# ==========================================================
def diagnostic_feedback():
    results = st.session_state.diagnostic_results
    if not results:
        st.info("No diagnostic session yet.")
        return

    st.subheader("📊 Diagnostic Results")
    for shape in st.session_state.student_mastery.keys():
        attempts = [r for r in results if r[0] == shape]
        correct = sum(1 for r in attempts if r[1])
        st.write(f"{shape.capitalize()}: {correct}/{len(attempts)} correct")

# ==========================================================
# SVG DISPLAY
# ==========================================================
def display_svg(shape_name, dims):
    import re
    path = os.path.join(SVG_DIR, f"{shape_name}.svg")
    if not os.path.exists(path):
        st.write("Diagram not available.")
        return

    with open(path, "r") as f:
        svg = f.read()

    svg = re.sub(r'width="[^"]+"', '', svg)
    svg = re.sub(r'height="[^"]+"', '', svg)

    font = 12
    labels = ""

    if shape_name == "square":
        labels += f'<text x="100" y="40" font-size="{font}">s={dims["side"]}</text>'
    elif shape_name == "rectangle":
        labels += f'<text x="125" y="25" font-size="{font}">l={dims["length"]}</text>'
        labels += f'<text x="5" y="85" font-size="{font}">w={dims["width"]}</text>'
    elif shape_name == "triangle":
        labels += f'<text x="120" y="165" font-size="{font}">b={dims["base"]}</text>'
        labels += f'<text x="130" y="95" font-size="{font}">h={dims["height"]}</text>'
    elif shape_name == "parallelogram":
        labels += f'<text x="120" y="165" font-size="{font}">b={dims["base"]}</text>'
        labels += f'<text x="105" y="105" font-size="{font}">h={dims["height"]}</text>'
    elif shape_name == "trapezium":
        labels += f'<text x="125" y="40" font-size="{font}">a={dims["a"]}</text>'
        labels += f'<text x="125" y="165" font-size="{font}">b={dims["b"]}</text>'
        labels += f'<text x="130" y="105" font-size="{font}">h={dims["height"]}</text>'
    elif shape_name == "circle":
        labels += f'<text x="190" y="150" font-size="{font}">r={dims["radius"]}</text>'

    svg = svg.replace("</svg>", labels + "</svg>")
    st.components.v1.html(
        f'<div style="width:650px; overflow:auto;">{svg}</div>',
        height=700
    )

# ==========================================================
# UI
# ==========================================================
st.title("📐 2D Shapes AreaTutor")

with st.sidebar:
    st.subheader("📊 Mastery Dashboard")
    for shape, score in st.session_state.student_mastery.items():
        icon = "🔴" if score < 40 else "🟡" if score < 80 else "🟢"
        st.write(f"{shape.capitalize():<15} {score}% {icon}")

    st.divider()
    st.subheader("🧑‍🏫 Feedback")
    st.info(st.session_state.feedback or "Awaiting student action…")

tab1, tab2 = st.tabs(["Practice", "Lessons"])

# ==========================================================
# PRACTICE TAB
# ==========================================================
with tab1:
    # Auto-start diagnostic if mastery empty
    if not st.session_state.initialized:
        st.info("📌 Preparing diagnostic session…")
        start_diagnostic()
        st.session_state.initialized = True

    left, right = st.columns([1.2, 1.8])
    problem = st.session_state.displayed_problem

    if problem:
        dims = problem["dims"]
        shape = problem["shape"]
        problem_text = problem.get("text", f"Find the area of {shape} with dimensions: {format_dims(dims)}")

        with left:
            session_type = "🧪 Diagnostic" if st.session_state.diagnostic_mode else "🎯 Adaptive"
            st.markdown(f"### {session_type} Question")
            st.write(problem_text)

            answer = st.text_input(
                "Enter your answer:",
                key="answer_input",
                disabled=st.session_state.answered
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.button("Check Answer",
                          on_click=check_answer,
                          args=(answer,),
                          disabled=st.session_state.answered)

            with c2:
                st.button("Hint", on_click=lambda: st.warning(f"💡 Hint: Use formula for {shape}"),
                          disabled=st.session_state.answered)

            with c3:
                st.button("Skip This Question", on_click=skip_question,
                          disabled=st.session_state.answered)

            with c4:
                st.button(
                    "Next Question",
                    on_click=lambda: (
                        st.session_state.__setitem__("diagnostic_index", st.session_state.diagnostic_index + 1)
                        if st.session_state.diagnostic_mode else None,
                        load_new_problem() if not st.session_state.diagnostic_mode else load_diagnostic_question()
                    ),
                    disabled=not st.session_state.answered
                )

        with right:
            st.subheader("Diagram")
            display_svg(shape, dims)

    else:
        st.info("No current problem.")

        # If diagnostic just finished, show results and provide button to start adaptive practice
        if st.session_state.diagnostic_results:
            diagnostic_feedback()
            if st.button("Start Adaptive Practice"):
                st.session_state.diagnostic_mode = False
                st.session_state.diagnostic_results = []
                load_new_problem()

# ==========================================================
# LESSONS TAB
# ==========================================================
with tab2:
    lesson_shape = st.selectbox(
        "Choose shape",
        ["square", "rectangle", "triangle",
         "parallelogram", "trapezium", "circle"]
    )

    if st.button("Start Lesson"):
        lesson = get_lesson_from_ontology(lesson_shape)
        if lesson:
            st.markdown("## 📘 Lesson")
            st.write(lesson["lesson_text"])
            st.code(lesson["formula_text"])
            
            st.markdown("### Worked Example")
            
            multi_step_text = "\n".join(lesson["worked_steps"])
            
            formatted_steps = multi_step_text.replace('\n', '  \n')
            
            for line in formatted_steps.split('  \n'):
                st.write("•", line)
        else:
            st.warning("No lesson found for this shape.")
