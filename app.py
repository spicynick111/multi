import os
import tempfile
from datetime import datetime

import streamlit as st

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ReportAI — Business Report Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── dark mode state ───────────────────────────────────────────────────────────
if "dark" not in st.session_state:
    st.session_state.dark = False

dark = st.session_state.dark

# ── theme variables ───────────────────────────────────────────────────────────
if dark:
    BG       = "#0f172a"
    BG2      = "#1e293b"
    CARD_BG  = "#1e293b"
    BORDER   = "#334155"
    TEXT     = "#f1f5f9"
    SUBTEXT  = "#94a3b8"
    ACCENT   = "#3b82f6"
    PEND_BG  = "#1e293b"; PEND_TXT = "#64748b"; PEND_BOR = "#334155"
    RUN_BG   = "#2d1f06";  RUN_TXT  = "#fbbf24"; RUN_BOR  = "#f59e0b"
    DONE_BG  = "#052e16";  DONE_TXT = "#34d399"; DONE_BOR = "#10b981"
    MET_BG   = "#1e293b";  MET_BOR  = "#3b82f6"
else:
    BG       = "#f8fafc"
    BG2      = "#ffffff"
    CARD_BG  = "#ffffff"
    BORDER   = "#e2e8f0"
    TEXT     = "#0f172a"
    SUBTEXT  = "#64748b"
    ACCENT   = "#2563eb"
    PEND_BG  = "#f1f5f9"; PEND_TXT = "#94a3b8"; PEND_BOR = "#cbd5e1"
    RUN_BG   = "#fef3c7"; RUN_TXT  = "#b45309";  RUN_BOR  = "#f59e0b"
    DONE_BG  = "#d1fae5"; DONE_TXT = "#065f46";  DONE_BOR = "#10b981"
    MET_BG   = "#eff6ff"; MET_BOR  = "#bfdbfe"

st.markdown(f"""
<style>
/* ── global ── */
[data-testid="stAppViewContainer"] {{
    background: {BG};
    color: {TEXT};
}}
[data-testid="stSidebar"] {{
    background: {BG2} !important;
    border-right: 1px solid {BORDER};
}}
[data-testid="stHeader"] {{ background: transparent !important; }}
h1, h2, h3, h4 {{ color: {TEXT} !important; }}
p, li, span, div {{ color: {TEXT}; }}
.stMarkdown p {{ color: {TEXT}; }}

/* ── upload box ── */
[data-testid="stFileUploader"] {{
    background: {CARD_BG};
    border: 2px dashed {ACCENT};
    border-radius: 12px;
    padding: 10px;
}}

/* ── agent cards ── */
.agent-card {{
    padding: 10px 14px;
    border-radius: 10px;
    margin: 5px 0;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.3s ease;
}}
.pending {{ background:{PEND_BG}; color:{PEND_TXT}; border-left:4px solid {PEND_BOR}; }}
.running {{ background:{RUN_BG};  color:{RUN_TXT};  border-left:4px solid {RUN_BOR};
            box-shadow: 0 0 10px {RUN_BOR}44; animation: pulse 1.2s infinite; }}
.done    {{ background:{DONE_BG}; color:{DONE_TXT}; border-left:4px solid {DONE_BOR}; }}

@keyframes pulse {{
  0%,100% {{ opacity:1; }} 50% {{ opacity:0.7; }}
}}

/* ── metric boxes ── */
.metric-box {{
    background: {MET_BG};
    border: 1px solid {MET_BOR};
    border-radius: 12px;
    padding: 20px 10px;
    text-align: center;
    transition: transform 0.2s;
}}
.metric-box:hover {{ transform: translateY(-3px); box-shadow: 0 4px 20px {ACCENT}33; }}
.metric-box h2 {{ color: {ACCENT} !important; font-size: 2.2rem; margin:0; }}
.metric-box p  {{ color: {SUBTEXT}; margin:4px 0 0 0; font-size:13px; }}

/* ── download buttons ── */
[data-testid="stDownloadButton"] > button {{
    width: 100%;
    border-radius: 10px;
    border: 1px solid {ACCENT};
    background: {CARD_BG};
    color: {ACCENT};
    font-weight: 600;
    transition: all 0.2s;
}}
[data-testid="stDownloadButton"] > button:hover {{
    background: {ACCENT};
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 4px 15px {ACCENT}55;
}}

/* ── expander ── */
[data-testid="stExpander"] {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}

/* ── progress bar ── */
[data-testid="stProgressBar"] > div > div {{
    background: linear-gradient(90deg, {ACCENT}, #8b5cf6);
    border-radius: 4px;
}}

/* ── divider ── */
hr {{ border-color: {BORDER}; }}

/* ── sidebar text ── */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {{ color: {TEXT} !important; }}
</style>
""", unsafe_allow_html=True)

