# AI Health & Fitness Plan Generator

A [Streamlit](https://streamlit.io/) app that uses [Agno](https://github.com/agno-agi/agno) agents with [Groq](https://groq.com/) to generate personalized meal plans, workout plans, and combined health strategies. Web search uses DuckDuckGo via Agno’s tools.

## Prerequisites

- Python 3.10+ (3.11+ recommended)
- A [Groq API key](https://console.groq.com/keys)

## Setup

```bash
git clone <your-repo-url>
cd ai_fitness_agent
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

**Option A — Streamlit secrets (recommended for local runs)**

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` and set `GROQ_API_KEY` to your key. This file is listed in `.gitignore` and must not be committed.

**Option B — Environment variable**

```bash
export GROQ_API_KEY="your-key"
```

Optional: set `GROQ_MODEL_ID` to another [Groq model](https://console.groq.com/docs/models) (default in code: `llama-3.3-70b-versatile`).

## Run

```bash
streamlit run fitness.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`).

## Project layout

| Path | Purpose |
|------|---------|
| `fitness.py` | Streamlit UI and Agno agents |
| `.streamlit/secrets.toml` | Local Groq key (create yourself; not in repo) |
| `requirements.txt` | Python dependencies |

## Security

- Never commit `.streamlit/secrets.toml` or any file containing API keys.
- If a key was exposed, revoke it in the Groq console and create a new one.

## License

See [LICENSE](LICENSE).
