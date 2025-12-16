import streamlit as st
import random
import os
from math import pi
from owlready2 import get_ontology, Thing, DataProperty, default_world, World

# ==========================================================
# CONFIG
# ==========================================================
st.set_page_config(page_title="Ontology-Powered Area ITS", layout="wide")
SVG_DIR = "diagrams"
ONTOLOGY_PATH = "AreaTutor.owl"

# Create a new independent world to avoid SQLite conflicts
world = World()
onto = world.get_ontology(ONTOLOGY_PATH).load()

# Store ontology in session_state to reuse
st.session_state.onto = onto

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

if "hint_level" not in st.session_state:
    st.session_state.hint_level = 0

if "answered" not in st.session_state:
    st.session_state.answered = False

if "initialized" not in st.session_state:
    st.session_state.initialized = False

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
        # Ontology individual
        comp = onto.Square(f"square_{random.randint(1,1000)}")
        comp.side = [s]

    elif shape == "rectangle":
        l = random.randint(5, 15)
        w = random.randint(3, 10)
        dims = {"length": l, "width": w}
        expected = l * w
        comp = onto.Rectangle(f"rectangle_{random.randint(1,1000)}")
        comp.length = [l]
        comp.width = [w]

    elif shape == "triangle":
        b = random.randint(5, 15)
        h = random.randint(3, 10)
        dims = {"base": b, "height": h}
        expected = 0.5 * b * h
        comp = onto.Triangle(f"triangle_{random.randint(1,1000)}")
        comp.base = [b]
        comp.height = [h]

    elif shape == "parallelogram":
        b = random.randint(5, 15)
        h = random.randint(3, 10)
        dims = {"base": b, "height": h}
        expected = b * h
        comp = onto.Parallelogram(f"parallelogram_{random.randint(1,1000)}")
        comp.base = [b]
        comp.height = [h]

    elif shape == "trapezium":
        a = random.randint(4, 10)
        b2 = random.randint(a + 2, a + 10)
        h = random.randint(3, 10)
        dims = {"a": a, "b": b2, "height": h}
        expected = 0.5 * (a + b2) * h
        comp = onto.Trapezium(f"trapezium_{random.randint(1,1000)}")
        comp.a = [a]
        comp.b = [b2]
        comp.height = [h]

    elif shape == "circle":
        r = random.randint(3, 10)
        dims = {"radius": r}
        expected = pi * r * r
        comp = onto.Circle(f"circle_{random.randint(1,1000)}")
        comp.radius = [r]

    return {
        "shape": shape,
        "dims": dims,
        "expected": round(expected, 2)
    }

# ==========================================================
# LOAD NEW QUESTION
# ==========================================================
def load_new_problem():
    shape = min(
        st.session_state.student_mastery,
        key=lambda s: st.session_state.student_mastery[s]
    )

    st.session_state.current_shape = shape
    st.session_state.displayed_problem = generate_problem(shape)
    st.session_state.feedback = ""
    st.session_state.hint_level = 0
    st.session_state.answered = False

if not st.session_state.initialized:
    load_new_problem()
    st.session_state.initialized = True

# ==========================================================
# SVG DISPLAY WITH PROPORTIONAL LABEL FONT
# ==========================================================
def display_svg(shape_name, dims):
    import re
    path = os.path.join(SVG_DIR, f"{shape_name}.svg")
    if not os.path.exists(path):
        st.write(f"SVG for {shape_name} not found")
        return
    with open(path, "r") as f:
        svg_content = f.read()

    # Remove width/height attributes for scaling
    svg_content = re.sub(r'width="[^"]+"', '', svg_content)
    svg_content = re.sub(r'height="[^"]+"', '', svg_content)

    # Fixed proportional font size
    font_size = 12

    labels = ""
    if shape_name == "square":
        s = dims['side']
        labels += f'<text x="100" y="40" font-size="{font_size}" fill="black">s={s}</text>'
    elif shape_name == "rectangle":
        l, w = dims['length'], dims['width']
        labels += f'<text x="125" y="25" font-size="{font_size}" fill="black">l={l}</text>'
        labels += f'<text x="7" y="85" font-size="{font_size}" fill="black">w={w}</text>'
    elif shape_name == "triangle":
        b, h = dims['base'], dims['height']
        labels += f'<text x="125" y="165" font-size="{font_size}" fill="black">b={b}</text>'
        labels += f'<text x="130" y="95" font-size="{font_size}" fill="red">h={h}</text>'
    elif shape_name == "parallelogram":
        b, h = dims['base'], dims['height']
        labels += f'<text x="125" y="165" font-size="{font_size}" fill="black">b={b}</text>'
        labels += f'<text x="105" y="105" font-size="{font_size}" fill="red">h={h}</text>'
    elif shape_name == "trapezium":
        a, b_val, h = dims['a'], dims['b'], dims['height']
        labels += f'<text x="125" y="40" font-size="{font_size}" fill="black">a={a}</text>'
        labels += f'<text x="125" y="165" font-size="{font_size}" fill="black">b={b_val}</text>'
        labels += f'<text x="130" y="105" font-size="{font_size}" fill="red">h={h}</text>'
    elif shape_name == "circle":
        r = dims['radius']
        labels += f'<text x="190" y="150" font-size="{font_size}" fill="red">r={r}</text>'

    svg_content = svg_content.replace("</svg>", labels + "</svg>")

    container = f'''
    <div style="width:650px; overflow:auto; margin-bottom:20px;">
        {svg_content}
    </div>
    '''
    st.components.v1.html(container, height=700)