# ── agent definitions (display order) ────────────────────────────────────────
PIPELINE = [
    ("validator",       "Data Validator",         "Validates CSV · detects column types"),
    ("planner",         "Analysis Planner",        "Plans which analyses to run"),
    ("analyses",        "Analysis Suite",          "Stats · Trend · Anomaly · Correlation"),
    ("visualization",   "Visualization Agent",     "Creates 5 Plotly charts"),
    ("narrator",        "Insight Narrator",        "Writes executive summary (LLM)"),
    ("recommendation",  "Recommendation Agent",    "Generates 3 strategic actions (LLM)"),
    ("compiler",        "Report Compiler",         "Builds PDF · PowerPoint · Email"),
]

PRIORITY_COLOR = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # ── Dark mode toggle (native Streamlit toggle — looks clean) ──────────────
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;padding:8px 0 4px 0">
      <span style="font-size:18px">{"🌙" if not dark else "☀️"}</span>
      <span style="font-weight:600;font-size:15px;color:{TEXT}">
        {"Dark" if dark else "Light"} Mode
      </span>
    </div>
    """, unsafe_allow_html=True)
    new_dark = st.toggle("Enable Dark Mode", value=dark, label_visibility="collapsed")
    if new_dark != dark:
        st.session_state.dark = new_dark
        st.rerun()

    st.divider()
    st.markdown("## ⚙️ Configuration")

    # Load Gemini key silently from secrets or env — users never see this
    _FAKE = {"your-gemini-api-key-here", "", "your-key-here"}
    _secret_key = (st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else "")
    _env_key    = os.getenv("GEMINI_API_KEY", "")
    _preset_key = ("" if _secret_key in _FAKE else _secret_key) or \
                  ("" if _env_key    in _FAKE else _env_key)
    if _preset_key:
        os.environ["GEMINI_API_KEY"] = _preset_key

    st.divider()

    st.markdown("## 🔁 Agent Pipeline")
    for _, name, desc in PIPELINE:
        st.markdown(f"**{name}**  \n{desc}")
    st.divider()

    st.markdown("## 📌 Tips")
    st.info(
        "Works with **any CSV**: sales data, user analytics, "
        "financial records, survey results, etc."
    )

# ── header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="padding:24px 0 8px 0">
  <h1 style="margin:0;font-size:2.2rem;color:{ACCENT}">📊 ReportAI</h1>
  <p style="margin:6px 0 0 0;font-size:1.05rem;color:{SUBTEXT}">
    Multi-agent LangGraph pipeline &nbsp;·&nbsp; Gemini 2.0 Flash &nbsp;·&nbsp; Free to use<br>
    Upload any CSV &rarr; 7 agents analyse it &rarr; <b>PDF + PowerPoint + Email</b> in ~2 minutes
  </p>
</div>
""", unsafe_allow_html=True)
st.divider()

# ── file upload ───────────────────────────────────────────────────────────────
uploaded = st.file_uploader("Upload your CSV file", type=["csv"])

if not uploaded:
    st.markdown("#### 👆 Upload a CSV to get started")
    st.stop()

# ── layout: pipeline | progress ───────────────────────────────────────────────
col_pipe, col_prog = st.columns([1, 2], gap="large")

with col_pipe:
    st.markdown("### Agent Pipeline")
    cards: dict = {}
    for key, name, desc in PIPELINE:
        cards[key] = st.empty()
        cards[key].markdown(
            f'<div class="agent-card pending">⬜ {name}<br>'
            f'<span style="font-weight:400;font-size:12px">{desc}</span></div>',
            unsafe_allow_html=True,
        )

