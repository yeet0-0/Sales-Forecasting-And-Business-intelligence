"""
STEP 8 - Build an editable Word version of the report.

Many colleges require a .docx submission, so this script renders the same
analysis as a formatted Word document with an auto-generated table of
contents, numbered headings, tables and all figures.

Output: reports/Project_Report.docx
"""

from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "reports"
FIG = REPORT_DIR / "figures"
OUT = REPORT_DIR / "Project_Report.docx"

SUMMARY = json.loads((REPORT_DIR / "summary.json").read_text(encoding="utf-8"))
FC = json.loads((REPORT_DIR / "forecast_metrics.json").read_text(encoding="utf-8"))
CLEAN = json.loads((REPORT_DIR / "cleaning_log.json").read_text(encoding="utf-8"))

KPI = SUMMARY["kpi"]
YEARLY = SUMMARY["yearly"]
REGION = SUMMARY["region"]
CATEGORY = SUMMARY["category"]
PRODUCT = SUMMARY["product"]
CHANNEL = SUMMARY["channel"]
SEGMENT = SUMMARY["segment"]
CONC = SUMMARY["concentration"]
SEASON = SUMMARY["seasonality"]
BEST = next(m for m in FC["comparison"] if m["model"] == FC["model"])

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
by_month = {m["month"]: m["avg_daily"] for m in SEASON["by_month"]}
PEAK = max(by_month, key=by_month.get)
LOW = min(by_month, key=by_month.get)

ACCENT = RGBColor(0x0F, 0x76, 0x6E)
INK = RGBColor(0x10, 0x18, 0x28)
MUTED = RGBColor(0x5B, 0x6B, 0x83)


def inr(value: float, decimals: int = 0) -> str:
    neg = value < 0
    s = f"{abs(value):.{decimals}f}"
    whole, _, frac = s.partition(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts) + "," + tail
    return ("-" if neg else "") + whole + (("." + frac) if frac else "")


def crore(v: float) -> str:
    return f"₹{v / 1e7:,.2f} crore"


# ------------------------------------------------------------------ document
doc = Document()
section = doc.sections[0]
section.page_height = Inches(11.69)
section.page_width = Inches(8.27)
section.top_margin = Inches(0.85)
section.bottom_margin = Inches(0.85)
section.left_margin = Inches(0.9)
section.right_margin = Inches(0.9)

styles = doc.styles
normal = styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(10.5)
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.12

for name, size, color, before, after in [
    ("Heading 1", 16, ACCENT, 20, 8),
    ("Heading 2", 12.5, INK, 14, 5),
]:
    st = styles[name]
    st.font.name = "Calibri"
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = color
    st.paragraph_format.space_before = Pt(before)
    st.paragraph_format.space_after = Pt(after)
    st.paragraph_format.keep_with_next = True


def p(text: str, *, size: float = 10.5, bold: bool = False, italic: bool = False,
      align=WD_ALIGN_PARAGRAPH.JUSTIFY, color=None, space_after: float = 6, style=None):
    para = doc.add_paragraph(style=style)
    para.alignment = align
    para.paragraph_format.space_after = Pt(space_after)
    run = para.add_run(text)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color is not None:
        run.font.color.rgb = color
    return para


def bullets(items):
    for item in items:
        para = doc.add_paragraph(style="List Bullet")
        para.paragraph_format.space_after = Pt(2)
        run = para.add_run(item)
        run.font.size = Pt(10.5)


def numbered(items):
    for item in items:
        para = doc.add_paragraph(style="List Number")
        para.paragraph_format.space_after = Pt(2)
        run = para.add_run(item)
        run.font.size = Pt(10.5)


def caption(text: str):
    cp = doc.add_paragraph()
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_after = Pt(10)
    run = cp.add_run(text)
    run.font.size = Pt(8.5)
    run.italic = True
    run.font.color.rgb = MUTED


def figure(name: str, cap: str, width: float = 6.1):
    doc.add_picture(str(FIG / name), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].paragraph_format.space_before = Pt(6)
    doc.paragraphs[-1].paragraph_format.keep_with_next = True
    caption(cap)


