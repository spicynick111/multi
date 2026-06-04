from typing import TypedDict, List


class ReportState(TypedDict):
    # Input
    csv_path: str
    filename: str
    df_json: str

    # Validation
    validation_summary: dict
    column_types: dict

    # Planning
    planned_analyses: List[str]
    data_context: str

    # Analysis results (each agent writes to its own key)
    stats_result: dict
    trend_result: dict
    anomaly_result: dict
    correlation_result: dict

    # Visualization
    chart_paths: List[str]

    # LLM outputs
    insights: str
    recommendations: List[dict]

    # Final outputs
    pdf_path: str
    pptx_path: str
    email_draft: str

    # Progress tracking
    progress_log: List[str]
