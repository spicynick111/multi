import os
from datetime import datetime

from fpdf import FPDF
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE as MSO
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from models.state import ReportState

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "reports")
PPTX_DIR    = os.path.join(os.path.dirname(__file__), "..", "outputs", "presentations")

# ── colour palette ────────────────────────────────────────────────────────────
C_BLUE   = (30,  64,  175)
C_LBLUE  = (59,  130, 246)
C_BG     = (239, 246, 255)
C_DARK   = (15,  23,  42)
C_GRAY   = (100, 116, 139)
C_WHITE  = (255, 255, 255)
C_GREEN  = (22,  163, 74)
C_AMBER  = (217, 119, 6)
C_RED    = (220, 38,  38)

PRIORITY_RGB = {"High": C_RED, "Medium": C_AMBER, "Low": C_GREEN}

# ── text sanitiser (Helvetica = latin-1 only) ─────────────────────────────────
_MAP = {
    "—":"--", "–":"-", "’":"'", "‘":"'",
    "“":'"',  "”":'"', "•":"*", "→":"->",
    "←":"<-", "↔":"<->","…":"..."," ":" ",
    "₹":"Rs", "€":"EUR","£":"GBP","✓":"OK",
    "✔":"OK",
}
def _s(t: str) -> str:
    if not t:
        return ""
    for c, r in _MAP.items():
        t = t.replace(c, r)
    return t.encode("latin-1", errors="replace").decode("latin-1")

def _trunc(s: str, n: int = 22) -> str:
    s = _s(str(s))
    return s[:n-1] + "…" if len(s) > n else s


# ══════════════════════════════════════════════════════════════════════════════
#  PDF
# ══════════════════════════════════════════════════════════════════════════════

class _PDF(FPDF):
    def __init__(self, title: str):
        super().__init__()
        self._title = _s(title)
        self.set_margins(18, 22, 18)
        self.set_auto_page_break(auto=True, margin=18)

    # ── running header ────────────────────────────────────────────────────────
    def header(self):
        if self.page == 1:
            return  # cover page has its own layout
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*C_GRAY)
        self.cell(0, 6, self._title, align="L", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*C_LBLUE)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    # ── running footer ────────────────────────────────────────────────────────
    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*C_GRAY)
        self.cell(0, 6, f"Page {self.page}  |  Generated {datetime.now().strftime('%d %b %Y')}", align="C")

    # ── helpers ───────────────────────────────────────────────────────────────
    def section(self, title: str):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*C_WHITE)
        self.set_fill_color(*C_BLUE)
        self.set_x(self.l_margin)
        self.cell(self.epw, 9, _s(title), fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*C_DARK)
        self.set_x(self.l_margin)
        self.multi_cell(self.epw, 6, _s(text))
        self.ln(2)

    def kv(self, label: str, value: str, bold_val: bool = False):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*C_GRAY)
        self.set_x(self.l_margin)
        self.cell(55, 7, _s(label))
        self.set_font("Helvetica", "B" if bold_val else "", 10)
        self.set_text_color(*C_DARK)
        self.set_x(self.l_margin + 55)
        self.multi_cell(self.epw - 55, 7, _s(str(value)))

    def th(self, cols: list, widths: list):
        """Table header row."""
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*C_WHITE)
        self.set_fill_color(*C_BLUE)
        self.set_x(self.l_margin)
        for col, w in zip(cols, widths):
            self.cell(w, 8, _s(col), border=1, fill=True, align="C")
        self.ln()

    def tr(self, vals: list, widths: list, shade: bool = False):
        """Table data row."""
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*C_DARK)
        if shade:
            self.set_fill_color(*C_BG)
        self.set_x(self.l_margin)
        for val, w in zip(vals, widths):
            self.cell(w, 7, _s(str(val)), border=1, fill=shade, align="C")
        self.ln()