def shade(cell, hex_color: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def table(headers, rows, right_cols=(), font_size: float = 8.8, highlight_rows=()):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Table Grid"
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        para = hdr[i].paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.RIGHT if i in right_cols else WD_ALIGN_PARAGRAPH.LEFT
        run = para.add_run(h)
        run.bold = True
        run.font.size = Pt(font_size)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shade(hdr[i], "0F766E")
    for r_idx, row in enumerate(rows):
        cells = t.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = ""
            para = cells[i].paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.RIGHT if i in right_cols else WD_ALIGN_PARAGRAPH.LEFT
            run = para.add_run(str(value))
            run.font.size = Pt(font_size)
            if r_idx in highlight_rows:
                run.bold = True
                shade(cells[i], "ECFDF5")
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def add_field(paragraph, instruction: str):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(separate)
    run._r.append(end)


# ---------------------------------------------------------------- footer
footer_p = section.footer.paragraphs[0]
footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
foot_run = footer_p.add_run("Sales Forecasting & BI Dashboard  ·  Page ")
foot_run.font.size = Pt(8)
foot_run.font.color.rgb = MUTED
add_field(footer_p, "PAGE")

# ---------------------------------------------------------------- title page
for _ in range(3):
    doc.add_paragraph()
p("PROJECT REPORT", size=10, bold=True, color=ACCENT, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
tr = title.add_run("Sales Forecasting and Business Intelligence Dashboard\nUsing Data Analytics and Power BI")
tr.bold = True
tr.font.size = Pt(24)
tr.font.color.rgb = INK

p("A data-driven study of three years of retail transactions, ending in a six-month revenue "
  "forecast and an interactive BI dashboard", size=11, italic=True, color=MUTED,
  align=WD_ALIGN_PARAGRAPH.CENTER, space_after=26)

meta = [
    ("Submitted by", "«Your Name» — «Roll Number»"),
    ("Course", "«B.Tech / BCA / MBA — Semester»"),
    ("Faculty guide", "«Guide Name»"),
    ("Institute", "«College / University»"),
    ("Period analysed", f"{CLEAN['date_min']} to {CLEAN['date_max']}"),
    ("Records analysed", f"{CLEAN['rows_final']:,} clean transaction lines"),
]
t = doc.add_table(rows=0, cols=2)
t.alignment = WD_TABLE_ALIGNMENT.CENTER
for key, value in meta:
    cells = t.add_row().cells
    cells[0].text = ""
    cells[1].text = ""
    r1 = cells[0].paragraphs[0].add_run(key)
    r1.bold = True
    r1.font.size = Pt(10)
    r2 = cells[1].paragraphs[0].add_run(value)
    r2.font.size = Pt(10)

doc.add_page_break()

# ---------------------------------------------------------------- contents
doc.add_heading("Table of Contents", level=1)
toc_p = doc.add_paragraph()
add_field(toc_p, r'TOC \o "1-2" \h \z \u')
p("If the contents list appears empty, right-click it and choose “Update Field”.", size=9,
  italic=True, color=MUTED)
doc.add_page_break()

# ---------------------------------------------------------------- abstract
doc.add_heading("Abstract", level=1)
p(f"Retail businesses generate thousands of transactions every week, yet most of them review "
  f"performance as a monthly total. This project converts raw point-of-sale style data into a "
  f"decision system. A realistic three-year dataset of {CLEAN['rows_final']:,} transaction lines was "
  f"cleaned, modelled and analysed, and a monthly revenue series was forecast six months ahead using "
  f"five competing statistical and machine-learning models. The best model ({FC['model']}) achieved "
  f"{BEST['accuracy']:.2f}% forecast accuracy (MAPE {BEST['mape']:.2f}%) on a six-month hold-out window. "
  f"The cleaned data and forecast are exposed through a fully interactive business intelligence "
  f"dashboard that runs offline in any browser. The analysis shows that the business earned "
  f"{crore(KPI['revenue'])} of revenue at a {KPI['margin_pct']:.2f}% margin, that revenue is highly "
  f"seasonal ({MONTHS[PEAK - 1]} is {by_month[PEAK] / by_month[LOW]:.1f}× {MONTHS[LOW - 1]}), that "
  f"{REGION[0]['region']} is the largest region, and that deep discounts reduce margin without "
  f"proportional volume gains. The forecast projects {crore(FC['next_6m_total'])} for the next six "
  f"months, {FC['next_6m_growth_pct']:.1f}% above the same period last year.")
p("Keywords: business intelligence, sales forecasting, data analytics, Power BI, time-series "
  "forecasting, MAPE, Holt-Winters, SARIMA, dashboard design, data cleaning.", size=9, italic=True,
  color=MUTED, align=WD_ALIGN_PARAGRAPH.LEFT)

# ---------------------------------------------------------------- 1 introduction
doc.add_heading("1. Introduction", level=1)
p("Sales is the engine of every commercial organisation, and sales data is one of the richest assets "
  "it owns. Every order carries a date, a product, a customer, a region, a channel, a quantity, a price "
  "and a discount. Individually these are administrative records; collectively they describe demand, "
  "profitability and customer behaviour. The gap between having the data and using the data is what "
  "business intelligence (BI) closes.")
p("This project treats sales analytics as a complete pipeline: collect, clean, analyse, forecast, "
  "visualise, decide. Instead of stopping at descriptive charts, the analysis goes one step further and "
  "produces a six-month revenue forecast with quantified uncertainty. The result is a dashboard a sales "
  "manager could open every Monday morning to answer three questions: how are we doing, why, and what "
  "is likely to happen next?")
p("Power BI is the industry-standard tool for delivering such dashboards, and this report documents the "
  "full Power BI implementation plan. Because a submitted project must also be demonstrable on any "
  "machine, the same model has been implemented as a self-contained dashboard using Python for the "
  "analysis and standard web technologies for the visuals. Both versions share the same cleaned dataset, "
  "KPI definitions and forecast output, so the Power BI build guide reproduces the delivered dashboard "
  "one-to-one.")

# ---------------------------------------------------------------- 2 problem
doc.add_heading("2. Problem Statement and Objectives", level=1)
doc.add_heading("2.1 Problem statement", level=2)
p("A mid-sized multi-region retailer records sales across four regions, four product categories, four "
  "channels and three customer segments. Management currently reviews revenue as a single monthly "
  "figure. This creates three specific problems: (i) strong and weak products, regions and channels "
  "cancel each other out in the total; (ii) there is no forward view, so inventory and staffing are "
  "planned on intuition; and (iii) data quality issues in the source export — duplicates, inconsistent "
  "spellings, mixed date formats and impossible quantities — quietly distort every report built on it.")
doc.add_heading("2.2 Objectives", level=2)
numbered([
    "Design a repeatable data-cleaning pipeline that converts a raw transactional export into an analysis-ready table, with a documented audit of every correction.",
    "Perform exploratory analysis to quantify revenue, profitability, seasonality, regional and product concentration, and the effect of discounting.",
    "Build and compare five forecasting models on a held-out six-month window and select the most accurate model using MAPE.",
    "Produce a six-month revenue forecast with 80% and 95% prediction intervals, overall and by region.",
    "Deliver an interactive BI dashboard with KPI cards, filters and drill-down across overview, forecast, product, region and customer views.",
    "Translate the findings into concrete, prioritised business recommendations.",
])

# ---------------------------------------------------------------- 3 scope
doc.add_heading("3. Scope of the Study", level=1)
p(f"The study covers {CLEAN['date_min']} to {CLEAN['date_max']} at transaction-line granularity, with a "
  f"six-month forecast horizon. Revenue, cost and profit are analysed; marketing spend, inventory "
  f"holding cost and competitor pricing are out of scope because they are not present in the source "
  f"data. The dataset is a realistic simulation rather than a company extract, so the emphasis is on the "
  f"method and the decision framework rather than on the specific rupee values.")

# ---------------------------------------------------------------- 4 background
doc.add_heading("4. Background and Literature", level=1)
p("Business intelligence combines data warehousing, reporting and analytics to support managerial "
  "decisions. A standard BI architecture ingests operational data, models it into a star schema (fact "
  "table plus dimensions), and serves it through dashboards. Power BI implements this pattern with Power "
  "Query for extraction and transformation, a tabular model for relationships and DAX measures, and a "
  "report layer for visuals.")
p("Sales forecasting is a classical time-series problem. Exponential smoothing (Holt-Winters) models "
  "level, trend and seasonality with simple recursive updates and remains a strong baseline for monthly "
  "business series (Hyndman & Athanasopoulos, 2021). SARIMA extends ARIMA with seasonal differencing and "
  "is widely used for demand data. Regression with Fourier terms offers a compact way to capture smooth "
  "annual seasonality with a linear trend, and is often more stable than SARIMA when only three seasonal "
  "cycles are available. Because no single model dominates on short series, forecasters compare "
  "candidates on a hold-out window using error metrics such as MAE, RMSE and MAPE, and select the model "
  "that generalises best.")

# ---------------------------------------------------------------- 5 methodology
doc.add_heading("5. Methodology", level=1)
doc.add_heading("5.1 Pipeline", level=2)
p("Raw data → clean → model → analyse → forecast → visualise. Each stage is a separate, re-runnable "
  "script, and each produces a file that the next stage consumes. This keeps the work auditable and "
  "makes it trivial to refresh with new data.")
doc.add_heading("5.2 Tools and technology", level=2)
table(["Layer", "Tools used"], [
    ["Data cleaning and analysis", "Python 3.10+, pandas, NumPy"],
    ["Statistical forecasting", "statsmodels (Holt-Winters, SARIMA), scikit-learn (linear regression)"],
    ["Visualisation", "Matplotlib for report figures; Power BI Desktop for the BI report"],
    ["Interactive dashboard", "Vanilla JavaScript with hand-built SVG charts (offline, no dependencies)"],
    ["Reproducibility", "Numbered scripts executed by a single entry point"],
], font_size=9)

doc.add_heading("5.3 Data model (star schema)", level=2)
p("The cleaned table is a fact table at transaction-line grain. Four conformed dimensions — Date, "
  "Product (with Category), Region (with State) and Customer (with Segment) — plus a Channel dimension "
  "surround it. In Power BI these become separate tables with one-to-many relationships from each "
  "dimension to the fact table, which is what allows slicers to filter every visual consistently.")
p(f"Grain matters: an order can contain several line items, so counting rows would overstate orders by "
  f"{CLEAN['rows_final'] / KPI['orders']:.1f}×. Every order metric therefore uses DISTINCTCOUNT(Order_ID), "
  f"while revenue and units are additive and can be summed directly.", italic=True)

# ---------------------------------------------------------------- 6 dataset
doc.add_heading("6. Dataset and Data Cleaning", level=1)
doc.add_heading("6.1 Data dictionary", level=2)
table(["Column", "Type", "Description"], [
    ["Order_ID", "Text", "Order identifier; repeats across line items"],
    ["Order_Date", "Date", "Transaction date"],
    ["Customer_ID", "Text", "Customer key"],
    ["Region / State", "Text", "Geography"],
    ["Category / Product", "Text", "Product hierarchy"],
    ["Channel", "Text", "Online, Retail Store, Distributor, Corporate"],
    ["Segment", "Text", "Consumer, Corporate, Home Office"],
    ["Quantity", "Integer", "Units; negative for returns"],
    ["Unit_Price", "Decimal", "Selling price per unit"],
    ["Discount_Pct", "Integer", "Discount applied (0–30%)"],
    ["Sales", "Decimal", "Net revenue after discount"],
    ["Cost", "Decimal", "Cost of goods sold"],
    ["Profit", "Decimal", "Sales − Cost"],
], font_size=8.8)

doc.add_heading("6.2 Cleaning actions and audit", level=2)
p("The raw export intentionally contains the defects analysts meet in practice. Each defect is handled by "
  "an explicit rule, and the count of affected rows is logged so that nothing is silently dropped.")
table(["Check", "Rows", "Action"], [
    ["Rows in raw export", f"{CLEAN['rows_raw']:,}", "starting point"],
    ["Duplicate rows removed", f"{CLEAN['duplicates_removed']:,}", "exact full-row repeats"],
    ["Missing region values", f"{CLEAN['missing_region_flagged']:,}", "flagged Unknown, excluded from region charts"],
    ["Missing customer IDs", f"{CLEAN['missing_customer_flagged']:,}", "flagged UNKNOWN"],
    ["Missing discount values", f"{CLEAN['missing_discount_set_to_zero']:,}", "imputed as 0%"],
    ["Sales values corrected", f"{CLEAN['sales_values_corrected']:,}", "price × quantity × (1 − discount) check"],
    ["Outlier rows quarantined", f"{CLEAN['outlier_rows_quarantined']:,}", "quantity > 100 units"],
    ["Return lines retained", f"{CLEAN['return_lines']:,}", "negative quantity, flagged Is_Return"],
    ["Clean records for analysis", f"{CLEAN['rows_final']:,}", f"{CLEAN['date_min']} to {CLEAN['date_max']}"],
], right_cols=(1,), font_size=8.8)
p("Why keep returns? Removing negative-quantity rows would inflate reported revenue. Instead the "
  "pipeline keeps them, flags them with Is_Return, and reports net revenue. This makes the forecast "
  "conservative rather than optimistic.", italic=True)

# ---------------------------------------------------------------- 7 EDA
doc.add_heading("7. Exploratory Data Analysis", level=1)
table(["KPI", "Value"], [
    ["Total revenue", crore(KPI["revenue"])],
    ["Total profit", crore(KPI["profit"])],
    ["Profit margin", f"{KPI['margin_pct']:.2f}%"],
    ["Orders", f"{KPI['orders']:,}"],
    ["Average order value", f"₹{inr(KPI['aov'])}"],
    ["Units sold", f"{KPI['units']:,}"],
], right_cols=(1,), font_size=8.8)

doc.add_heading("7.1 Growth trend", level=2)
p(f"Revenue rose from {crore(YEARLY[0]['sales'])} in {YEARLY[0]['year']} to {crore(YEARLY[-1]['sales'])} "
  f"in {YEARLY[-1]['year']}. Growth was {YEARLY[1]['growth']:.1f}% in {YEARLY[1]['year']} and "
  f"{YEARLY[2]['growth']:.1f}% in {YEARLY[2]['year']}. The series is not a straight line: it oscillates "
  f"strongly within each year, which is the seasonality the forecast model must capture.")
table(["Year", "Revenue", "Profit", "Orders", "Growth"], [
    [str(y["year"]), inr(y["sales"]), inr(y["profit"]), f"{y['orders']:,}",
     "—" if y["growth"] is None else f"{y['growth']:.1f}%"] for y in YEARLY
], right_cols=(1, 2, 3, 4), font_size=8.8)
figure("fig_monthly_trend.png",
       "Figure 1 — Monthly revenue with a three-month moving average. Peaks cluster in October–November.")

doc.add_heading("7.2 Seasonality", level=2)
p(f"Seasonality is the single most actionable pattern in the data. {MONTHS[PEAK - 1]} is the strongest "
  f"month with an average daily revenue of ₹{inr(by_month[PEAK])}, while {MONTHS[LOW - 1]} is the "
  f"weakest at ₹{inr(by_month[LOW])} — a {by_month[PEAK] / by_month[LOW]:.1f}× swing. Inventory "
  f"build-up must start six to eight weeks before the peak to avoid stock-outs on high-value products.")
figure("fig_seasonality.png",
       "Figure 2 — Average daily revenue by calendar month, and a year × month revenue heatmap.")

doc.add_heading("7.3 Regional performance", level=2)
p(f"{REGION[0]['region']} leads with {REGION[0]['share']:.1f}% of revenue at a {REGION[0]['margin']:.2f}% "
  f"margin, while {REGION[-1]['region']} contributes {REGION[-1]['share']:.1f}%. Margins across regions are "
  f"within about one percentage point of each other, so the regional difference is a scale difference, "
  f"not a pricing or cost difference. Growth in the smaller region therefore has to come from volume and "
  f"distribution rather than from margin expansion.")
table(["Region", "Revenue", "Profit", "Margin", "Orders", "Share"], [
    [r["region"], inr(r["sales"]), inr(r["profit"]), f"{r['margin']:.2f}%",
     f"{r['orders']:,}", f"{r['share']:.1f}%"] for r in REGION
], right_cols=(1, 2, 3, 4, 5), font_size=8.8)
figure("fig_region_performance.png",
       "Figure 3 — Revenue and profit by region. Profit tracks revenue closely, confirming similar margins.")

doc.add_heading("7.4 Product and category mix", level=2)
p(f"{CATEGORY[0]['category']} generates {CATEGORY[0]['share']:.1f}% of revenue and "
  f"{CATEGORY[1]['category']} another {CATEGORY[1]['share']:.1f}%. The remaining categories are "
  f"high-frequency but low-ticket: they keep customers coming back and support cross-selling, yet they "
  f"cannot move total revenue on their own. Just {CONC['products_for_80pct']} of {CONC['total_products']} "
  f"products ({CONC['products_for_80pct'] / CONC['total_products'] * 100:.0f}%) generate 80% of revenue — "
  f"a textbook Pareto distribution.")
table(["Category", "Revenue", "Profit", "Margin", "Units", "Share"], [
    [c["category"], inr(c["sales"]), inr(c["profit"]), f"{c['margin']:.2f}%",
     f"{c['units']:,}", f"{c['share']:.1f}%"] for c in CATEGORY
], right_cols=(1, 2, 3, 4, 5), font_size=8.8)
figure("fig_category_share.png", "Figure 4 — Revenue share by category.")
figure("fig_pareto.png",
       f"Figure 5 — Pareto (ABC) analysis: the cumulative curve crosses 80% after "
       f"{CONC['products_for_80pct']} products.")

doc.add_heading("7.5 Top products", level=2)
table(["#", "Product", "Category", "Revenue", "Profit", "Units"], [
    [str(i + 1), prod["product"], prod["category"], inr(prod["sales"]), inr(prod["profit"]), f"{prod['units']:,}"]
    for i, prod in enumerate(PRODUCT[:10])
], right_cols=(3, 4, 5), font_size=8.5)
figure("fig_top_products.png", "Figure 6 — Top ten products by revenue.")

doc.add_heading("7.6 Channels and segments", level=2)
p(f"{CHANNEL[0]['channel']} is the largest channel by revenue "
  f"({CHANNEL[0]['sales'] / KPI['revenue'] * 100:.1f}% share) and "
  f"{sorted(CHANNEL, key=lambda c: -c['margin'])[0]['channel']} earns the highest margin at "
  f"{max(c['margin'] for c in CHANNEL):.2f}%. Corporate customers carry a slightly higher margin than "
  f"consumers, consistent with larger basket sizes and negotiated trade terms.")
table(["Channel", "Revenue", "Profit", "Margin", "Orders"], [
    [c["channel"], inr(c["sales"]), inr(c["profit"]), f"{c['margin']:.2f}%", f"{c['orders']:,}"]
    for c in CHANNEL
], right_cols=(1, 2, 3, 4), font_size=8.8)
table(["Segment", "Revenue", "Profit", "Margin", "Orders"], [
    [s["segment"], inr(s["sales"]), inr(s["profit"]), f"{s['margin']:.2f}%", f"{s['orders']:,}"]
    for s in SEGMENT
], right_cols=(1, 2, 3, 4), font_size=8.8)
figure("fig_channel_mix.png", "Figure 7 — Channel revenue with margin annotated.")

doc.add_heading("7.7 The cost of discounting", level=2)
p("Discounts are the fastest lever to move volume and the fastest way to destroy margin. Margin falls "
  "steadily as discount depth increases, and beyond 20% the business is trading profit for revenue. The "
  "dashboard makes this visible by default so that promotional decisions are made with the margin "
  "consequence in front of the decision maker.")
figure("fig_discount_impact.png", "Figure 8 — Profit margin by discount band versus the overall margin.")

# ---------------------------------------------------------------- 8 forecast
doc.add_heading("8. Sales Forecasting", level=1)
doc.add_heading("8.1 Approach", level=2)
p("Monthly revenue was aggregated into 36 observations. The first 30 months were used for training and "
  "the final 6 months were held back for validation, simulating a real “forecast the future with only "
  "the past available” situation. Five models plus an ensemble were fitted:")
bullets([
    "Seasonal Naive — repeats the value from the same month last year. A strong benchmark for seasonal business data.",
    "3-Month Moving Average — smooths recent noise; no trend or seasonality.",
    "Holt-Winters — additive trend and additive 12-month seasonality (exponential smoothing).",
    "SARIMA — seasonal ARIMA with differencing; captures autocorrelation.",
    "Linear Regression — trend plus two Fourier harmonics (sin/cos pairs) to model annual seasonality.",
    "Ensemble — average of the two best statistical models.",
])
p("Accuracy is measured with MAPE (mean absolute percentage error), complemented by MAE and RMSE. MAPE "
  "is preferred for reporting because it is scale-free and easy to explain to non-technical stakeholders.")

doc.add_heading("8.2 Hold-out results", level=2)
models_sorted = sorted(FC["comparison"], key=lambda m: m["mape"])
best_row = [i for i, m in enumerate(models_sorted) if m["model"] == FC["model"]]
table(["Model", "MAPE", "Accuracy", "RMSE"], [
    [m["model"], f"{m['mape']:.2f}%", f"{m['accuracy']:.2f}%", inr(m["rmse"])] for m in models_sorted
], right_cols=(1, 2, 3), font_size=8.8, highlight_rows=tuple(best_row))
figure("fig_model_comparison.png",
       "Figure 9 — MAPE by model on the six-month hold-out window (lower is better).")
p(f"Winner: {FC['model']} with {BEST['accuracy']:.2f}% accuracy. With only 36 observations, SARIMA's "
  f"seasonal parameters are weakly identified; the parsimonious regression with Fourier terms generalises "
  f"better. This is a useful lesson: on short series, a simpler model often wins.")

doc.add_heading("8.3 Final forecast", level=2)
p(f"The winning model was refitted on all 36 months. Prediction intervals are derived from the hold-out "
  f"error and widen with the square root of the horizon, reflecting growing uncertainty. The forecast "
  f"totals {crore(FC['next_6m_total'])} over the next six months, compared with "
  f"{crore(FC['next_6m_last_year'])} in the same period last year — growth of "
  f"{FC['next_6m_growth_pct']:.1f}%.")
table(["Month", "Forecast", "80% low", "80% high", "95% low", "95% high"], [
    [f"{MONTHS[int(f['month'][5:7]) - 1]} {f['month'][:4]}", inr(f["yhat"]), inr(f["lo80"]),
     inr(f["hi80"]), inr(f["lo95"]), inr(f["hi95"])] for f in FC["forecast"]
], right_cols=(1, 2, 3, 4, 5), font_size=8.8)
figure("fig_forecast.png",
       "Figure 10 — History, model fit and six-month forecast with prediction intervals.")
figure("fig_forecast_next.png", "Figure 11 — Point forecast by month with 95% intervals.")
table(["Region", "History (36 months)", "Forecast (6 months)", "Share of forecast"], [
    [r["name"], inr(r["history_total"]), inr(r["forecast_total"]),
     f"{r['forecast_total'] / r['history_total'] * 100:.1f}%"] for r in FC["by_region"]
], right_cols=(1, 2, 3), font_size=8.8)

# ---------------------------------------------------------------- 9 dashboard
doc.add_heading("9. Dashboard Design and Implementation", level=1)
doc.add_heading("9.1 Design principles", level=2)
bullets([
    "One screen, one question. Each tab answers a different question instead of packing every visual onto one page.",
    "Filter once, apply everywhere. A single filter bar (year, region, category, channel, segment) recomputes every KPI and chart on the active tab.",
    "Context on every number. KPI cards show the change versus the previous twelve months; charts use tooltips with exact values.",
    "Explain the “so what”. The overview ends with three automatically generated insights that restate the filtered data in business language.",
    "Accessible defaults. High-contrast palette, tabular numerals, no colour-only encoding of meaning.",
])
doc.add_heading("9.2 Dashboard pages", level=2)
table(["Page", "Content"], [
    ["Overview", "Six KPI cards with sparklines, revenue and profit trend, category donut, region comparison, channel mix, seasonality heatmap, discount-versus-margin, and three dynamic insights."],
    ["Forecast", "Six-month forecast with 80%/95% intervals, model comparison table, hold-out validation chart, month-wise table, regional forecast and method note."],
    ["Products", "Top products, Pareto curve, category margin comparison, concentration statistics and a sortable, searchable product table."],
    ["Regions", "Region scorecards with growth, category mix by region, top states and a region detail table."],
    ["Customers", "Segment mix, top customers, Lorenz concentration curve and customer statistics."],
    ["Data & Quality", "Data-quality audit tiles, paginated transaction browser with search, and one-click CSV export of the filtered selection."],
], font_size=8.8)

doc.add_heading("9.3 Power BI implementation", level=2)
p("The same report is implemented in Power BI Desktop using the cleaned CSV as the source. Power Query "
  "handles type conversions and text normalisation; the model uses a star schema with a dedicated Date "
  "table; DAX measures compute revenue, profit, margin, distinct orders, average order value and "
  "year-on-year growth. Slicers for year, region, category and channel drive page-level filter context. "
  "The forecast visual is produced by the built-in Analytics pane (exponential smoothing) and "
  "cross-checked against the Python forecast exported as a table. A step-by-step build guide is provided "
  "in docs/PowerBI_Build_Guide.md so the report can be reproduced without the original file. A "
  "ready-made star-schema workbook (data/clean/Sales_Data_Model.xlsx) is included for a one-click "
  "import.")

# ---------------------------------------------------------------- 10 results
doc.add_heading("10. Results and Business Recommendations", level=1)
numbered([
    f"Plan the year around {MONTHS[PEAK - 1]}–{MONTHS[PEAK % 12]}. The festive peak is "
    f"{by_month[PEAK] / by_month[LOW]:.1f}× the weakest month. Lock in stock, logistics and temporary "
    f"staffing at least six weeks early; a stock-out in the peak costs far more than holding cost.",
    "Protect margin from deep discounts. Orders with 20%+ discount earn a fraction of the normal margin. Replace blanket percentage discounts with bundle offers and loyalty credits that preserve the price anchor.",
    f"Grow the under-penetrated region. {REGION[-1]['region']} contributes only {REGION[-1]['share']:.1f}% "
    f"of revenue. Because regional margins are similar, incremental volume there converts to profit at "
    f"the normal rate.",
    f"Manage the product tail deliberately. {CONC['products_for_80pct']} products carry 80% of revenue. "
    f"Protect their availability; review or delist the long tail that adds complexity without contribution.",
    f"Retain the top customers. The top 10% of customers generate {CONC['top10_customer_share']:.1f}% of "
    f"revenue. Assign account management to them and measure retention explicitly.",
    "Use the forecast as a range, not a number. The 95% interval widens to several lakh by month six. Plan inventory to the upper bound and cash to the lower bound.",
])

doc.add_heading("11. Limitations and Future Scope", level=1)
bullets([
    "The dataset is a realistic simulation, not a live company extract. The method transfers directly; the specific values would change.",
    "Only 36 monthly observations are available, which limits the complexity of models that can be estimated reliably. With 5+ years of history, SARIMA and gradient-boosted trees would become stronger candidates.",
    "The forecast is univariate: it models revenue as a function of its own history. Promotion calendars, price changes, holidays and competitor actions are not explicit inputs.",
    "Inventory, marketing spend and customer acquisition cost are outside the dataset, so the recommendations are revenue- and margin-based rather than full profit-and-loss optimisations.",
    "Future work: hierarchical forecasting by region and category with reconciliation, probabilistic forecasting (quantile regression), automated retraining, and row-level security once the dashboard is published to the Power BI service.",
])

doc.add_heading("12. Conclusion", level=1)
p(f"This project demonstrates the complete path from raw transactional data to a decision-ready business "
  f"intelligence product. Cleaning recovered a trustworthy dataset and documented every correction. "
  f"Exploratory analysis exposed strong seasonality, a concentrated product portfolio, a clear regional "
  f"hierarchy and a measurable margin cost of discounting. Five forecasting models were compared on a "
  f"genuine hold-out window; the parsimonious regression with Fourier seasonality won with "
  f"{BEST['accuracy']:.2f}% accuracy and produced a six-month forecast of "
  f"{crore(FC['next_6m_total'])} with quantified uncertainty. Finally, an interactive dashboard packages "
  f"all of this into six focused pages that a manager can filter and read in seconds.")
p("The wider lesson is that business intelligence is not a charting exercise. Value appears when data "
  "quality is engineered, when the right model is selected through disciplined validation, and when the "
  "output is delivered at the moment of decision. The same architecture — clean, model, analyse, "
  "forecast, visualise — applies to almost any sales organisation.")

# ---------------------------------------------------------------- references
doc.add_heading("References", level=1)
refs = [
    "Hyndman, R.J. & Athanasopoulos, G. (2021). Forecasting: Principles and Practice, 3rd edition. OTexts.",
    "Box, G.E.P., Jenkins, G.M., Reinsel, G.C. & Ljung, G.M. (2015). Time Series Analysis: Forecasting and Control. Wiley.",
    "Few, S. (2012). Show Me the Numbers: Designing Tables and Graphs to Enlighten. Analytics Press.",
    "Kimball, R. & Ross, M. (2013). The Data Warehouse Toolkit, 3rd edition. Wiley.",
    "Microsoft (2024). Power BI documentation — data modelling, DAX and visualisation. learn.microsoft.com/power-bi.",
    "McKinney, W. (2022). Python for Data Analysis, 3rd edition. O'Reilly.",
    "Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. JMLR, 12, 2825–2830.",
]
for i, ref in enumerate(refs, start=1):
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(3)
    para.paragraph_format.left_indent = Inches(0.3)
    para.paragraph_format.first_line_indent = Inches(-0.3)
    run = para.add_run(f"[{i}] {ref}")
    run.font.size = Pt(9)

# ---------------------------------------------------------------- appendix
doc.add_page_break()
doc.add_heading("Appendix A — How to Run the Project", level=1)
p("One command rebuilds everything from scratch:  python run_project.py")
p("Then open dashboard/index.html in any modern browser. No server, internet connection or installation "
  "is required for the dashboard.")
table(["Path", "Contents"], [
    ["run_project.py", "Runs the full pipeline end to end"],
    ["src/01_generate_data.py", "Creates the realistic raw dataset"],
    ["src/02_clean_data.py", "Cleaning, validation and feature engineering"],
    ["src/03_eda_analysis.py", "KPIs, charts and insight generation"],
    ["src/04_forecast.py", "Model comparison and six-month forecast"],
    ["src/05_build_dashboard.py", "Packs data for the dashboard"],
    ["src/06_build_report.py", "Builds the HTML report"],
    ["src/07_build_excel.py", "Builds the Excel data model"],
    ["src/08_build_docx.py", "Builds this Word report"],
    ["dashboard/index.html", "Interactive dashboard (open directly)"],
    ["docs/PowerBI_Build_Guide.md", "Step-by-step Power BI rebuild guide"],
    ["docs/Viva_QA.md", "Likely viva questions with answers"],
    ["reports/figures/", "All charts used in this report"],
], font_size=8.8)

p("Note: replace the «placeholders» on the title page with your own details before submission.",
  size=9, italic=True, color=MUTED)

doc.save(str(OUT))
print(f"[docx] written -> {OUT}")
print(f"[docx] size: {OUT.stat().st_size / 1024:.0f} KB")
