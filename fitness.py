import logging
import os
import streamlit as st
from agno.agent import Agent
from agno.models.groq import Groq
from agno.run.agent import RunOutput
from agno.tools.duckduckgo import DuckDuckGoTools

logger = logging.getLogger(__name__)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


def _format_run_output(run: RunOutput, label: str) -> str:
    """Human-readable summary of an agent run (content, tools, metrics)."""
    parts: list[str] = [f"=== {label} ==="]
    parts.append(f"agent_name={run.agent_name!r} model={run.model!r} run_id={run.run_id!r}")
    if run.content is not None:
        c = run.content
        text = c if isinstance(c, str) else str(c)
        parts.append("--- assistant content ---")
        parts.append(text if len(text) <= 12000 else text[:12000] + "\n… [truncated]")
    if run.tools:
        parts.append("--- tool calls ---")
        for t in run.tools:
            parts.append(f"  • {t.tool_name} args={t.tool_args}")
            if t.result:
                r = t.result
                parts.append(f"    result: {r}" if len(r) <= 4000 else f"    result: {r[:4000]}…")
            if t.tool_call_error:
                parts.append("    (tool error)")
    if run.metrics is not None:
        parts.append(f"--- run metrics --- {run.metrics}")
    if run.messages:
        parts.append(f"--- message trace ({len(run.messages)} messages) ---")
        for msg in run.messages[-8:]:
            role = getattr(msg, "role", None) or getattr(msg, "name", "?")
            body = getattr(msg, "content", msg)
            if isinstance(body, list):
                body = str(body)
            s = body if isinstance(body, str) else str(body)
            parts.append(f"  [{role}] {s[:1500]}{'…' if len(s) > 1500 else ''}")
    return "\n".join(parts)


def _log_agent_run(label: str, run: RunOutput) -> None:
    logger.info("\n%s", _format_run_output(run, label))

# Groq reads GROQ_API_KEY from the environment (see https://console.groq.com/keys)
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except (FileNotFoundError, RuntimeError):
    pass

# Default: llama-3.3-70b-versatile. Override with env GROQ_MODEL_ID if you prefer another Groq model.
_GROQ_MODEL_ID = os.getenv("GROQ_MODEL_ID", "llama-3.3-70b-versatile")

# Dietary Planner Agent
dietary_planner = Agent(
    model=Groq(id=_GROQ_MODEL_ID),
    description="Creates personalized dietary plans based on user input.",
    instructions=[
        "Generate a diet plan with breakfast, lunch, dinner, and snacks.",
        "Consider dietary preferences like Keto, Vegetarian, or Low Carb.",
        "Ensure proper hydration and electrolyte balance.",
        "Provide nutritional breakdown including macronutrients and vitamins.",
        "Suggest meal preparation tips for easy implementation.",
        "If necessary, search the web using DuckDuckGo for additional information.",
    ],
    tools=[DuckDuckGoTools()],
    markdown=True,
)

# Function to get a personalized meal plan
def get_meal_plan(age, weight, height, activity_level, dietary_preference, fitness_goal):
    prompt = (f"Create a personalized meal plan for a {age}-year-old person, weighing {weight}kg, "
              f"{height}cm tall, with an activity level of '{activity_level}', following a "
              f"'{dietary_preference}' diet, aiming to achieve '{fitness_goal}'.")
    out = dietary_planner.run(prompt)
    _log_agent_run("Dietary Planner", out)
    return out

# Fitness Trainer Agent
fitness_trainer = Agent(
    model=Groq(id=_GROQ_MODEL_ID),
    description="Generates customized workout routines based on fitness goals.",
    instructions=[
        "Create a workout plan including warm-ups, main exercises, and cool-downs.",
        "Adjust workouts based on fitness level: Beginner, Intermediate, Advanced.",
        "Consider weight loss, muscle gain, endurance, or flexibility goals.",
        "Provide safety tips and injury prevention advice.",
        "Suggest progress tracking methods for motivation.",
        "If necessary, search the web using DuckDuckGo for additional information.",
    ],
    tools=[DuckDuckGoTools()],
    markdown=True,
)

# Function to get a personalized fitness plan
def get_fitness_plan(age, weight, height, activity_level, fitness_goal):
    prompt = (f"Generate a workout plan for a {age}-year-old person, weighing {weight}kg, "
              f"{height}cm tall, with an activity level of '{activity_level}', "
              f"aiming to achieve '{fitness_goal}'. Include warm-ups, exercises, and cool-downs.")
    out = fitness_trainer.run(prompt)
    _log_agent_run("Fitness Trainer", out)
    return out

# Team Lead Agent (combines both meal and fitness plans)
team_lead = Agent(
    model=Groq(id=_GROQ_MODEL_ID),
    description="Combines diet and workout plans into a holistic health strategy.",
    instructions=[
        "Merge personalized diet and fitness plans for a comprehensive approach, Use Tables if possible.",
        "Ensure alignment between diet and exercise for optimal results.",
        "Suggest lifestyle tips for motivation and consistency.",
        "Provide guidance on tracking progress and adjusting plans over time."
    ],
    markdown=True
)