with col_prog:
    st.markdown("### Live Progress")
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    log_box = st.container()

# ── run graph OR load from cache ─────────────────────────────────────────────
# Key the cache on filename + size so re-uploading a different file re-runs
_file_key = f"{uploaded.name}_{len(uploaded.getvalue())}"

if st.session_state.get("_file_key") != _file_key:
    # First time for this file — run the graph
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded.getvalue())
        tmp_path = tmp.name

    try:
        from graph.workflow import build_graph
        graph = build_graph()

        initial: dict = {
            "csv_path": tmp_path,
            "filename": uploaded.name,
            "df_json": "",
            "validation_summary": {},
            "column_types": {},
            "planned_analyses": [],
            "data_context": "",
            "stats_result": {},
            "trend_result": {},
            "anomaly_result": {},
            "correlation_result": {},
            "chart_paths": [],
            "insights": "",
            "recommendations": [],
            "pdf_path": "",
            "pptx_path": "",
            "email_draft": "",
            "progress_log": [],
        }

        accumulated = initial.copy()
        total = len(PIPELINE)
        step  = 0

        def _mark(key: str, state: str, name: str, desc: str):
            icons = {"running": "⚙️", "done": "✅"}
            cards[key].markdown(
                f'<div class="agent-card {state}">{icons.get(state,"⬜")} {name}<br>'
                f'<span style="font-weight:400;font-size:12px">{desc}</span></div>',
                unsafe_allow_html=True,
            )

        _mark("validator", "running", "Data Validator", "Validating your data…")

        for event in graph.stream(initial, stream_mode="updates"):
            for node_name, update in event.items():
                for k, v in update.items():
                    accumulated[k] = v

                for key, name, desc in PIPELINE:
                    if key == node_name:
                        _mark(key, "done", name, desc)
                        idx = [p[0] for p in PIPELINE].index(key)
                        if idx + 1 < len(PIPELINE):
                            nk, nn, nd = PIPELINE[idx + 1]
                            _mark(nk, "running", nn, f"{nd}…")
                        break

                step += 1
                progress_bar.progress(min(step / total, 1.0))
                new_logs = update.get("progress_log", [])
                for entry in new_logs:
                    log_box.markdown(f"- {entry}")
                status_text.markdown(f"**Step {step} / {total}** — `{node_name}` complete")

        status_text.markdown("**✅ All steps complete!**")
        progress_bar.progress(1.0)

        # ── save to session state so page rerenders don't re-run the graph ──
        st.session_state["_file_key"]    = _file_key
        st.session_state["_accumulated"] = accumulated

    except Exception as exc:
        st.error(f"Something went wrong: {exc}")
        st.exception(exc)
        st.stop()
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

else:
    # Same file — reuse cached results, hide the pipeline/progress UI
    accumulated = st.session_state["_accumulated"]
    for key, name, desc in PIPELINE:
        cards[key].markdown(
            f'<div class="agent-card done">✅ {name}<br>'
            f'<span style="font-weight:400;font-size:12px">{desc}</span></div>',
            unsafe_allow_html=True,
        )
    progress_bar.progress(1.0)
    status_text.markdown("**✅ All steps complete!**")
    for entry in accumulated.get("progress_log", []):
        log_box.markdown(f"- {entry}")