# ==========================================================
# CHECK ANSWER
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

    if abs(user_input - expected) < 0.01:
        st.session_state.feedback = "✅ Correct! Click **Next Question** to continue."
        st.session_state.student_mastery[shape] = min(
            100, st.session_state.student_mastery[shape] + 10
        )
        st.session_state.answered = True
    else:
        st.session_state.feedback = "❌ Incorrect. Try again or use a hint."

# ==========================================================
# NEXT QUESTION
# ==========================================================
def next_question():
    if not st.session_state.answered:
        return
    load_new_problem()

# ==========================================================
# HINTS
# ==========================================================
def give_hint():
    if st.session_state.answered:
        return
    st.session_state.hint_level += 1
    shape = st.session_state.current_shape

    if st.session_state.hint_level == 1:
        st.session_state.feedback = f"💡 Recall the area formula for a {shape}."
    elif st.session_state.hint_level == 2:
        formulas = {
            "square": "Area = side²",
            "rectangle": "Area = length × width",
            "triangle": "Area = ½ × base × height",
            "parallelogram": "Area = base × height",
            "trapezium": "Area = ½ × (a + b) × height",
            "circle": "Area = π × r²"
        }
        st.session_state.feedback = f"📐 {formulas[shape]}"
    else:
        st.session_state.feedback = "No more hints."

# ==========================================================
# UI
# ==========================================================
st.title("📐 Ontology-Powered Intelligent Tutoring System")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.subheader("📊 Mastery Levels")
    for s, v in st.session_state.student_mastery.items():
        colour = "🟥" if v < 50 else "🟨" if v < 85 else "🟩"
        st.write(f"{s.capitalize():<15} {v}% {colour}")

    st.subheader("🧑‍🏫 Feedback")
    st.info(st.session_state.feedback or "Awaiting answer...")

# ---------- MAIN ----------
left, right = st.columns([1.2, 1.8])

problem = st.session_state.displayed_problem
dims = problem["dims"]
shape = problem["shape"]

with left:
    st.markdown("### Question")

    if shape == "square":
        st.write(f"Find the area of a square with side **{dims['side']}** units.")
    elif shape == "rectangle":
        st.write(f"Find the area of a rectangle with length **{dims['length']}** and width **{dims['width']}**.")
    elif shape == "triangle":
        st.write(f"Find the area of a triangle with base **{dims['base']}** and height **{dims['height']}**.")
    elif shape == "parallelogram":
        st.write(f"Find the area of a parallelogram with base **{dims['base']}** and height **{dims['height']}**.")
    elif shape == "trapezium":
        st.write(f"Find the area of a trapezium with bases **{dims['a']}**, **{dims['b']}** and height **{dims['height']}**.")
    elif shape == "circle":
        st.write(f"Find the area of a circle with radius **{dims['radius']}**.")

    answer = st.text_input(
        "Enter your answer:",
        key="answer_input",
        disabled=st.session_state.answered
    )

    b1, b2, b3 = st.columns(3)
    with b1:
        st.button(
            "Check Answer",
            on_click=check_answer,
            args=(answer,),
            disabled=st.session_state.answered,
            key="btn_check"
        )
    with b2:
        st.button(
            "Hint",
            on_click=give_hint,
            disabled=st.session_state.answered,
            key="btn_hint"
        )
    with b3:
        st.button(
            "Next Question",
            on_click=next_question,
            disabled=not st.session_state.answered,
            key="btn_next"
        )

with right:
    st.markdown("### Diagram")
    display_svg(shape, dims)