# Function to get a full health plan
def get_full_health_plan(name, age, weight, height, activity_level, dietary_preference, fitness_goal):
    meal_run = get_meal_plan(age, weight, height, activity_level, dietary_preference, fitness_goal)
    fitness_run = get_fitness_plan(age, weight, height, activity_level, fitness_goal)

    meal_text = meal_run.content if isinstance(meal_run.content, str) else str(meal_run.content or "")
    fitness_text = fitness_run.content if isinstance(fitness_run.content, str) else str(fitness_run.content or "")

    team_out = team_lead.run(
        f"Greet the customer, {name}\n\n"
        f"User Information: {age} years old, {weight}kg, {height}cm, activity level: {activity_level}.\n\n"
        f"Fitness Goal: {fitness_goal}\n\n"
        f"Meal Plan:\n{meal_text}\n\n"
        f"Workout Plan:\n{fitness_text}\n\n"
        f"Provide a holistic health strategy integrating both plans."
    )
    _log_agent_run("Team Lead", team_out)
    return team_out, meal_run, fitness_run


# Set up Streamlit UI with a fitness theme
st.set_page_config(page_title="AI Health & Fitness Plan", page_icon="🏋️‍♂️", layout="wide")

if not os.getenv("GROQ_API_KEY"):
    st.error(
        "Missing **GROQ_API_KEY**. Set it before running, e.g. "
        "`export GROQ_API_KEY=...` in your shell, or add `GROQ_API_KEY` to `.streamlit/secrets.toml`."
    )
    st.stop()

# Custom Styles for a Fitness and Health Theme
st.markdown("""
    <style>
        .title {
            text-align: center;
            font-size: 48px;
            font-weight: bold;
            color: #FF6347;
        }
        .subtitle {
            text-align: center;
            font-size: 24px;
            color: #4CAF50;
        }
        .sidebar {
            background-color: #F5F5F5;
            padding: 20px;
            border-radius: 10px;
        }
        .content {
            padding: 20px;
            background-color: #E0F7FA;
            border-radius: 10px;
            margin-top: 20px;
        }
        .btn {
            display: inline-block;
            background-color: #FF6347;
            color: white;
            padding: 10px 20px;
            text-align: center;
            border-radius: 5px;
            font-weight: bold;
            text-decoration: none;
            margin-top: 10px;
        }
        .goal-card {
            padding: 20px;
            margin: 10px;
            background-color: #FFF;
            border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
        }
    </style>
""", unsafe_allow_html=True)

# Title and Subtitle
st.markdown('<h1 class="title">🏋️‍♂️ AI Health & Fitness Plan Generator</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Personalized fitness and nutrition plans to help you achieve your health goals!</p>', unsafe_allow_html=True)

st.sidebar.header("⚙️ Health & Fitness Inputs")
st.sidebar.subheader("Personalize Your Fitness Plan")

# User inputs for personal information and fitness goals
age = st.sidebar.number_input("Age (in years)", min_value=10, max_value=100, value=25)
weight = st.sidebar.number_input("Weight (in kg)", min_value=30, max_value=200, value=70)
height = st.sidebar.number_input("Height (in cm)", min_value=100, max_value=250, value=170)
activity_level = st.sidebar.selectbox("Activity Level", ["Low", "Moderate", "High"])
dietary_preference = st.sidebar.selectbox("Dietary Preference", ["Keto", "Vegetarian", "Low Carb", "Balanced"])
fitness_goal = st.sidebar.selectbox("Fitness Goal", ["Weight Loss", "Muscle Gain", "Endurance", "Flexibility"])
show_agent_logs = st.sidebar.checkbox("Show agent run logs in UI", value=True)

# Divider for aesthetics
st.markdown("---")

# Displaying the user's inputted fitness profile
st.markdown("### 🏃‍♂️ Personal Fitness Profile")
name = st.text_input("What's your name?", "John Doe")

# Button to generate the full health plan
if st.sidebar.button("Generate Health Plan"):
    if not age or not weight or not height:
        st.sidebar.warning("Please fill in all required fields.")
    else:
        with st.spinner("💥 Generating your personalized health & fitness plan..."):
            full_health_plan, meal_run, fitness_run = get_full_health_plan(
                name, age, weight, height, activity_level, dietary_preference, fitness_goal
            )

        st.subheader("Your Personalized Health & Fitness Plan")
        st.markdown(full_health_plan.content)

        st.info("This is your customized health and fitness strategy, including meal and workout plans.")

        if show_agent_logs:
            st.subheader("Agent run logs")
            with st.expander("Dietary Planner — full output", expanded=False):
                st.code(_format_run_output(meal_run, "Dietary Planner"), language=None)
            with st.expander("Fitness Trainer — full output", expanded=False):
                st.code(_format_run_output(fitness_run, "Fitness Trainer"), language=None)
            with st.expander("Team Lead — full output", expanded=False):
                st.code(_format_run_output(full_health_plan, "Team Lead"), language=None)

        # Motivational Message
        st.markdown("""
            <div class="goal-card">
                <h4>🏆 Stay Focused, Stay Fit!</h4>
                <p>Consistency is key! Keep pushing yourself, and you will see results. Your fitness journey starts now!</p>
            </div>
        """, unsafe_allow_html=True)