def _cover_page(pdf: _PDF, state: dict, stem: str):
    vs = state.get("validation_summary", {})
    pdf.add_page()

    # Blue band
    pdf.set_fill_color(*C_BLUE)
    pdf.rect(0, 0, pdf.w, 65, style="F")

    # Title
    pdf.set_xy(18, 16)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*C_WHITE)
    pdf.cell(0, 12, "Business Intelligence Report", new_x="LMARGIN", new_y="NEXT")

    # Dataset name
    pdf.set_xy(18, 32)
    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(191, 219, 254)
    pdf.cell(0, 8, _s(stem), new_x="LMARGIN", new_y="NEXT")

    # Date
    pdf.set_xy(18, 50)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, datetime.now().strftime("%B %d, %Y"), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(18)

    # Key stat boxes (4 across)
    def stat_box(x, y, num, lbl):
        pdf.set_fill_color(*C_BG)
        pdf.rect(x, y, 40, 24, style="F")
        pdf.set_draw_color(*C_LBLUE)
        pdf.rect(x, y, 40, 24)
        pdf.set_xy(x, y + 3)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(*C_BLUE)
        pdf.cell(40, 10, str(num), align="C", new_x="RIGHT", new_y="TOP")
        pdf.set_xy(x, y + 14)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*C_GRAY)
        pdf.cell(40, 7, _s(lbl), align="C")

    anomaly = state.get("anomaly_result", {})
    corr    = state.get("correlation_result", {})
    base_x  = pdf.l_margin
    base_y  = pdf.get_y()
    gap     = (pdf.epw - 160) / 3

    stat_box(base_x,              base_y, f"{vs.get('rows',0):,}", "Records")
    stat_box(base_x + 40 + gap,   base_y, vs.get('columns', 0),    "Features")
    stat_box(base_x + 80 + 2*gap, base_y, anomaly.get("anomaly_count", 0), "Anomalies")
    stat_box(base_x + 120 + 3*gap,base_y, len(corr.get("top_pairs", [])), "Correlations")

    pdf.set_y(base_y + 32)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*C_GRAY)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, 5,
        _s(state.get("data_context", "")) or
        "This report provides a comprehensive analysis of the uploaded dataset."
    )


