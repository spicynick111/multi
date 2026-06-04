from langchain_core.messages import HumanMessage
from models.state import ReportState
from utils.llm import get_llm


def planner_node(state: ReportState) -> dict:
    vs = state["validation_summary"]

    # Rule-based: decide which analyses make sense for this data
    analyses = ["stats", "correlation"]
    if vs.get("datetime_columns"):
        analyses.append("trend")
    if len(vs.get("numeric_columns", [])) >= 2:
        analyses.append("anomaly")

    # LLM: describe the dataset in business language for the report header
    data_context = _describe_dataset(vs)

    log = state.get("progress_log", [])
    return {
        "planned_analyses": analyses,
        "data_context": data_context,
        "progress_log": log + [
            f"✅ Analysis Planner — Scheduled: {', '.join(analyses)}"
        ],
    }


def _describe_dataset(vs: dict) -> str:
    try:
        llm = get_llm()
        prompt = (
            "You are a data analyst. Describe this dataset in exactly 2 business-friendly sentences.\n\n"
            f"Rows: {vs['rows']}\n"
            f"Numeric columns: {', '.join(vs.get('numeric_columns', [])[:6])}\n"
            f"Categorical columns: {', '.join(vs.get('categorical_columns', [])[:6])}\n"
            f"Date columns: {', '.join(vs.get('datetime_columns', [])[:3])}\n\n"
            "Write only 2 sentences. No bullet points."
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception:
        numeric = ", ".join(vs.get("numeric_columns", [])[:4]) or "various metrics"
        return (
            f"This dataset contains {vs['rows']:,} records across {vs['columns']} dimensions "
            f"including {numeric}. "
            "The following analysis covers statistical patterns, trends, anomalies, and key correlations."
        )
