# 🏋️ Workout Plan Generator

A Streamlit web app that generates personalised weekly workout plans using the Groq LLM API. Pick your goal, experience level, available days, and equipment — get back a structured, table-formatted training plan you can download as Markdown or plain text.

Built with `streamlit` + `groq`, running `openai/gpt-oss-20b`.

---

## Features

- **Structured inputs** — goal, experience level, equipment, days per week (1–7), plus an optional free-text field for injuries or limitations
- **Constraint-aware prompting** — the model is instructed to respect equipment limits absolutely (no-equipment means bodyweight only), generate exactly the requested number of days, and scope difficulty to the stated experience level
- **Injury handling** — if limitations are supplied, the plan avoids stressing those areas and prepends a caution notice
- **Consistent output format** — every plan comes back as a Markdown table per training day, followed by tips and a safety disclaimer
- **Session persistence** — the generated plan survives Streamlit reruns via `st.session_state`
- **Regenerate** — request a fresh plan from the same inputs without re-entering anything
- **Downloads** — export the plan as `workout_plan.md` or `workout_plan.txt`
- **Graceful error handling** — distinct, human-readable messages for bad API keys, network failures, rate limits, and empty responses

---

## Requirements

- Python 3.9 or newer
- A Groq API key (free tier available at [console.groq.com](https://console.groq.com))

`requirements.txt`:

```
streamlit>=1.35.0
groq>=0.9.0
```

---

## Installation

```bash
git clone <your-repo-url>
cd workout-plan-generator

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

---

## Running the app

```bash
streamlit run workout_plan_generator.py
```

Streamlit opens the app at `http://localhost:8501`.

Paste your Groq API key into the sidebar field (it's a password input, so it never renders in plain text and is never written to disk).

### Optional: avoid pasting the key every time

Create `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "gsk_your_key_here"
```

Then default the sidebar input to it:

```python
api_key = st.text_input(
    "Groq API Key",
    type="password",
    value=st.secrets.get("GROQ_API_KEY", ""),
)
```

Add `.streamlit/secrets.toml` to your `.gitignore`.

---

## Usage

1. Enter your Groq API key in the sidebar
2. Select your **fitness goal** — build muscle, lose fat, general fitness, or improve endurance
3. Select your **experience level** — beginner, intermediate, or advanced
4. Select your **equipment** — no equipment, home dumbbells, or full gym
5. Set **days per week** with the slider (1–7)
6. Optionally describe any **injuries or limitations** in free text
7. Click **Generate** — the plan renders below, with metric cards summarising your inputs
8. Use **Regenerate** for a different plan from the same inputs, or download as `.md` / `.txt`

---

## Project structure

```
workout-plan-generator/
├── workout_plan_generator.py   # the whole app — constants, core function, UI
├── requirements.txt
└── README.md
```

The single module separates cleanly into three parts:

| Section | Contents |
|---|---|
| **Constants** | `FITNESS_GOALS`, `EXPERIENCE_LEVELS`, `EQUIPMENT_OPTIONS`, `SYSTEM_PROMPT` |
| **Core logic** | `generate_workout_plan(...)` — fully type-hinted, no Streamlit dependency |
| **UI** | `main()` — page config, sidebar, inputs, rendering, downloads |

`generate_workout_plan()` is deliberately free of any Streamlit calls, so it can be imported and reused from a CLI, a FastAPI route, or a test suite without changes.

---

## How it works

`SYSTEM_PROMPT` carries eight numbered rules covering equipment enforcement, exact day count, level-appropriate scoping, injury avoidance, a mandatory output structure, rest-day handling, and a hard boundary against drifting into diet advice.

The user prompt is built separately and interpolates the form values, so the instruction set stays stable while only the variables change:

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ],
    temperature=0.7,
    max_tokens=2048,
)
```

`temperature=0.7` gives enough variation that repeated generations differ meaningfully, while the format rules keep the structure consistent.

---

## Error handling

| Exception | Cause | What the user sees |
|---|---|---|
| `AuthenticationError` | Invalid or missing API key | Prompt to check the key |
| `APIConnectionError` | Network unreachable | Prompt to check connectivity and retry |
| `APIStatusError` (429) | Rate limit exceeded | Prompt to wait before retrying |
| `APIStatusError` (other) | Non-2xx from the API | Status code surfaced |
| `ValueError` | Model returned empty content | Prompt to regenerate |
| `Exception` | Anything unforeseen | Generic failure message |

Invalid input (missing key, zero days) is caught before the API call and short-circuited with `st.stop()`, so no request is wasted.

---

## Customisation

**Change the model** — swap the `model` argument. Groq's other hosted models work as drop-in replacements; smaller ones are faster and cheaper but follow the format rules less reliably.

**Add goals or equipment tiers** — append to `FITNESS_GOALS` or `EQUIPMENT_OPTIONS`. Options are driven from these lists, so the UI picks up new entries automatically.

**Change the output format** — edit rule 5 in `SYSTEM_PROMPT`. That block is the single source of truth for plan structure.

**Tighten adherence** — lower `temperature` toward `0.3` if plans drift from the specified format.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'groq'`** — the virtualenv isn't active, or dependencies weren't installed. Activate it and re-run `pip install -r requirements.txt`.

**Plan has the wrong number of days** — usually a smaller model. Switch back to `llama-3.3-70b-versatile` or lower the temperature.

**Plan gets truncated mid-table** — raise `max_tokens`. Seven-day plans for advanced users can exceed 2048.

**Rate limited on the free tier** — Groq's free tier caps requests per minute. Wait a moment and retry; the app surfaces this as a distinct message rather than a generic failure.

---

## Disclaimer

This app generates fitness content with a language model. It is **not** medical advice and is no substitute for a qualified trainer or physician. Every generated plan includes this notice. Anyone with an existing injury or medical condition should consult a doctor before starting a new exercise programme.

---

## License

MIT

