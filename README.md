# 📊 Autonomous Business Report Generator

> Upload any CSV → 7 AI agents analyse it → Get a full **PDF Report + PowerPoint Deck + Email Draft** in under 2 minutes.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-1C3C3C?style=flat&logo=langchain&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.0_Flash-Free-4285F4?style=flat&logo=google&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat)

---

## What It Does

Drop any CSV file into the app and a pipeline of **7 specialized AI agents** kicks in:

| Step | Agent | What It Does |
|------|-------|-------------|
| 1 | **Data Validator** | Cleans data, handles missing values, detects column types |
| 2 | **Analysis Planner** | Uses LLM to understand the dataset and plan analyses |
| 3 | **Analysis Suite** | Runs Stats · Trend · Anomaly · Correlation in parallel |
| 4 | **Visualization Agent** | Creates 5 Plotly charts (distributions, heatmap, trends, anomalies) |
| 5 | **Insight Narrator** | Writes a 3-paragraph executive summary using Gemini |
| 6 | **Recommendation Agent** | Generates 3 data-backed strategic action items |
| 7 | **Report Compiler** | Assembles everything into PDF + PowerPoint + Email |

### Output You Get
- **PDF Report** — Cover page, stats tables, correlation table, anomaly analysis, all charts, recommendations
- **PowerPoint Deck** — Title slide, 8 metric cards, stats table, correlation bars, chart slides, recommendation cards, thank-you slide
- **Email Draft** — Ready-to-send stakeholder update with key findings
- **Send to Email** — Type any email address → PDF + PPTX land in inbox instantly

---

## Demo

| Light Mode | Dark Mode |
|-----------|----------|
| Upload CSV → Watch 7 agents run live | Toggle 🌙 in sidebar |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM | Gemini 2.0 Flash via `google-genai` |
| Data Analysis | Pandas · SciPy · scikit-learn |
| Visualisation | Plotly + Kaleido |
| PDF Generation | fpdf2 |
| PowerPoint | python-pptx |
| Email | Resend API / Gmail SMTP |
| UI | Streamlit |

**Cost: $0** — Gemini 2.0 Flash free tier (1,500 req/day). No OpenAI. No paid APIs.

---

## Project Structure

```
business-report-agent/
├── app.py                      ← Streamlit UI (dark mode, live pipeline)
├── requirements.txt
│
├── agents/
│   ├── validator.py            ← CSV cleaning + type detection
│   ├── planner.py              ← LLM-based analysis planning
│   ├── stats_agent.py          ← Descriptive statistics
│   ├── trend_agent.py          ← Time series + trend direction
│   ├── anomaly_agent.py        ← Isolation Forest + Z-score
│   ├── correlation_agent.py    ← Correlation matrix + top pairs
│   ├── visualization_agent.py  ← 5 Plotly charts → PNG
│   ├── narrator_agent.py       ← Executive summary (Gemini)
│   ├── recommendation_agent.py ← Strategic actions (Gemini)
│   └── compiler_agent.py       ← PDF + PowerPoint + Email
│
├── graph/
│   └── workflow.py             ← LangGraph StateGraph pipeline
│
├── models/
│   └── state.py                ← Shared ReportState TypedDict
│
├── utils/
│   ├── llm.py                  ← Gemini wrapper
│   └── email_sender.py         ← Resend / Gmail SMTP
│
└── outputs/
    ├── charts/                 ← Generated PNG charts
    ├── reports/                ← Generated PDF files
    └── presentations/          ← Generated PPTX files
```

---

## Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/spicynick111/multi.git
cd multi
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Get a free Gemini API key
- Go to [aistudio.google.com](https://aistudio.google.com)
- Click **Get API Key** → Create key → Copy it

### 4. Configure secrets
Create `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your-gemini-api-key-here"

# Optional: for email sending
RESEND_API_KEY = "re_xxxxxxxxxxxx"   # free at resend.com
```

### 5. Run the app
```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) → Upload any CSV → Done.

---

## Email Sending (Optional)

To enable the **Send Report** feature (sends PDF + PPTX to any inbox):

**Option A — Resend** *(recommended, proper no-reply sender)*
1. Sign up free at [resend.com](https://resend.com)
2. Create an API Key
3. Add to `secrets.toml`: `RESEND_API_KEY = "re_..."`

**Option B — Gmail SMTP**
1. Create a dedicated Gmail (e.g. `reportai.noreply@gmail.com`)
2. Get a 16-char App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Add to `secrets.toml`:
```toml
SENDER_EMAIL        = "reportai.noreply@gmail.com"
SENDER_APP_PASSWORD = "abcd efgh ijkl mnop"
```

---

## Deploying to Streamlit Community Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select this repo → `app.py`
4. **Advanced settings → Secrets** → paste your `secrets.toml` content
5. Deploy — your app gets a public URL in ~2 minutes

---

## LangGraph Pipeline

```
START
  │
  ▼
validator ──► planner ──► analyses (stats + trend + anomaly + correlation)
                                │
                                ▼
                         visualization ──► narrator ──► recommendation ──► compiler
                                                                               │
                                                                              END
                                                                    (PDF + PPT + Email)
```

Results are cached in `st.session_state` — the graph runs **once per file upload**, never on tab clicks or theme toggles.

---

## Contributing

Pull requests are welcome. For major changes, open an issue first.

---

## License

MIT License — free to use, modify, and distribute.

---

<p align="center">Built with LangGraph · Gemini · Streamlit</p>
