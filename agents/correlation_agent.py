import io
import pandas as pd
import numpy as np
from models.state import ReportState


def correlation_node(state: ReportState) -> dict:
    df = pd.read_json(io.StringIO(state["df_json"]), orient="split")
    vs = state["validation_summary"]
    numeric_cols = vs.get("numeric_columns", [])

    result: dict = {}

    if len(numeric_cols) < 2:
        return {"correlation_result": result}

    corr = df[numeric_cols].corr().round(3)
    result["matrix"] = corr.to_dict()

    pairs = []
    for i, c1 in enumerate(numeric_cols):
        for c2 in numeric_cols[i + 1 :]:
            val = corr.loc[c1, c2]
            if not np.isnan(val):
                pairs.append({
                    "col1": c1,
                    "col2": c2,
                    "correlation": round(float(val), 3),
                    "strength": (
                        "strong" if abs(val) > 0.7
                        else "moderate" if abs(val) > 0.4
                        else "weak"
                    ),
                    "direction": "positive" if val > 0 else "negative",
                })

    pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
    result["top_pairs"] = pairs[:6]

    return {"correlation_result": result}
