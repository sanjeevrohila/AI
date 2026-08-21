"""
Workout Plan Generator
A Streamlit app that generates personalized workout plans using Groq LLM API.
"""

import streamlit as st
from groq import Groq, APIConnectionError, APIStatusError, AuthenticationError
from typing import Optional


# ── Constants ────────────────────────────────────────────────────────────────

FITNESS_GOALS = ["Build muscle", "Lose fat", "General fitness", "Improve endurance"]
EXPERIENCE_LEVELS = ["Beginner", "Intermediate", "Advanced"]
EQUIPMENT_OPTIONS = ["No equipment", "Home dumbbells", "Full gym"]

SYSTEM_PROMPT = """
You are an expert certified personal trainer with 15 years of experience.
Your task is to generate a safe, realistic, and structured weekly workout plan.

STRICT RULES you must follow:
1. Respect the equipment constraint absolutely — if the user has no equipment, prescribe ONLY bodyweight exercises.
2. Respect the days per week — generate EXACTLY that many workout days, no more.
3. Respect the experience level — beginner plans must be simple; advanced plans can include compound lifts and periodisation.
4. If injuries or limitations are mentioned, AVOID exercises that stress those areas and add a ⚠️ disclaimer at the top.
5. Format output EXACTLY as:
   ## Weekly Workout Plan
   **Goal:** <goal> | **Level:** <level> | **Equipment:** <equipment>

   ### Day 1 – <focus area>
   | Exercise | Sets | Reps / Duration | Rest |
   |---|---|---|---|
   | Exercise name | X | Y | Z |
   ...

   Repeat for each day.

   ### 💡 Tips
   - 2-3 actionable tips relevant to the goal.

   ### ⚠️ Disclaimer
   Always include: "This plan is for informational purposes only. Consult a physician before starting any new exercise programme."
   If injury input was provided, also add injury-specific caution.

6. Do NOT include exercises beyond what the equipment allows.
7. Do NOT add rest days unless the user has fewer than 7 days — in that case, note remaining days as rest.
8. Stay focused — no diet advice unless directly related to the goal.
"""


# ── Core function ─────────────────────────────────────────────────────────────

def generate_workout_plan(
    api_key: str,
    fitness_goal: str,
    experience_level: str,
    days_per_week: int,
    equipment: str,
    injuries: Optional[str] = None,
) -> str:
    """
    Generate a personalised workout plan using the Groq API.

    Args:
        api_key: Groq API key.
        fitness_goal: User's primary fitness goal.
        experience_level: User's training experience level.
        days_per_week: Number of days available to train per week.
        equipment: Equipment the user has access to.
        injuries: Optional free-text description of injuries or limitations.

    Returns:
        A formatted workout plan as a markdown string.

    Raises:
        ValueError: If any required input is invalid.
        AuthenticationError: If the API key is invalid.
        APIConnectionError: If the network request fails.
        APIStatusError: If the API returns a non-2xx response.
    """

    # Build user prompt
    injury_section = (
        f"\n⚠️ Injuries / Limitations: {injuries.strip()}"
        if injuries and injuries.strip()
        else "\nNo injuries or limitations reported."
    )

    user_prompt = f"""
Please generate a weekly workout plan for the following person:

- Fitness Goal: {fitness_goal}
- Experience Level: {experience_level}
- Days Available Per Week: {days_per_week}
- Equipment Access: {equipment}
{injury_section}

Generate exactly {days_per_week} workout day(s). Format the output as instructed.
""".strip()

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=2048,
    )

    content = response.choices[0].message.content

    if not content or not content.strip():
        raise ValueError("The model returned an empty response. Please try again.")

    return content.strip()


