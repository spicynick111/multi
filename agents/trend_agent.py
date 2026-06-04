import io
import pandas as pd
import numpy as np
from models.state import ReportState


def trend_node(state: ReportState) -> dict:
    df = pd.read_json(io.StringIO(state["df_json"]), orient="split")
    vs = state["validation_summary"]
    datetime_cols = vs.get("datetime_columns", [])
    numeric_cols = vs.get("numeric_columns", [])

    result: dict = {"has_trend_data": False}

    if not datetime_cols or not numeric_cols:
        return {"trend_result": result}

    date_col = datetime_cols[0]

    try:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)

        result["has_trend_data"] = True
        result["date_column"] = date_col
        result["date_range"] = {
            "start": str(df[date_col].min().date()),
            "end": str(df[date_col].max().date()),
        }

        # Monthly average for up to 3 numeric columns
        result["monthly_trends"] = {}
        for col in numeric_cols[:3]:
            monthly = (
                df.set_index(date_col)[col]
                .resample("ME")
                .mean()
                .dropna()
                .round(3)
            )
            result["monthly_trends"][col] = {
                str(k.date()): float(v) for k, v in monthly.items()
            }

        # Overall slope: increasing or decreasing
        result["trend_direction"] = {}
        x = np.arange(len(df))
        for col in numeric_cols[:3]:
            y = df[col].fillna(df[col].mean()).values
            slope = float(np.polyfit(x, y, 1)[0])
            result["trend_direction"][col] = "increasing" if slope > 0 else "decreasing"
            result[f"{col}_slope"] = round(slope, 4)

    except Exception as e:
        result["error"] = str(e)

    return {"trend_result": result}
