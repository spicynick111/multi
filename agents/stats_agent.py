import io
import pandas as pd
from models.state import ReportState


def stats_node(state: ReportState) -> dict:
    df = pd.read_json(io.StringIO(state["df_json"]), orient="split")
    vs = state["validation_summary"]
    numeric_cols = vs.get("numeric_columns", [])
    cat_cols = vs.get("categorical_columns", [])

    result: dict = {}

    if numeric_cols:
        desc = df[numeric_cols].describe().round(3)
        result["descriptive"] = desc.to_dict()
        result["skewness"] = df[numeric_cols].skew().round(3).to_dict()

        result["extremes"] = {
            col: {
                "max": round(float(df[col].max()), 3),
                "min": round(float(df[col].min()), 3),
                "range": round(float(df[col].max() - df[col].min()), 3),
            }
            for col in numeric_cols[:6]
        }

    if cat_cols:
        result["value_counts"] = {
            col: df[col].value_counts().head(5).to_dict()
            for col in cat_cols[:4]
        }

    return {"stats_result": result}