def _build_pdf(state: dict, stem: str, ts: str) -> str:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    vs       = state.get("validation_summary", {})
    stats    = state.get("stats_result", {})
    anomaly  = state.get("anomaly_result", {})
    corr     = state.get("correlation_result", {})
    trend    = state.get("trend_result", {})
    recs     = state.get("recommendations", [])

    pdf = _PDF(title=f"BI Report - {stem}")

    # ── Cover ─────────────────────────────────────────────────────────────────
    _cover_page(pdf, state, stem)

    # ── Executive Summary ─────────────────────────────────────────────────────
    pdf.add_page()
    pdf.section("Executive Summary")
    pdf.body(state.get("insights", "No insights generated."))

    # ── Statistical Analysis Table ────────────────────────────────────────────
    numeric_cols = vs.get("numeric_columns", [])
    if numeric_cols and stats.get("descriptive"):
        pdf.add_page()
        pdf.section("Statistical Analysis")
        ws = [44, 20, 22, 22, 20, 20, 22]
        pdf.th(["Column", "Count", "Mean", "Std Dev", "Min", "Max", "Median"], ws)
        desc = stats["descriptive"]
        for i, col in enumerate(numeric_cols[:12]):
            d = desc.get(col, {})
            pdf.tr([
                _trunc(col, 20),
                f"{d.get('count', 0):.0f}",
                f"{d.get('mean', 0):.2f}",
                f"{d.get('std', 0):.2f}",
                f"{d.get('min', 0):.2f}",
                f"{d.get('max', 0):.2f}",
                f"{d.get('50%', 0):.2f}",
            ], ws, shade=(i % 2 == 0))
        pdf.ln(4)

        # Skewness note
        skew = stats.get("skewness", {})
        highly_skewed = [c for c, v in skew.items() if abs(v) > 1]
        if highly_skewed:
            pdf.body(f"Highly skewed columns (|skew| > 1): {', '.join(highly_skewed[:5])}")

    # ── Correlation Table ─────────────────────────────────────────────────────
    if corr.get("top_pairs"):
        pdf.section("Correlation Analysis")
        wc = [50, 50, 30, 35, 35]
        pdf.th(["Column A", "Column B", "r Value", "Strength", "Direction"], wc)
        for i, p in enumerate(corr["top_pairs"][:10]):
            pdf.tr([
                _trunc(p["col1"], 22),
                _trunc(p["col2"], 22),
                str(p["correlation"]),
                p["strength"].capitalize(),
                p["direction"].capitalize(),
            ], wc, shade=(i % 2 == 0))
        pdf.ln(4)

    # ── Anomaly Detection ────────────────────────────────────────────────────
    if anomaly.get("anomaly_count", 0) > 0:
        pdf.section("Anomaly Detection")
        pdf.kv("Method", "Isolation Forest (contamination = 5%)")
        pdf.kv("Anomalies Found", f"{anomaly['anomaly_count']} records ({anomaly['anomaly_percentage']}%)", bold_val=True)
        pdf.ln(2)

        z_outliers = anomaly.get("zscore_outliers", {})
        if z_outliers:
            wz = [70, 50, 50]
            pdf.th(["Column", "Z-Score Outliers (>3)", "% of Column"], wz)
            for i, (col, cnt) in enumerate(list(z_outliers.items())[:8]):
                total = vs.get("rows", 1)
                pdf.tr([_trunc(col, 30), str(cnt), f"{cnt/total*100:.1f}%"], wz, shade=(i % 2 == 0))
            pdf.ln(4)

    # ── Trend Analysis ───────────────────────────────────────────────────────
    if trend.get("has_trend_data"):
        pdf.section("Trend Analysis")
        pdf.kv("Date Column",  trend.get("date_column", "-"))
        pdf.kv("Date Range",   f"{trend['date_range']['start']}  to  {trend['date_range']['end']}")
        pdf.ln(2)
        for col, direction in trend.get("trend_direction", {}).items():
            slope = trend.get(f"{col}_slope", 0)
            pdf.kv(f"{_trunc(col,20)} trend", f"{direction.capitalize()}  (slope: {slope:.4f})")
        pdf.ln(3)

    # ── Charts ───────────────────────────────────────────────────────────────
    chart_titles = [
        "Distribution of Key Metrics",
        "Correlation Matrix",
        "Trend Over Time",
        "Category Breakdown",
        "Anomaly Detection Scatter",
    ]
    for i, chart_path in enumerate(state.get("chart_paths", [])):
        if os.path.exists(chart_path):
            pdf.add_page()
            pdf.section(chart_titles[i] if i < len(chart_titles) else f"Chart {i+1}")
            try:
                pdf.image(chart_path, x=pdf.l_margin, y=pdf.get_y() + 2, w=pdf.epw)
            except Exception:
                pdf.body("[Chart could not be rendered]")

    # ── Recommendations ───────────────────────────────────────────────────────
    if recs:
        pdf.add_page()
        pdf.section("Strategic Recommendations")
        p_rgb = {"High": C_RED, "Medium": C_AMBER, "Low": C_GREEN}
        for i, rec in enumerate(recs, 1):
            pri = rec.get("priority", "Medium")
            color = p_rgb.get(pri, C_GRAY)

            # Priority badge
            pdf.set_fill_color(*color)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*C_WHITE)
            pdf.set_x(pdf.l_margin)
            pdf.cell(24, 7, f"  {pri.upper()}", fill=True, align="L")

            # Action heading
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*C_DARK)
            pdf.set_x(pdf.l_margin + 26)
            pdf.cell(pdf.epw - 26, 7, _s(f"{i}. {rec.get('action','')[:80]}"),
                     new_x="LMARGIN", new_y="NEXT")

            # Impact
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*C_GRAY)
            pdf.set_x(pdf.l_margin + 6)
            pdf.multi_cell(pdf.epw - 6, 6, _s(f"Impact: {rec.get('impact','')}"))
            pdf.ln(4)

    path = os.path.join(REPORTS_DIR, f"{stem}_{ts}.pdf")
    pdf.output(path)
    return path


