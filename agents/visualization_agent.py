import io
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from models.state import ReportState

CHARTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "charts")


def visualization_node(state: ReportState) -> dict:
    os.makedirs(CHARTS_DIR, exist_ok=True)

    df = pd.read_json(io.StringIO(state["df_json"]), orient="split")
    vs = state["validation_summary"]
    numeric_cols = vs.get("numeric_columns", [])
    cat_cols = vs.get("categorical_columns", [])

    chart_paths: list = []

    # 1. Distributions
    _save(
        _distributions(df, numeric_cols),
        os.path.join(CHARTS_DIR, "distributions.png"),
        chart_paths,
    )

    # 2. Correlation heatmap
    _save(
        _heatmap(state.get("correlation_result", {}), numeric_cols),
        os.path.join(CHARTS_DIR, "correlation_heatmap.png"),
        chart_paths,
    )

    # 3. Trend line
    _save(
        _trend_chart(state.get("trend_result", {})),
        os.path.join(CHARTS_DIR, "trend.png"),
        chart_paths,
    )

    # 4. Categorical bar
    _save(
        _category_bar(df, cat_cols, numeric_cols),
        os.path.join(CHARTS_DIR, "category_breakdown.png"),
        chart_paths,
    )

    # 5. Anomaly scatter
    _save(
        _anomaly_scatter(df, numeric_cols, state.get("anomaly_result", {})),
        os.path.join(CHARTS_DIR, "anomalies.png"),
        chart_paths,
    )

    log = state.get("progress_log", [])
    return {
        "chart_paths": chart_paths,
        "progress_log": log + [f"✅ Visualization Agent — {len(chart_paths)} charts created"],
    }


# ── helpers ──────────────────────────────────────────────────────────────────

def _save(fig, path: str, paths: list):
    if fig is None:
        return
    try:
        fig.write_image(path, width=1100, height=500, scale=1)
        paths.append(path)
    except Exception:
        pass


def _distributions(df, numeric_cols):
    cols = numeric_cols[:3]
    if not cols:
        return None
    fig = make_subplots(rows=1, cols=len(cols), subplot_titles=cols)
    for i, col in enumerate(cols, 1):
        fig.add_trace(go.Histogram(x=df[col], name=col, showlegend=False,
                                   marker_color="#3b82f6"), row=1, col=i)
    fig.update_layout(title_text="Distribution of Key Metrics",
                      template="plotly_white", height=420)
    return fig


def _heatmap(corr_result, numeric_cols):
    if not corr_result.get("matrix") or len(numeric_cols) < 2:
        return None
    corr_df = pd.DataFrame(corr_result["matrix"])
    fig = px.imshow(
        corr_df,
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        text_auto=".2f",
        title="Correlation Matrix",
    )
    fig.update_layout(template="plotly_white", height=520)
    return fig


def _trend_chart(trend_result):
    if not trend_result.get("has_trend_data") or not trend_result.get("monthly_trends"):
        return None
    col = list(trend_result["monthly_trends"].keys())[0]
    data = trend_result["monthly_trends"][col]
    tdf = pd.DataFrame(list(data.items()), columns=["Date", col])
    tdf["Date"] = pd.to_datetime(tdf["Date"])
    fig = px.line(tdf, x="Date", y=col, title=f"{col} Over Time",
                  markers=True, line_shape="spline",
                  color_discrete_sequence=["#3b82f6"])
    fig.update_layout(template="plotly_white", height=420)
    return fig


def _category_bar(df, cat_cols, numeric_cols):
    if not cat_cols or not numeric_cols:
        return None
    cat, num = cat_cols[0], numeric_cols[0]
    grouped = (
        df.groupby(cat)[num].mean()
        .sort_values(ascending=False)
        .head(12)
        .reset_index()
    )
    fig = px.bar(grouped, x=cat, y=num, title=f"Average {num} by {cat}",
                 color=num, color_continuous_scale="Blues")
    fig.update_layout(template="plotly_white", height=420)
    return fig


def _anomaly_scatter(df, numeric_cols, anomaly_result):
    if len(numeric_cols) < 2 or not anomaly_result.get("anomaly_indices"):
        return None
    c1, c2 = numeric_cols[0], numeric_cols[1]
    df = df.copy()
    df["Anomaly"] = df.index.isin(anomaly_result["anomaly_indices"])
    fig = px.scatter(
        df, x=c1, y=c2, color="Anomaly",
        color_discrete_map={True: "#ef4444", False: "#3b82f6"},
        title=f"Anomaly Detection — {c1} vs {c2}",
        opacity=0.7,
    )
    fig.update_layout(template="plotly_white", height=420)
    return fig