# ── results ───────────────────────────────────────────────────────────────────
try:
    st.divider()
    st.markdown("## 📥 Your Reports Are Ready")

    dl1, dl2, dl3 = st.columns(3)
    with dl1:
        pdf_path = accumulated.get("pdf_path", "")
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button("📄 Download PDF Report", f.read(),
                    file_name=f"report_{uploaded.name.replace('.csv','')}.pdf",
                    mime="application/pdf", use_container_width=True)
    with dl2:
        pptx_path = accumulated.get("pptx_path", "")
        if pptx_path and os.path.exists(pptx_path):
            with open(pptx_path, "rb") as f:
                st.download_button("📊 Download PowerPoint", f.read(),
                    file_name=f"report_{uploaded.name.replace('.csv','')}.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True)
    with dl3:
        email_draft = accumulated.get("email_draft", "")
        if email_draft:
            st.download_button("✉️ Download Email Draft", email_draft,
                file_name="email_draft.txt", mime="text/plain",
                use_container_width=True)

    # ── key metrics ───────────────────────────────────────────────────────────
    st.divider()
    vs          = accumulated.get("validation_summary", {})
    anomaly     = accumulated.get("anomaly_result", {})
    correlation = accumulated.get("correlation_result", {})

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-box"><h2>{vs.get("rows",0):,}</h2><p>Records Analysed</p></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-box"><h2>{vs.get("columns",0)}</h2><p>Features Detected</p></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-box"><h2>{anomaly.get("anomaly_count",0)}</h2><p>Anomalies Flagged</p></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-box"><h2>{len(correlation.get("top_pairs",[]))}</h2><p>Correlations Found</p></div>', unsafe_allow_html=True)

    # ── charts ────────────────────────────────────────────────────────────────
    chart_paths = accumulated.get("chart_paths", [])
    if chart_paths:
        st.divider()
        st.markdown("### 📈 Visualizations")
        for i in range(0, len(chart_paths), 2):
            c1, c2 = st.columns(2)
            if os.path.exists(chart_paths[i]):
                c1.image(chart_paths[i], use_container_width=True)
            if i + 1 < len(chart_paths) and os.path.exists(chart_paths[i + 1]):
                c2.image(chart_paths[i + 1], use_container_width=True)

    # ── recommendations ───────────────────────────────────────────────────────
    recs = accumulated.get("recommendations", [])
    if recs:
        st.divider()
        st.markdown("### 🎯 Strategic Recommendations")
        for i, rec in enumerate(recs, 1):
            icon = PRIORITY_COLOR.get(rec.get("priority", "Medium"), "•")
            with st.expander(f"{icon} {i}. {rec.get('action','')}", expanded=True):
                st.markdown(f"**Impact:** {rec.get('impact','')}")
                st.markdown(f"**Priority:** `{rec.get('priority','Medium')}`")

    # ── email preview + send ──────────────────────────────────────────────────
    if email_draft:
        st.divider()
        st.markdown("### ✉️ Email Report")
        tab_preview, tab_send = st.tabs(["📄 Preview Draft", "🚀 Send Now"])

        with tab_preview:
            # Show the full email draft text
            st.markdown(
                f'<div style="background:{"#1e293b" if dark else "#f8fafc"};'
                f'border:1px solid {BORDER};border-radius:10px;padding:20px;'
                f'font-family:monospace;font-size:13px;color:{TEXT};'
                f'white-space:pre-wrap;line-height:1.7">'
                + email_draft.replace("<", "&lt;").replace(">", "&gt;")
                + "</div>",
                unsafe_allow_html=True,
            )

        with tab_send:
            st.markdown(
                f'<p style="color:{SUBTEXT};font-size:14px;margin-bottom:12px">'
                "Enter <b>any email address</b> — the full report (PDF + PowerPoint) "
                "will be sent there instantly.</p>",
                unsafe_allow_html=True,
            )

            recipient = st.text_input(
                "Recipient Email",
                placeholder="someone@gmail.com",
                label_visibility="visible",
            )

            if st.button("📤 Send Report", type="primary", use_container_width=True):
                if not recipient or "@" not in recipient:
                    st.warning("Please enter a valid email address.")
                else:
                    with st.spinner(f"Sending report to {recipient}…"):
                        try:
                            from utils.email_sender import send_report as _send
                            backend = _send(
                                recipient_email=recipient,
                                subject=f"Business Intelligence Report — {datetime.now().strftime('%B %Y')}",
                                body=email_draft,
                                pdf_path=accumulated.get("pdf_path", ""),
                                pptx_path=accumulated.get("pptx_path", ""),
                            )
                            via = "Resend" if backend == "resend" else "Gmail"
                            st.success(f"✅ Report sent to **{recipient}** via {via} — PDF + PowerPoint attached!")
                        except ValueError:
                            st.error("Email sending not configured. Add credentials to secrets.")
                        except Exception as mail_err:
                            st.error(f"Send failed: {mail_err}")

except Exception as exc:
    st.error(f"Something went wrong: {exc}")
    st.exception(exc)
