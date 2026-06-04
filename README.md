# Autonomous Business Report Generator

Multi-agent LangGraph pipeline that turns any CSV into a full analyst report — PDF + PowerPoint + stakeholder email — in under 2 minutes. 100% free, no paid API.

## Agent Pipeline

```
CSV Upload
    │
    ▼
[1] Data Validator      → cleans data, detects column types
    │
    ▼
[2] Analysis Planner    → decides which analyses to run (LLM)
    │
    ▼
[3] Analysis Suite      → Stats · Trend · Anomaly · Correlation (parallel logic)
    │
    ▼
[4] Visualization Agent → 5 Plotly charts saved as PNG
    │
    ▼
[5] Insight Narrator    → executive summary in business language (LLM)
    │
    ▼
[6] Recommendation Agent→ 3 strategic action items (LLM)
    │
    ▼
[7] Report Compiler     → PDF + PowerPoint + Email draft
```

## Setup

### 1. Install Ollama (local LLM — free)
```bash
# Download from https://ollama.com
ollama pull llama3.1
ollama serve
```

### 2. Install Python dependencies
```bash
cd business-report-agent
pip install -r requirements.txt
```

### 3. Run the app
```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## Usage

1. Upload any CSV file (sales, analytics, finance, survey data)
2. Select your Ollama model in the sidebar
3. Watch the 7 agents run live
4. Download your PDF report, PowerPoint deck, and email draft

## Tech Stack

| Component | Tool |
|-----------|------|
| Orchestration | LangGraph |
| LLM | Ollama (Llama 3.1 / Mistral / Phi-3) |
| Data Analysis | Pandas · SciPy · scikit-learn |
| Charts | Plotly + Kaleido |
| PDF | fpdf2 |
| PowerPoint | python-pptx |
| UI | Streamlit |

## Cost

**$0** — All models run locally via Ollama. No OpenAI, no Anthropic, no cloud LLM.

## Output Files

Generated files are saved to:
- `outputs/reports/` — PDF report
- `outputs/presentations/` — PowerPoint deck
- `outputs/charts/` — Individual chart PNGs
