from langchain_core.messages import HumanMessage
from models.state import ReportState
from utils.llm import get_llm


def narrator_node(state: ReportState) -> dict:
    insights = _generate_insights(state)
    log = state.get("progress_log", [])
    return {
        "insights": insights,
        "progress_log": log + ["✅ Insight Narrator — Executive summary written"],
    }


def _generate_insights(state: ReportState) -> str:
    vs = state["validation_summary"]
    anomaly = state.get("anomaly_result", {})
    trend = state.get("trend_result", {})
    correlation = state.get("correlation_result", {})
    stats = state.get("stats_result", {})

    # Build a compact fact sheet for the LLM
    facts = [
        f"Dataset: {vs['rows']:,} rows, {vs['columns']} columns",
        f"Numeric features: {', '.join(vs.get('numeric_columns', [])[:5])}",
    ]

    if trend.get("trend_direction"):
        for col, direction in list(trend["trend_direction"].items())[:2]:
            facts.append(f"{col} is {direction} over time")

    if anomaly.get("anomaly_count", 0) > 0:
        facts.append(
            f"{anomaly['anomaly_count']} anomalous records found "
            f"({anomaly['anomaly_percentage']}% of data)"
        )

    if correlation.get("top_pairs"):
        top = correlation["top_pairs"][0]
        facts.append(
            f"Strongest correlation: {top['col1']} ↔ {top['col2']} "
            f"({top['correlation']}, {top['strength']} {top['direction']})"
        )

    if stats.get("extremes"):
        for col, ex in list(stats["extremes"].items())[:2]:
            facts.append(f"{col} ranges from {ex['min']} to {ex['max']}")

    fact_block = "\n".join(f"- {f}" for f in facts)

    try:
        llm = get_llm()
        prompt = (
            "You are a senior business analyst writing an executive summary.\n\n"
            f"Key findings:\n{fact_block}\n\n"
            "Write exactly 3 paragraphs (no bullet points, no headers):\n"
            "1. What the data shows at a high level\n"
            "2. Key patterns and relationships\n"
            "3. Data quality observations and anomalies\n\n"
            "Use clear, professional business language."
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception:
        return (
            f"The dataset contains {vs['rows']:,} records across {vs['columns']} dimensions, "
            f"covering {', '.join(vs.get('numeric_columns', [])[:3])}.\n\n"
            + (
                f"Temporal analysis reveals {', '.join(vs.get('numeric_columns', [])[:2])} "
                "show clear directional trends, suggesting evolving business dynamics. "
                if trend.get("has_trend_data") else ""
            )
            + (
                f"\n\nIsolation Forest identified {anomaly['anomaly_count']} anomalous records "
                f"({anomaly['anomaly_percentage']}%). These records warrant further investigation "
                "to determine whether they represent data entry errors or genuine business outliers."
                if anomaly.get("anomaly_count", 0) > 0 else
                "\n\nData quality appears consistent with no significant anomalies detected."
            )
        )
