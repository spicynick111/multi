import io
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from models.state import ReportState


def anomaly_node(state: ReportState) -> dict:
    df = pd.read_json(io.StringIO(state["df_json"]), orient="split")
    vs = state["validation_summary"]
    numeric_cols = vs.get("numeric_columns", [])

    result: dict = {"anomaly_count": 0, "anomaly_percentage": 0.0}

    if not numeric_cols:
        return {"anomaly_result": result}

    try:
        X = df[numeric_cols].fillna(0)

        iso = IsolationForest(contamination=0.05, random_state=42, n_jobs=-1)
        labels = iso.fit_predict(X)

        mask = labels == -1
        result["anomaly_count"] = int(mask.sum())
        result["anomaly_percentage"] = round(float(mask.mean()) * 100, 2)
        result["anomaly_indices"] = list(df.index[mask][:30])

        # Per-column Z-score outliers
        zscore_outliers = {}
        for col in numeric_cols[:6]:
            std = df[col].std()
            if std > 0:
                z = np.abs((df[col] - df[col].mean()) / std)
                count = int((z > 3).sum())
                if count > 0:
                    zscore_outliers[col] = count
        result["zscore_outliers"] = zscore_outliers

    except Exception as e:
        result["error"] = str(e)

    return {"anomaly_result": result}
