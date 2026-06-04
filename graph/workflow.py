from langgraph.graph import StateGraph, START, END

from agents.validator import validator_node
from agents.planner import planner_node
from agents.stats_agent import stats_node
from agents.trend_agent import trend_node
from agents.anomaly_agent import anomaly_node
from agents.correlation_agent import correlation_node
from agents.visualization_agent import visualization_node
from agents.narrator_agent import narrator_node
from agents.recommendation_agent import recommendation_node
from agents.compiler_agent import compiler_node
from models.state import ReportState


def analyses_node(state: ReportState) -> dict:
    """
    Runs all four analysis agents. Each writes to its own key in state
    so there are no conflicts. Progress logs are manually merged.
    """
    planned = state.get("planned_analyses", ["stats", "correlation"])
    result: dict = {}
    new_logs: list = []

    if "stats" in planned:
        r = stats_node(state)
        result.update(r)
        new_logs.append("✅ Stats Agent — Descriptive statistics computed")

    if "trend" in planned:
        r = trend_node(state)
        result.update(r)
        has = r.get("trend_result", {}).get("has_trend_data", False)
        new_logs.append(
            "✅ Trend Agent — Temporal patterns analysed"
            if has else "⚠️  Trend Agent — No datetime column, skipped"
        )

    if "anomaly" in planned:
        r = anomaly_node(state)
        result.update(r)
        count = r.get("anomaly_result", {}).get("anomaly_count", 0)
        new_logs.append(f"✅ Anomaly Agent — {count} anomalous records detected")

    if "correlation" in planned:
        r = correlation_node(state)
        result.update(r)
        pairs = len(r.get("correlation_result", {}).get("top_pairs", []))
        new_logs.append(f"✅ Correlation Agent — {pairs} variable relationships identified")

    result["progress_log"] = state.get("progress_log", []) + new_logs
    return result


def build_graph():
    builder = StateGraph(ReportState)

    builder.add_node("validator", validator_node)
    builder.add_node("planner", planner_node)
    builder.add_node("analyses", analyses_node)
    builder.add_node("visualization", visualization_node)
    builder.add_node("narrator", narrator_node)
    builder.add_node("recommendation", recommendation_node)
    builder.add_node("compiler", compiler_node)

    builder.add_edge(START, "validator")
    builder.add_edge("validator", "planner")
    builder.add_edge("planner", "analyses")
    builder.add_edge("analyses", "visualization")
    builder.add_edge("visualization", "narrator")
    builder.add_edge("narrator", "recommendation")
    builder.add_edge("recommendation", "compiler")
    builder.add_edge("compiler", END)

    return builder.compile()
