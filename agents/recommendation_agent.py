import json
from langchain_core.messages import HumanMessage
from models.state import ReportState
from utils.llm import get_llm


def recommendation_node(state: ReportState) -> dict:
    recommendations = _generate_recommendations(state)
    log = state.get("progress_log", [])
    return {
        "recommendations": recommendations,
        "progress_log": log + ["✅ Recommendation Agent — 3 strategic actions generated"],
    }


def _generate_recommendations(state: ReportState) -> list:
    vs = state["validation_summary"]
    anomaly = state.get("anomaly_result", {})
    correlation = state.get("correlation_result", {})
    insights = state.get("insights", "")

    try:
        llm = get_llm()
        prompt = (
            "You are a business strategy consultant. Based on the data analysis below, "
            "provide exactly 3 actionable recommendations.\n\n"
            f"Dataset: {vs['rows']:,} rows, {vs['columns']} columns\n"
            f"Anomalies: {anomaly.get('anomaly_count', 0)} records "
            f"({anomaly.get('anomaly_percentage', 0)}%)\n"
            f"Top correlations: {json.dumps(correlation.get('top_pairs', [])[:2])}\n"
            f"Summary excerpt: {insights[:400]}\n\n"
            "Respond ONLY with a valid JSON array, no extra text:\n"
            '[\n'
            '  {"action": "...", "impact": "...", "priority": "High"},\n'
            '  {"action": "...", "impact": "...", "priority": "Medium"},\n'
            '  {"action": "...", "impact": "...", "priority": "Low"}\n'
            ']'
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        start = content.find("[")
        end = content.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
        raise ValueError("No JSON array found")
    except Exception:
        return _fallback_recommendations(anomaly, correlation)


def _fallback_recommendations(anomaly: dict, correlation: dict) -> list:
    recs = []

    if anomaly.get("anomaly_count", 0) > 0:
        recs.append({
            "action": f"Investigate {anomaly['anomaly_count']} flagged anomalous records to identify data quality issues or fraud patterns.",
            "impact": "Improve data integrity and surface hidden risks that may be skewing business metrics.",
            "priority": "High",
        })
    else:
        recs.append({
            "action": "Implement automated data validation checks on all incoming data pipelines.",
            "impact": "Prevent future data quality degradation and reduce manual review time by up to 60%.",
            "priority": "High",
        })

    if correlation.get("top_pairs"):
        top = correlation["top_pairs"][0]
        recs.append({
            "action": f"Leverage the {top['strength']} {top['direction']} correlation between "
                      f"{top['col1']} and {top['col2']} to build a predictive model.",
            "impact": "Enable proactive decision-making with data-driven forecasts.",
            "priority": "Medium",
        })
    else:
        recs.append({
            "action": "Enrich the dataset with additional behavioral or contextual features.",
            "impact": "Unlock deeper segmentation insights and improve model accuracy.",
            "priority": "Medium",
        })

    recs.append({
        "action": "Set up a monthly automated reporting pipeline using this analysis framework.",
        "impact": "Reduce report generation time from days to minutes and ensure consistent insights.",
        "priority": "Low",
    })

    return recs
