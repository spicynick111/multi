import pandas as pd
from models.state import ReportState


def validator_node(state: ReportState) -> dict:
    df = pd.read_csv(state["csv_path"], encoding="latin-1", encoding_errors="replace")

    column_types: dict = {}
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            column_types[col] = "datetime"
        elif pd.api.types.is_numeric_dtype(df[col]):
            column_types[col] = "numeric"
        else:
            try:
                pd.to_datetime(df[col], infer_datetime_format=True)
                column_types[col] = "datetime"
                df[col] = pd.to_datetime(df[col], infer_datetime_format=True)
            except Exception:
                column_types[col] = "categorical"

    # Drop rows where more than half of values are missing
    df = df.dropna(thresh=len(df.columns) // 2 + 1)

    # Fill remaining missing values
    for col in df.columns:
        if column_types.get(col) == "numeric":
            df[col] = df[col].fillna(df[col].median())
        elif column_types.get(col) == "categorical":
            mode = df[col].mode()
            df[col] = df[col].fillna(mode[0] if len(mode) > 0 else "Unknown")

    numeric_cols = [c for c, t in column_types.items() if t == "numeric"]
    datetime_cols = [c for c, t in column_types.items() if t == "datetime"]
    categorical_cols = [c for c, t in column_types.items() if t == "categorical"]

    validation_summary = {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "numeric_columns": numeric_cols,
        "datetime_columns": datetime_cols,
        "categorical_columns": categorical_cols,
    }

    log = state.get("progress_log", [])
    return {
        "df_json": df.to_json(orient="split", date_format="iso"),
        "column_types": column_types,
        "validation_summary": validation_summary,
        "progress_log": log + [
            f"✅ Data Validator — {len(df):,} rows · {len(df.columns)} columns · "
            f"{len(numeric_cols)} numeric · {len(datetime_cols)} date · {len(categorical_cols)} categorical"
        ],
    }