# ── Streamlit UI ──────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Workout Plan Generator",
        page_icon="🏋️",
        layout="centered",
    )

    st.title("🏋️ Workout Plan Generator")
    st.caption("Powered by Groq · Built with Streamlit")
    st.divider()

    # ── Sidebar: API Key ──
    with st.sidebar:
        st.header("⚙️ Configuration")
        api_key = st.text_input(
            "Groq API Key",
            type="password",
            placeholder="gsk_...",
            help="Get your free key at console.groq.com",
        )
        st.markdown("---")
        st.markdown("**How to use:**")
        st.markdown("1. Enter your Groq API key\n2. Fill in your details\n3. Click **Generate Plan**")

    # ── Main inputs ──
    st.subheader("Tell us about yourself")

    col1, col2 = st.columns(2)

    with col1:
        fitness_goal = st.selectbox(
            "🎯 Fitness Goal",
            options=FITNESS_GOALS,
            index=0,
        )
        experience_level = st.selectbox(
            "📊 Experience Level",
            options=EXPERIENCE_LEVELS,
            index=0,
        )

    with col2:
        days_per_week = st.slider(
            "📅 Days Available Per Week",
            min_value=1,
            max_value=7,
            value=3,
            step=1,
        )
        equipment = st.selectbox(
            "🏠 Equipment Access",
            options=EQUIPMENT_OPTIONS,
            index=0,
        )

    injuries = st.text_area(
        "🩹 Injuries or Limitations (optional)",
        placeholder='e.g. "bad knees", "no overhead pressing", "lower back pain"',
        height=80,
    )

    st.divider()

    # ── Generate button ──
    col_btn1, col_btn2 = st.columns([1, 4])

    with col_btn1:
        generate = st.button("⚡ Generate Plan", type="primary", use_container_width=True)

    with col_btn2:
        regenerate = st.button(
            "🔄 Regenerate",
            use_container_width=True,
            disabled="workout_plan" not in st.session_state,
        )

    trigger = generate or regenerate

    # ── Validation & generation ──
    if trigger:
        # Validate API key
        if not api_key or not api_key.strip():
            st.error("🔑 Please enter your Groq API key in the sidebar.")
            st.stop()

        # Validate days
        if days_per_week < 1:
            st.error("📅 Please select at least 1 training day.")
            st.stop()

        with st.spinner("🤖 Generating your personalised plan..."):
            try:
                plan = generate_workout_plan(
                    api_key=api_key.strip(),
                    fitness_goal=fitness_goal,
                    experience_level=experience_level,
                    days_per_week=days_per_week,
                    equipment=equipment,
                    injuries=injuries if injuries else None,
                )
                # Persist in session state
                st.session_state["workout_plan"] = plan
                st.session_state["plan_meta"] = {
                    "goal": fitness_goal,
                    "level": experience_level,
                    "days": days_per_week,
                    "equipment": equipment,
                }

            except AuthenticationError:
                st.error("🔑 Invalid API key. Please check your Groq API key and try again.")
                st.stop()

            except APIConnectionError:
                st.error("🌐 Network error. Please check your internet connection and try again.")
                st.stop()

            except APIStatusError as e:
                if e.status_code == 429:
                    st.error("⏳ Rate limit hit. Please wait a moment and try again.")
                else:
                    st.error(f"❌ API error ({e.status_code}): {e.message}")
                st.stop()

            except ValueError as e:
                st.error(f"⚠️ {e}")
                st.stop()

            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
                st.stop()

    # ── Display plan ──
    if "workout_plan" in st.session_state:
        st.divider()
        st.subheader("📋 Your Personalised Workout Plan")

        meta = st.session_state.get("plan_meta", {})
        cols = st.columns(4)
        cols[0].metric("Goal", meta.get("goal", "—"))
        cols[1].metric("Level", meta.get("level", "—"))
        cols[2].metric("Days/week", meta.get("days", "—"))
        cols[3].metric("Equipment", meta.get("equipment", "—"))

        st.markdown(st.session_state["workout_plan"])

        st.divider()

        # ── Download buttons ──
        dl_col1, dl_col2 = st.columns(2)

        with dl_col1:
            st.download_button(
                label="📥 Download as .md",
                data=st.session_state["workout_plan"],
                file_name="workout_plan.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with dl_col2:
            st.download_button(
                label="📄 Download as .txt",
                data=st.session_state["workout_plan"],
                file_name="workout_plan.txt",
                mime="text/plain",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