# ══════════════════════════════════════════════════════════════════════════════
#  PowerPoint
# ══════════════════════════════════════════════════════════════════════════════

def _rgb(t): return RGBColor(*t)

def _add_band(slide, prs, title: str, subtitle: str = ""):
    """Navy header band with white title across the top of slide."""
    band = slide.shapes.add_shape(
        MSO.RECTANGLE, 0, 0, prs.slide_width, Inches(1.25)
    )
    band.fill.solid()
    band.fill.fore_color.rgb = _rgb(C_BLUE)
    band.line.fill.background()

    tb = slide.shapes.add_textbox(Inches(0.35), Inches(0.1), Inches(12.6), Inches(0.75))
    tf = tb.text_frame
    p = tf.paragraphs[0]
    p.text = _s(title)
    r = p.runs[0]; r.font.size = Pt(22); r.font.bold = True
    r.font.color.rgb = _rgb(C_WHITE)

    if subtitle:
        p2 = tf.add_paragraph()
        p2.text = _s(subtitle)
        r2 = p2.runs[0]; r2.font.size = Pt(11)
        r2.font.color.rgb = RGBColor(191, 219, 254)


def _add_text(slide, x, y, w, h, text: str, size=12, bold=False,
              color=None, align=PP_ALIGN.LEFT, wrap=True):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.text = _s(text)
    p.alignment = align
    r = p.runs[0]
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = _rgb(color or C_DARK)
    return tb


def _metric_card(slide, x, y, number, label, color=C_BLUE):
    """Floating metric card: big number + label."""
    W, H = 2.9, 1.55
    card = slide.shapes.add_shape(MSO.ROUNDED_RECTANGLE,
                                   Inches(x), Inches(y), Inches(W), Inches(H))
    card.fill.solid(); card.fill.fore_color.rgb = _rgb(C_BG)
    card.line.color.rgb = _rgb(color); card.line.width = Pt(1.8)

    # big number
    _add_text(slide, x, y + 0.12, W, 0.8, str(number),
              size=34, bold=True, color=color, align=PP_ALIGN.CENTER)
    # label
    _add_text(slide, x, y + 0.9, W, 0.45, _s(label),
              size=11, color=C_GRAY, align=PP_ALIGN.CENTER)


def _rec_card(slide, x, y, title: str, impact: str, priority: str):
    """Recommendation card with colored left-border."""
    W, H = 12.0, 1.1
    pri_color = {"High": C_RED, "Medium": C_AMBER, "Low": C_GREEN}.get(priority, C_GRAY)

    # card bg
    bg = slide.shapes.add_shape(MSO.RECTANGLE,
                                 Inches(x), Inches(y), Inches(W), Inches(H))
    bg.fill.solid(); bg.fill.fore_color.rgb = _rgb(C_BG)
    bg.line.fill.background()

    # left accent strip
    bar = slide.shapes.add_shape(MSO.RECTANGLE,
                                  Inches(x), Inches(y), Inches(0.12), Inches(H))
    bar.fill.solid(); bar.fill.fore_color.rgb = _rgb(pri_color)
    bar.line.fill.background()

    # priority badge text
    _add_text(slide, x + 0.2, y + 0.05, 0.8, 0.35,
              priority.upper(), size=8, bold=True, color=pri_color)
    # title
    _add_text(slide, x + 0.2, y + 0.32, W - 0.3, 0.4,
              _s(title[:110]), size=11, bold=True, color=C_DARK)
    # impact
    _add_text(slide, x + 0.2, y + 0.7, W - 0.3, 0.35,
              _s(f"Impact: {impact[:100]}"), size=9, color=C_GRAY)


def _build_pptx(state: dict, stem: str, ts: str) -> str:
    os.makedirs(PPTX_DIR, exist_ok=True)
    vs      = state.get("validation_summary", {})
    stats   = state.get("stats_result", {})
    anomaly = state.get("anomaly_result", {})
    corr    = state.get("correlation_result", {})
    trend   = state.get("trend_result", {})
    recs    = state.get("recommendations", [])

    prs = Presentation()
    prs.slide_width  = Inches(13.33)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # ── Slide 1: Title ────────────────────────────────────────────────────────
    sl = prs.slides.add_slide(blank)
    sl.background.fill.solid()
    sl.background.fill.fore_color.rgb = _rgb(C_BLUE)

    # White accent line
    line = sl.shapes.add_shape(MSO.RECTANGLE, 0, Inches(3.9), prs.slide_width, Inches(0.06))
    line.fill.solid(); line.fill.fore_color.rgb = _rgb(C_LBLUE); line.line.fill.background()

    _add_text(sl, 0.8, 1.5, 11.5, 1.3, "Business Intelligence Report",
              size=42, bold=True, color=C_WHITE, align=PP_ALIGN.LEFT)
    _add_text(sl, 0.8, 3.0, 11.5, 0.7, _s(stem).upper(),
              size=20, color=(191, 219, 254), align=PP_ALIGN.LEFT)
    _add_text(sl, 0.8, 4.2, 6.0, 0.5,
              datetime.now().strftime("Generated on %B %d, %Y"),
              size=12, color=(148, 163, 184), align=PP_ALIGN.LEFT)
    _add_text(sl, 0.8, 5.0, 6.0, 0.5,
              f"Powered by ReportAI  |  Multi-Agent LangGraph Pipeline",
              size=10, color=(100, 116, 139), align=PP_ALIGN.LEFT)

    # ── Slide 2: Key Metrics ─────────────────────────────────────────────────
    sl = prs.slides.add_slide(blank)
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = _rgb(C_WHITE)
    _add_band(sl, prs, "Key Metrics at a Glance", subtitle=f"Dataset: {_s(stem)}")

    _metric_card(sl, 0.4,  1.55, f"{vs.get('rows',0):,}",         "Total Records",       C_BLUE)
    _metric_card(sl, 3.45, 1.55, vs.get("columns", 0),             "Features Analysed",   C_LBLUE)
    _metric_card(sl, 6.5,  1.55, anomaly.get("anomaly_count", 0),  "Anomalies Detected",  C_RED)
    _metric_card(sl, 9.55, 1.55, len(corr.get("top_pairs", [])),   "Correlations Found",  C_GREEN)

    _metric_card(sl, 0.4,  3.45, len(vs.get("numeric_columns", [])),   "Numeric Features",  C_BLUE)
    _metric_card(sl, 3.45, 3.45, len(vs.get("categorical_columns",[])), "Category Features", C_LBLUE)
    _metric_card(sl, 6.5,  3.45, len(vs.get("datetime_columns", [])),   "Date Features",     C_AMBER)

    trend_dir = list(trend.get("trend_direction", {}).values())
    trend_str = trend_dir[0].capitalize() if trend_dir else "N/A"
    _metric_card(sl, 9.55, 3.45, trend_str, "Primary Trend", C_GREEN)

    # ── Slide 3: Executive Summary ───────────────────────────────────────────
    sl = prs.slides.add_slide(blank)
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = _rgb(C_WHITE)
    _add_band(sl, prs, "Executive Summary")
    _add_text(sl, 0.4, 1.4, 12.5, 5.8,
              _s(state.get("insights", ""))[:900],
              size=13, color=C_DARK, wrap=True)

    # ── Slide 4: Statistical Overview ────────────────────────────────────────
    numeric_cols = vs.get("numeric_columns", [])
    desc = stats.get("descriptive", {})
    if numeric_cols and desc:
        sl = prs.slides.add_slide(blank)
        sl.background.fill.solid(); sl.background.fill.fore_color.rgb = _rgb(C_WHITE)
        _add_band(sl, prs, "Statistical Overview", subtitle="Descriptive statistics for numeric columns")

        # Simple text table
        col_w = [2.5, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2]
        headers = ["Column", "Count", "Mean", "Std Dev", "Min", "Median", "Max"]
        TY = 1.45
        ROW_H = 0.38

        # Header row background
        hdr_bg = sl.shapes.add_shape(MSO.RECTANGLE,
                                      Inches(0.3), Inches(TY), Inches(12.7), Inches(ROW_H))
        hdr_bg.fill.solid(); hdr_bg.fill.fore_color.rgb = _rgb(C_BLUE); hdr_bg.line.fill.background()

        tx = 0.3
        for h, w in zip(headers, col_w):
            _add_text(sl, tx, TY + 0.04, w, ROW_H - 0.06, h,
                      size=10, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
            tx += w

        for ri, col in enumerate(numeric_cols[:14]):
            d = desc.get(col, {})
            row_y = TY + ROW_H * (ri + 1)
            if ri % 2 == 0:
                row_bg = sl.shapes.add_shape(MSO.RECTANGLE,
                                              Inches(0.3), Inches(row_y), Inches(12.7), Inches(ROW_H))
                row_bg.fill.solid(); row_bg.fill.fore_color.rgb = _rgb(C_BG); row_bg.line.fill.background()

            vals = [
                _trunc(col, 20),
                f"{d.get('count',0):.0f}",
                f"{d.get('mean',0):.2f}",
                f"{d.get('std',0):.2f}",
                f"{d.get('min',0):.2f}",
                f"{d.get('50%',0):.2f}",
                f"{d.get('max',0):.2f}",
            ]
            tx = 0.3
            for v, w in zip(vals, col_w):
                _add_text(sl, tx, row_y + 0.05, w, ROW_H - 0.08,
                          v, size=9, color=C_DARK, align=PP_ALIGN.CENTER)
                tx += w

    # ── Slide 5: Correlation Analysis ────────────────────────────────────────
    if corr.get("top_pairs"):
        sl = prs.slides.add_slide(blank)
        sl.background.fill.solid(); sl.background.fill.fore_color.rgb = _rgb(C_WHITE)
        _add_band(sl, prs, "Correlation Analysis", subtitle="Top variable relationships")

        pairs = corr["top_pairs"][:8]
        for i, p in enumerate(pairs):
            bar_y = 1.45 + i * 0.68
            strength_pct = abs(p["correlation"])
            bar_w = 8.0 * strength_pct

            col_c = C_GREEN if p["direction"] == "positive" else C_RED
            bg = sl.shapes.add_shape(MSO.RECTANGLE,
                                      Inches(4.0), Inches(bar_y + 0.12), Inches(8.0), Inches(0.3))
            bg.fill.solid(); bg.fill.fore_color.rgb = _rgb(C_BG); bg.line.fill.background()

            if bar_w > 0.05:
                bar = sl.shapes.add_shape(MSO.RECTANGLE,
                                           Inches(4.0), Inches(bar_y + 0.12), Inches(bar_w), Inches(0.3))
                bar.fill.solid(); bar.fill.fore_color.rgb = _rgb(col_c); bar.line.fill.background()

            _add_text(sl, 0.3, bar_y, 3.6, 0.55,
                      f"{_trunc(p['col1'],18)} × {_trunc(p['col2'],18)}",
                      size=10, bold=True, color=C_DARK)
            _add_text(sl, 12.1, bar_y + 0.08, 1.1, 0.4,
                      f"r={p['correlation']}", size=10, bold=True, color=col_c, align=PP_ALIGN.RIGHT)

    # ── Chart slides ──────────────────────────────────────────────────────────
    chart_labels = [
        "Distribution of Key Metrics",
        "Correlation Heatmap",
        "Trend Analysis",
        "Category Breakdown",
        "Anomaly Detection",
    ]
    for i, cp in enumerate(state.get("chart_paths", [])[:5]):
        if not os.path.exists(cp):
            continue
        sl = prs.slides.add_slide(blank)
        sl.background.fill.solid(); sl.background.fill.fore_color.rgb = _rgb(C_WHITE)
        lbl = chart_labels[i] if i < len(chart_labels) else f"Chart {i+1}"
        _add_band(sl, prs, lbl)
        try:
            sl.shapes.add_picture(cp, Inches(0.3), Inches(1.35),
                                   width=Inches(12.7), height=Inches(5.9))
        except Exception:
            _add_text(sl, 1, 3, 11, 1, "[Chart unavailable]", size=14, color=C_GRAY)

    # ── Recommendations slide ────────────────────────────────────────────────
    if recs:
        sl = prs.slides.add_slide(blank)
        sl.background.fill.solid(); sl.background.fill.fore_color.rgb = _rgb(C_WHITE)
        _add_band(sl, prs, "Strategic Recommendations",
                  subtitle="Data-backed action items")

        for i, rec in enumerate(recs[:5]):
            _rec_card(sl, 0.3, 1.4 + i * 1.22,
                      f"{i+1}. {rec.get('action','')}",
                      rec.get("impact", ""),
                      rec.get("priority", "Medium"))

    # ── Thank you slide ───────────────────────────────────────────────────────
    sl = prs.slides.add_slide(blank)
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = _rgb(C_BLUE)
    _add_text(sl, 1, 2.2, 11, 1.5, "Thank You",
              size=52, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
    _add_text(sl, 1, 4.0, 11, 0.6,
              "Generated by ReportAI — Autonomous Business Report Generator",
              size=14, color=(191, 219, 254), align=PP_ALIGN.CENTER)
    _add_text(sl, 1, 4.8, 11, 0.5,
              datetime.now().strftime("%B %d, %Y"),
              size=12, color=(148, 163, 184), align=PP_ALIGN.CENTER)

    path = os.path.join(PPTX_DIR, f"{stem}_{ts}.pptx")
    prs.save(path)
    return path


# ══════════════════════════════════════════════════════════════════════════════
#  Email draft
# ══════════════════════════════════════════════════════════════════════════════

def _build_email(state: dict) -> str:
    vs   = state.get("validation_summary", {})
    recs = state.get("recommendations", [])
    preview = state.get("insights", "")[:250]

    rec_lines = "\n".join(
        f"  {i}. [{r.get('priority','?')} Priority] {r.get('action','')}"
        for i, r in enumerate(recs, 1)
    )
    return (
        f"Subject: Business Intelligence Report — {datetime.now().strftime('%B %Y')} Analysis\n\n"
        "Hi Team,\n\n"
        f"Please find the latest data analysis report attached, covering "
        f"{vs.get('rows',0):,} records across {vs.get('columns',0)} dimensions.\n\n"
        f"Key Highlights:\n{preview}...\n\n"
        f"Top Recommendations:\n{rec_lines}\n\n"
        "The full report (PDF) and slide deck (PowerPoint) are attached.\n\n"
        "Best regards,\n[Your Name]\n\n"
        "---\nGenerated by ReportAI — Autonomous Business Report Generator\n"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  Node entry point
# ══════════════════════════════════════════════════════════════════════════════

def compiler_node(state: ReportState) -> dict:
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = state.get("filename", "dataset").replace(".csv", "").replace(" ", "_")

    pdf_path    = _build_pdf(state, stem, ts)
    pptx_path   = _build_pptx(state, stem, ts)
    email_draft = _build_email(state)

    log = state.get("progress_log", [])
    return {
        "pdf_path":    pdf_path,
        "pptx_path":   pptx_path,
        "email_draft": email_draft,
        "progress_log": log + ["✅ Report Compiler — PDF · PowerPoint · Email draft ready"],
    }
