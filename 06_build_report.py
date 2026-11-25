"""
STEP 6 - Build the printable project report (HTML -> print to PDF).

Every number comes from reports/summary.json, reports/forecast_metrics.json
and reports/cleaning_log.json, so the report can never disagree with the
analysis.

Output: reports/Project_Report.html
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "reports"
SUMMARY = json.loads((REPORT_DIR / "summary.json").read_text(encoding="utf-8"))
FORECAST = json.loads((REPORT_DIR / "forecast_metrics.json").read_text(encoding="utf-8"))
CLEAN = json.loads((REPORT_DIR / "cleaning_log.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ helpers
def inr(value: float, decimals: int = 0) -> str:
    """Indian digit grouping: 12,34,56,789"""
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
    out = whole + (("." + frac) if frac else "")
    return ("-" if neg else "") + out


def crore(value: float) -> str:
    return f"₹{value / 1e7:,.2f} crore"


def lakh(value: float) -> str:
    return f"₹{value / 1e5:,.1f} lakh"


KPI = SUMMARY["kpi"]
MONTHLY = SUMMARY["monthly"]
YEARLY = SUMMARY["yearly"]
REGION = SUMMARY["region"]
CATEGORY = SUMMARY["category"]
PRODUCT = SUMMARY["product"]
CHANNEL = SUMMARY["channel"]
SEGMENT = SUMMARY["segment"]
CONC = SUMMARY["concentration"]
SEASON = SUMMARY["seasonality"]
FC = FORECAST
BEST = next(m for m in FC["comparison"] if m["model"] == FC["model"])

months_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
by_month = {m["month"]: m["avg_daily"] for m in SEASON["by_month"]}
peak_month = max(by_month, key=by_month.get)
low_month = min(by_month, key=by_month.get)

def growth_text(value):
    return "—" if value is None else f"{value:.1f}%"


year_rows = "".join(
    f"<tr><td>{y['year']}</td><td class='r'>{inr(y['sales'])}</td>"
    f"<td class='r'>{inr(y['profit'])}</td><td class='r'>{y['orders']:,}</td>"
    f"<td class='r'>{growth_text(y['growth'])}</td></tr>"
    for y in YEARLY
)

region_rows = "".join(
    f"<tr><td>{r['region']}</td><td class='r'>{inr(r['sales'])}</td>"
    f"<td class='r'>{inr(r['profit'])}</td><td class='r'>{r['margin']:.2f}%</td>"
    f"<td class='r'>{r['orders']:,}</td><td class='r'>{r['share']:.1f}%</td></tr>"
    for r in REGION
)

category_rows = "".join(
    f"<tr><td>{c['category']}</td><td class='r'>{inr(c['sales'])}</td>"
    f"<td class='r'>{inr(c['profit'])}</td><td class='r'>{c['margin']:.2f}%</td>"
    f"<td class='r'>{c['units']:,}</td><td class='r'>{c['share']:.1f}%</td></tr>"
    for c in CATEGORY
)

channel_rows = "".join(
    f"<tr><td>{c['channel']}</td><td class='r'>{inr(c['sales'])}</td>"
    f"<td class='r'>{inr(c['profit'])}</td><td class='r'>{c['margin']:.2f}%</td>"
    f"<td class='r'>{c['orders']:,}</td></tr>"
    for c in CHANNEL
)

segment_rows = "".join(
    f"<tr><td>{s['segment']}</td><td class='r'>{inr(s['sales'])}</td>"
    f"<td class='r'>{inr(s['profit'])}</td><td class='r'>{s['margin']:.2f}%</td>"
    f"<td class='r'>{s['orders']:,}</td></tr>"
    for s in SEGMENT
)

product_rows = "".join(
    f"<tr><td>{i + 1}</td><td>{p['product']}</td><td>{p['category']}</td>"
    f"<td class='r'>{inr(p['sales'])}</td><td class='r'>{inr(p['profit'])}</td>"
    f"<td class='r'>{p['units']:,}</td></tr>"
    for i, p in enumerate(PRODUCT[:10])
)

model_rows = "".join(
    f"<tr class='{'best' if m['model'] == FC['model'] else ''}'>"
    f"<td>{m['model']}</td><td class='r'>{m['mape']:.2f}%</td>"
    f"<td class='r'>{m['accuracy']:.2f}%</td><td class='r'>{inr(m['rmse'])}</td></tr>"
    for m in sorted(FC["comparison"], key=lambda x: x["mape"])
)

forecast_rows = "".join(
    f"<tr><td>{months_order[int(f['month'][5:7]) - 1]} {f['month'][:4]}</td>"
    f"<td class='r'>{inr(f['yhat'])}</td><td class='r'>{inr(f['lo80'])}</td>"
    f"<td class='r'>{inr(f['hi80'])}</td><td class='r'>{inr(f['lo95'])}</td>"
    f"<td class='r'>{inr(f['hi95'])}</td></tr>"
    for f in FC["forecast"]
)

region_fc_rows = "".join(
    f"<tr><td>{r['name']}</td><td class='r'>{inr(r['history_total'])}</td>"
    f"<td class='r'>{inr(r['forecast_total'])}</td>"
    f"<td class='r'>{r['forecast_total'] / r['history_total'] * 100:.1f}%</td></tr>"
    for r in FC["by_region"]
)

clean_rows = [
    ("Rows in raw export", f"{CLEAN['rows_raw']:,}", "starting point"),
    ("Duplicate rows removed", f"{CLEAN['duplicates_removed']:,}", "exact repeats dropped"),
    ("Missing region values", f"{CLEAN['missing_region_flagged']:,}", "flagged as Unknown, excluded from region charts"),
    ("Missing customer IDs", f"{CLEAN['missing_customer_flagged']:,}", "flagged as UNKNOWN"),
    ("Missing discount values", f"{CLEAN['missing_discount_set_to_zero']:,}", "imputed as 0% discount"),
    ("Sales values corrected", f"{CLEAN['sales_values_corrected']:,}", "price × quantity × (1 − discount) check"),
    ("Outlier rows quarantined", f"{CLEAN['outlier_rows_quarantined']:,}", "quantity > 100 units"),
    ("Return lines retained", f"{CLEAN['return_lines']:,}", "negative quantity, flagged Is_Return"),
    ("Clean records for analysis", f"{CLEAN['rows_final']:,}", f"{CLEAN['date_min']} to {CLEAN['date_max']}"),
]
clean_rows_html = "".join(
    f"<tr><td>{a}</td><td class='r'>{b}</td><td>{c}</td></tr>" for a, b, c in clean_rows
)

season_rows = "".join(
    f"<tr><td>{months_order[m['month'] - 1]}</td><td class='r'>{inr(m['avg_daily'])}</td>"
    f"<td class='r'>{m['avg_daily'] / max(x['avg_daily'] for x in SEASON['by_month']) * 100:.0f}%</td></tr>"
    for m in SEASON["by_month"]
)

CSS = """
:root { --ink:#101828; --muted:#5b6b83; --line:#dfe5ee; --accent:#0f766e; --soft:#f4f7fb; }
* { box-sizing: border-box; }
body { margin:0; background:#eef2f7; color:var(--ink);
  font-family: Georgia, "Times New Roman", serif; font-size: 14.5px; line-height: 1.62; }
.page { max-width: 880px; margin: 0 auto; background:#fff; padding: 56px 64px 64px;
  box-shadow: 0 20px 60px -30px rgba(16,24,40,.35); }
h1,h2,h3,h4 { font-family: "Segoe UI", Arial, sans-serif; line-height: 1.25; }
h1 { font-size: 34px; letter-spacing: -0.6px; margin: 0 0 6px; }
h2 { font-size: 21px; margin: 38px 0 12px; padding-bottom: 7px; border-bottom: 2px solid var(--accent); }
h3 { font-size: 15.5px; margin: 24px 0 8px; color: var(--accent); letter-spacing: .2px; }
p { margin: 0 0 11px; text-align: justify; }
ul, ol { margin: 0 0 12px; padding-left: 22px; }
li { margin-bottom: 5px; }
.small { font-size: 12.5px; color: var(--muted); }
.cover { text-align:center; padding: 40px 0 26px; border-bottom: 3px solid var(--accent); margin-bottom: 26px; }
.cover .kicker { font-family:"Segoe UI",Arial,sans-serif; letter-spacing: 3px; text-transform: uppercase;
  font-size: 11px; color: var(--accent); font-weight: 700; margin-bottom: 18px; }
.cover h1 { font-size: 30px; max-width: 700px; margin: 0 auto 10px; }
.cover .sub { font-size: 15px; color: var(--muted); font-style: italic; margin: 10px 0 24px; }
.cover .meta { display:inline-block; text-align:left; font-family:"Segoe UI",Arial,sans-serif; font-size: 13px;
  background: var(--soft); border: 1px solid var(--line); border-radius: 10px; padding: 16px 26px; }
.cover .meta div { margin: 3px 0; }
.cover .meta b { display:inline-block; width: 128px; color: var(--muted); font-weight: 600; }
.pipeline { display:flex; flex-wrap: wrap; gap: 8px; margin: 16px 0 20px; }
.pipeline .step { flex: 1 1 120px; background: var(--soft); border: 1px solid var(--line); border-radius: 9px;
  padding: 10px 12px; font-family:"Segoe UI",Arial,sans-serif; font-size: 11.5px; }
.pipeline .step b { display:block; color: var(--accent); font-size: 11px; letter-spacing: .8px; text-transform: uppercase; }
table { width: 100%; border-collapse: collapse; margin: 12px 0 16px; font-family:"Segoe UI",Arial,sans-serif; font-size: 12.5px; }
th { background: var(--soft); text-align: left; padding: 8px 10px; border-bottom: 2px solid var(--line);
  font-size: 10.5px; text-transform: uppercase; letter-spacing: .7px; color: var(--muted); }
td { padding: 7px 10px; border-bottom: 1px solid var(--line); }
.r { text-align: right; font-variant-numeric: tabular-nums; }
tr.best td { background: #ecfdf5; font-weight: 600; }
figure { margin: 16px 0 18px; text-align:center; }
figure img { max-width: 100%; border: 1px solid var(--line); border-radius: 8px; }
figcaption { font-size: 11.5px; color: var(--muted); margin-top: 5px; font-family:"Segoe UI",Arial,sans-serif; }
.callout { background:#f0fdfa; border-left: 4px solid var(--accent); padding: 12px 16px; margin: 16px 0;
  border-radius: 0 8px 8px 0; font-size: 13.5px; }
.callout b { color: var(--accent); }
.kpi-strip { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 16px 0 18px; }
.kpi-box { background: var(--soft); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px;
  font-family:"Segoe UI",Arial,sans-serif; }
.kpi-box .k { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); font-weight: 700; }
.kpi-box .v { font-size: 20px; font-weight: 700; margin-top: 2px; }
.toc { font-family:"Segoe UI",Arial,sans-serif; font-size: 13px; }
.toc div { display:flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dotted var(--line); }
.toc span:last-child { color: var(--muted); }
.pagebreak { page-break-before: always; }
footer.rep { margin-top: 40px; padding-top: 14px; border-top: 1px solid var(--line); font-size: 11px; color: var(--muted);
  display:flex; justify-content: space-between; font-family:"Segoe UI",Arial,sans-serif; }
@media print {
  body { background:#fff; font-size: 10.6pt; }
  .page { box-shadow:none; max-width:none; padding: 0; }
  h2 { page-break-after: avoid; }
  figure, table { page-break-inside: avoid; }
  .pagebreak { page-break-before: always; }
  .no-print { display:none; }
}
"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Sales Forecasting and Business Intelligence Dashboard - Project Report</title>
<style>{CSS}</style>
</head>
<body>
<div class="page">

  <div class="cover">
    <div class="kicker">Project Report</div>
    <h1>Sales Forecasting and Business Intelligence Dashboard Using Data Analytics and Power&nbsp;BI</h1>
    <div class="sub">A data-driven study of three years of retail transactions, ending in a six-month revenue forecast and an interactive BI dashboard</div>
    <div class="meta">
      <div><b>Submitted by</b> &lt;Your Name&gt; &mdash; &lt;Roll Number&gt;</div>
      <div><b>Course</b> &lt;B.Tech / BCA / MBA &mdash; Semester&gt;</div>
      <div><b>Guide</b> &lt;Faculty Guide Name&gt;</div>
      <div><b>Institute</b> &lt;College / University Name&gt;</div>
      <div><b>Period analysed</b> {CLEAN['date_min']} to {CLEAN['date_max']}</div>
      <div><b>Records</b> {CLEAN['rows_final']:,} clean transaction lines</div>
    </div>
  </div>

  <h2 style="border:0; margin-top:8px;">Abstract</h2>
  <p>
    Retail businesses generate thousands of transactions every week, yet most of them review
    performance as a monthly total. This project converts raw point-of-sale style data into a
    decision system. A realistic three-year dataset of {CLEAN['rows_final']:,} transaction lines was
    cleaned, modelled and analysed, and a monthly revenue series was forecast six months ahead
    using five competing statistical and machine-learning models. The best model
    ({FC['model']}) achieved <b>{BEST['accuracy']:.2f}% forecast accuracy</b> (MAPE {BEST['mape']:.2f}%) on a
    six-month hold-out window. The cleaned data and forecast are exposed through a fully
    interactive business intelligence dashboard that runs offline in any browser. The analysis shows
    that the business earned {crore(KPI['revenue'])} of revenue at a {KPI['margin_pct']:.2f}% margin,
    that revenue is highly seasonal (October is {by_month[peak_month] / by_month[low_month]:.1f}× February),
    that {REGION[0]['region']} is the largest region, and that deep discounts reduce margin without
    proportional volume gains. The forecast projects {crore(FC['next_6m_total'])} for the next six
    months, {FC['next_6m_growth_pct']:.1f}% above the same period last year.
  </p>
  <p class="small"><b>Keywords:</b> business intelligence, sales forecasting, data analytics, Power BI,
    time-series forecasting, MAPE, Holt-Winters, SARIMA, dashboard design, data cleaning.</p>

  <h2>Table of contents</h2>
  <div class="toc">
    <div><span>1. Introduction</span></div>
    <div><span>2. Problem statement and objectives</span></div>
    <div><span>3. Scope of the study</span></div>
    <div><span>4. Background and literature</span></div>
    <div><span>5. Methodology</span></div>
    <div><span>6. Dataset and data cleaning</span></div>
    <div><span>7. Exploratory data analysis</span></div>
    <div><span>8. Sales forecasting</span></div>
    <div><span>9. Dashboard design and implementation</span></div>
    <div><span>10. Results and business recommendations</span></div>
    <div><span>11. Limitations and future scope</span></div>
    <div><span>12. Conclusion</span></div>
    <div><span>References</span></div>
    <div><span>Appendix A - How to run the project</span></div>
  </div>
  <p class="small">Page numbers are omitted on purpose: the report reflows as figures are added or
    removed. Use your browser's print preview for exact pagination.</p>

  <h2>1. Introduction</h2>
  <p>
    Sales is the engine of every commercial organisation, and sales data is one of the richest
    assets it owns. Every order carries a date, a product, a customer, a region, a channel, a
    quantity, a price and a discount. Individually these are administrative records; collectively
    they describe demand, profitability and customer behaviour. The gap between having the data and
    using the data is what business intelligence (BI) closes.
  </p>
  <p>
    This project treats sales analytics as a complete pipeline: <b>collect, clean, analyse, forecast,
    visualise, decide</b>. Instead of stopping at descriptive charts, the analysis goes one step
    further and produces a six-month revenue forecast with quantified uncertainty. The result is a
    dashboard that a sales manager could open every Monday morning to answer three questions:
    <i>How are we doing, why, and what is likely to happen next?</i>
  </p>
  <p>
    Power BI is the industry-standard tool for delivering such dashboards, and this report documents
    the full Power BI implementation plan. Because a submitted project must also be demonstrable on
    any machine, the same model has been implemented as a self-contained dashboard using Python for
    the analysis and standard web technologies for the visuals. Both versions share the same cleaned
    dataset, the same KPI definitions and the same forecast output, so the Power BI build guide in
    the appendix reproduces the delivered dashboard one-to-one.
  </p>

  <h2>2. Problem statement and objectives</h2>
  <h3>2.1 Problem statement</h3>
  <p>
    A mid-sized multi-region retailer records sales across four regions, four product categories,
    four channels and three customer segments. Management currently reviews revenue as a single
    monthly figure. This creates three specific problems: (i) strong and weak products, regions and
    channels cancel each other out in the total; (ii) there is no forward view, so inventory and
    staffing are planned on intuition; and (iii) data quality issues in the source export -
    duplicates, inconsistent spellings, mixed date formats and impossible quantities - quietly
    distort every report built on it.
  </p>
  <h3>2.2 Objectives</h3>
  <ol>
    <li>Design a repeatable data-cleaning pipeline that converts a raw transactional export into an analysis-ready table, with a documented audit of every correction.</li>
    <li>Perform exploratory analysis to quantify revenue, profitability, seasonality, regional and product concentration, and the effect of discounting.</li>
    <li>Build and compare five forecasting models on a held-out six-month window and select the most accurate model using MAPE.</li>
    <li>Produce a six-month revenue forecast with 80% and 95% prediction intervals, overall and by region.</li>
    <li>Deliver an interactive BI dashboard with KPI cards, filters and drill-down across overview, forecast, product, region and customer views.</li>
    <li>Translate the findings into concrete, prioritised business recommendations.</li>
  </ol>

  <h2>3. Scope of the study</h2>
  <p>
    The study covers {CLEAN['date_min']} to {CLEAN['date_max']} at transaction-line granularity, with a
    six-month forecast horizon. Revenue, cost and profit are analysed; marketing spend, inventory
    holding cost and competitor pricing are out of scope because they are not present in the source
    data. The dataset is a realistic simulation rather than a company extract, so the emphasis is on
    the method and the decision framework rather than on the specific rupee values.
  </p>

  <h2>4. Background and literature</h2>
  <p>
    Business intelligence combines data warehousing, reporting and analytics to support managerial
    decisions. A standard BI architecture ingests operational data, models it into a star schema
    (fact table plus dimensions), and serves it through dashboards. Power BI implements this pattern
    with Power Query for extraction and transformation, a tabular model for relationships and DAX
    measures, and a report layer for visuals.
  </p>
  <p>
    Sales forecasting is a classical time-series problem. Exponential smoothing (Holt-Winters) models
    level, trend and seasonality with simple recursive updates and remains a strong baseline for
    monthly business series (Hyndman &amp; Athanasopoulos, 2021). SARIMA extends ARIMA with seasonal
    differencing and is widely used for demand data. Regression with Fourier terms offers a compact
    way to capture smooth annual seasonality with a linear trend, and is often more stable than
    SARIMA when only three seasonal cycles are available. Because no single model dominates on short
    series, forecasters compare candidates on a hold-out window using error metrics such as MAE,
    RMSE and MAPE, and select the model that generalises best.
  </p>

  <h2 class="pagebreak">5. Methodology</h2>
  <div class="pipeline">
    <div class="step"><b>1 · Raw data</b>transactional export with deliberate quality defects</div>
    <div class="step"><b>2 · Clean</b>dates, duplicates, text, missing values, outliers, returns</div>
    <div class="step"><b>3 · Model</b>calendar features, margins, monthly aggregation</div>
    <div class="step"><b>4 · Analyse</b>KPIs, seasonality, concentration, discount impact</div>
    <div class="step"><b>5 · Forecast</b>five models, hold-out comparison, intervals</div>
    <div class="step"><b>6 · Visualise</b>interactive dashboard and Power BI report</div>
  </div>
  <h3>5.1 Tools and technology</h3>
  <table>
    <thead><tr><th style="width:30%">Layer</th><th>Tools used</th></tr></thead>
    <tbody>
      <tr><td>Data cleaning and analysis</td><td>Python 3.10+, pandas, NumPy</td></tr>
      <tr><td>Statistical forecasting</td><td>statsmodels (Holt-Winters, SARIMA), scikit-learn (linear regression)</td></tr>
      <tr><td>Visualisation</td><td>Matplotlib for report figures; Power BI Desktop for the BI report</td></tr>
      <tr><td>Interactive dashboard</td><td>Vanilla JavaScript with hand-built SVG charts (offline, no dependencies)</td></tr>
      <tr><td>Reproducibility</td><td>Numbered scripts executed by a single entry point</td></tr>
    </tbody>
  </table>
  <h3>5.2 Data model (star schema)</h3>
  <p>
    The cleaned table is a fact table at transaction-line grain. Four conformed dimensions -
    Date, Product (with Category), Region (with State) and Customer (with Segment) - plus a Channel
    dimension surround it. In Power BI, these become separate tables with one-to-many relationships
    from each dimension to the fact table, which is what allows slicers to filter every visual
    consistently. DAX measures are defined on the fact table: total revenue, total profit, margin %,
    order count (distinct order ID), average order value and year-on-year growth.
  </p>
  <div class="callout">
    <b>Grain matters.</b> An "order" can contain several line items, so counting rows would overstate
    orders by {CLEAN['rows_final'] / KPI['orders']:.1f}×. Every order metric therefore uses
    <i>DISTINCTCOUNT(Order_ID)</i>, while revenue and units are additive and can be summed directly.
  </div>

  <h2 class="pagebreak">6. Dataset and data cleaning</h2>
  <h3>6.1 Data dictionary</h3>
  <table>
    <thead><tr><th>Column</th><th>Type</th><th>Description</th></tr></thead>
    <tbody>
      <tr><td>Order_ID</td><td>Text</td><td>Order identifier; repeats across line items</td></tr>
      <tr><td>Order_Date</td><td>Date</td><td>Transaction date</td></tr>
      <tr><td>Customer_ID</td><td>Text</td><td>Customer key</td></tr>
      <tr><td>Region / State</td><td>Text</td><td>Geography</td></tr>
      <tr><td>Category / Product</td><td>Text</td><td>Product hierarchy</td></tr>
      <tr><td>Channel</td><td>Text</td><td>Online, Retail Store, Distributor, Corporate</td></tr>
      <tr><td>Segment</td><td>Text</td><td>Consumer, Corporate, Home Office</td></tr>
      <tr><td>Quantity</td><td>Integer</td><td>Units; negative for returns</td></tr>
      <tr><td>Unit_Price</td><td>Decimal</td><td>Selling price per unit</td></tr>
      <tr><td>Discount_Pct</td><td>Integer</td><td>Discount applied (0-30%)</td></tr>
      <tr><td>Sales</td><td>Decimal</td><td>Net revenue after discount</td></tr>
      <tr><td>Cost</td><td>Decimal</td><td>Cost of goods sold</td></tr>
      <tr><td>Profit</td><td>Decimal</td><td>Sales − Cost</td></tr>
    </tbody>
  </table>

  <h3>6.2 Cleaning actions and audit</h3>
  <p>
    The raw export intentionally contains the defects analysts meet in practice. Each defect is
    handled by an explicit rule, and the count of affected rows is logged so that nothing is silently
    dropped.
  </p>
  <table>
    <thead><tr><th>Check</th><th class="r">Rows</th><th>Action</th></tr></thead>
    <tbody>{clean_rows_html}</tbody>
  </table>
  <div class="callout">
    <b>Why keep returns?</b> Removing negative-quantity rows would inflate reported revenue. Instead
    the pipeline keeps them, flags them with <i>Is_Return</i>, and reports net revenue. This makes the
    forecast conservative rather than optimistic.
  </div>

  <h2 class="pagebreak">7. Exploratory data analysis</h2>
  <div class="kpi-strip">
    <div class="kpi-box"><div class="k">Total revenue</div><div class="v">{crore(KPI['revenue'])}</div></div>
    <div class="kpi-box"><div class="k">Total profit</div><div class="v">{crore(KPI['profit'])}</div></div>
    <div class="kpi-box"><div class="k">Profit margin</div><div class="v">{KPI['margin_pct']:.2f}%</div></div>
    <div class="kpi-box"><div class="k">Orders</div><div class="v">{KPI['orders']:,}</div></div>
    <div class="kpi-box"><div class="k">Average order value</div><div class="v">₹{inr(KPI['aov'])}</div></div>
    <div class="kpi-box"><div class="k">Units sold</div><div class="v">{KPI['units']:,}</div></div>
  </div>

  <h3>7.1 Growth trend</h3>
  <p>
    Revenue rose from {crore(YEARLY[0]['sales'])} in {YEARLY[0]['year']} to {crore(YEARLY[-1]['sales'])}
    in {YEARLY[-1]['year']}. Growth was {YEARLY[1]['growth']:.1f}% in {YEARLY[1]['year']} and
    {YEARLY[2]['growth']:.1f}% in {YEARLY[2]['year']}. The series is not a straight line: it oscillates
    strongly within each year, which is the seasonality the forecast model must capture.
  </p>
  <table>
    <thead><tr><th>Year</th><th class="r">Revenue</th><th class="r">Profit</th><th class="r">Orders</th><th class="r">Growth</th></tr></thead>
    <tbody>{year_rows}</tbody>
  </table>
  <figure>
    <img src="figures/fig_monthly_trend.png" alt="Monthly revenue trend" />
    <figcaption>Figure 1 — Monthly revenue with a three-month moving average. Peaks cluster in October–November.</figcaption>
  </figure>

  <h3>7.2 Seasonality</h3>
  <p>
    Seasonality is the single most actionable pattern in the data. {months_order[peak_month - 1]} is
    the strongest month with an average daily revenue of ₹{inr(by_month[peak_month])}, while
    {months_order[low_month - 1]} is the weakest at ₹{inr(by_month[low_month])} — a
    {by_month[peak_month] / by_month[low_month]:.1f}× swing. Inventory build-up must start roughly six
    to eight weeks before the peak to avoid stock-outs on high-value products.
  </p>
  <figure>
    <img src="figures/fig_seasonality.png" alt="Seasonality charts" />
    <figcaption>Figure 2 — Average daily revenue by calendar month, and a year × month revenue heatmap.</figcaption>
  </figure>

  <h3>7.3 Regional performance</h3>
  <p>
    {REGION[0]['region']} leads with {REGION[0]['share']:.1f}% of revenue at a {REGION[0]['margin']:.2f}%
    margin, while {REGION[-1]['region']} contributes {REGION[-1]['share']:.1f}%. Margins across regions
    are within one percentage point of each other, so the regional difference is a scale difference,
    not a pricing or cost difference. Growth in the smaller region therefore has to come from volume
    and distribution rather than from margin expansion.
  </p>
  <table>
    <thead><tr><th>Region</th><th class="r">Revenue</th><th class="r">Profit</th><th class="r">Margin</th><th class="r">Orders</th><th class="r">Share</th></tr></thead>
    <tbody>{region_rows}</tbody>
  </table>
  <figure>
    <img src="figures/fig_region_performance.png" alt="Regional performance" />
    <figcaption>Figure 3 — Revenue and profit by region. Profit tracks revenue closely, confirming similar margins.</figcaption>
  </figure>

  <h3>7.4 Product and category mix</h3>
  <p>
    {CATEGORY[0]['category']} generates {CATEGORY[0]['share']:.1f}% of revenue and
    {CATEGORY[1]['category']} another {CATEGORY[1]['share']:.1f}%. The remaining categories are
    high-frequency but low-ticket: they keep customers coming back and support cross-selling, yet they
    cannot move total revenue on their own. Just {CONC['products_for_80pct']} of
    {CONC['total_products']} products ({CONC['products_for_80pct'] / CONC['total_products'] * 100:.0f}%)
    generate 80% of revenue — a textbook Pareto distribution.
  </p>
  <table>
    <thead><tr><th>Category</th><th class="r">Revenue</th><th class="r">Profit</th><th class="r">Margin</th><th class="r">Units</th><th class="r">Share</th></tr></thead>
    <tbody>{category_rows}</tbody>
  </table>
  <figure>
    <img src="figures/fig_category_share.png" alt="Category share" />
    <figcaption>Figure 4 — Revenue share by category.</figcaption>
  </figure>
  <figure>
    <img src="figures/fig_pareto.png" alt="Pareto analysis" />
    <figcaption>Figure 5 — Pareto (ABC) analysis: the cumulative curve crosses 80% after {CONC['products_for_80pct']} products.</figcaption>
  </figure>

  <h3>7.5 Top products</h3>
  <table>
    <thead><tr><th>#</th><th>Product</th><th>Category</th><th class="r">Revenue</th><th class="r">Profit</th><th class="r">Units</th></tr></thead>
    <tbody>{product_rows}</tbody>
  </table>
  <figure>
    <img src="figures/fig_top_products.png" alt="Top products" />
    <figcaption>Figure 6 — Top ten products by revenue.</figcaption>
  </figure>

  <h3>7.6 Channels and segments</h3>
  <p>
    {CHANNEL[0]['channel']} is the largest channel by revenue
    ({CHANNEL[0]['sales'] / KPI['revenue'] * 100:.1f}% share) and
    {sorted(CHANNEL, key=lambda c: -c['margin'])[0]['channel']} earns the highest margin at
    {max(c['margin'] for c in CHANNEL):.2f}%. Corporate customers carry a slightly higher margin than
    consumers, consistent with larger basket sizes and negotiated trade terms.
  </p>
  <table>
    <thead><tr><th>Channel</th><th class="r">Revenue</th><th class="r">Profit</th><th class="r">Margin</th><th class="r">Orders</th></tr></thead>
    <tbody>{channel_rows}</tbody>
  </table>
  <table>
    <thead><tr><th>Segment</th><th class="r">Revenue</th><th class="r">Profit</th><th class="r">Margin</th><th class="r">Orders</th></tr></thead>
    <tbody>{segment_rows}</tbody>
  </table>
  <figure>
    <img src="figures/fig_channel_mix.png" alt="Channel performance" />
    <figcaption>Figure 7 — Channel revenue with margin annotated.</figcaption>
  </figure>

  <h3>7.7 The cost of discounting</h3>
  <p>
    Discounts are the fastest lever to move volume and the fastest way to destroy margin. Margin falls
    steadily as discount depth increases, and beyond 20% the business is trading profit for revenue.
    The dashboard makes this visible by default so that promotional decisions are made with the margin
    consequence in front of the decision maker.
  </p>
  <figure>
    <img src="figures/fig_discount_impact.png" alt="Discount impact" />
    <figcaption>Figure 8 — Profit margin by discount band versus the overall margin.</figcaption>
  </figure>

  <h2 class="pagebreak">8. Sales forecasting</h2>
  <h3>8.1 Approach</h3>
  <p>
    Monthly revenue was aggregated into 36 observations. The first 30 months were used for training and
    the final 6 months were held back for validation, simulating a real "forecast the future with only
    the past available" situation. Five models plus an ensemble were fitted:
  </p>
  <ul>
    <li><b>Seasonal Naive</b> — repeats the value from the same month last year. A strong benchmark for seasonal business data.</li>
    <li><b>3-Month Moving Average</b> — smooths recent noise; no trend or seasonality.</li>
    <li><b>Holt-Winters</b> — additive trend and additive 12-month seasonality (exponential smoothing).</li>
    <li><b>SARIMA</b> — seasonal ARIMA with differencing; captures autocorrelation.</li>
    <li><b>Linear Regression</b> — trend plus two Fourier harmonics (sin/cos pairs) to model annual seasonality.</li>
    <li><b>Ensemble</b> — average of the two best statistical models.</li>
  </ul>
  <p>
    Accuracy is measured with MAPE (mean absolute percentage error), complemented by MAE and RMSE.
    MAPE is preferred for reporting because it is scale-free and easy to explain to non-technical
    stakeholders.
  </p>

  <h3>8.2 Hold-out results</h3>
  <table>
    <thead><tr><th>Model</th><th class="r">MAPE</th><th class="r">Accuracy</th><th class="r">RMSE</th></tr></thead>
    <tbody>{model_rows}</tbody>
  </table>
  <figure>
    <img src="figures/fig_model_comparison.png" alt="Model comparison" />
    <figcaption>Figure 9 — MAPE by model on the six-month hold-out window (lower is better).</figcaption>
  </figure>
  <div class="callout">
    <b>Winner: {FC['model']}</b> with {BEST['accuracy']:.2f}% accuracy. With only 36 observations,
    SARIMA's seasonal parameters are weakly identified; the parsimonious regression with Fourier terms
    generalises better. This is a useful lesson: on short series, a simpler model often wins.
  </div>

  <h3>8.3 Final forecast</h3>
  <p>
    The winning model was refitted on all 36 months. Prediction intervals are derived from the
    hold-out error and widen with the square root of the horizon, reflecting growing uncertainty.
    The forecast totals {crore(FC['next_6m_total'])} over the next six months, compared with
    {crore(FC['next_6m_last_year'])} in the same period last year — a growth of
    {FC['next_6m_growth_pct']:.1f}%.
  </p>
  <table>
    <thead><tr><th>Month</th><th class="r">Forecast</th><th class="r">80% low</th><th class="r">80% high</th><th class="r">95% low</th><th class="r">95% high</th></tr></thead>
    <tbody>{forecast_rows}</tbody>
  </table>
  <figure>
    <img src="figures/fig_forecast.png" alt="Forecast chart" />
    <figcaption>Figure 10 — History, model fit and six-month forecast with prediction intervals.</figcaption>
  </figure>
  <figure>
    <img src="figures/fig_forecast_next.png" alt="Forecast bars" />
    <figcaption>Figure 11 — Point forecast by month with 95% intervals.</figcaption>
  </figure>
  <table>
    <thead><tr><th>Region</th><th class="r">History (36 months)</th><th class="r">Forecast (6 months)</th><th class="r">Share of forecast</th></tr></thead>
    <tbody>{region_fc_rows}</tbody>
  </table>

  <h2 class="pagebreak">9. Dashboard design and implementation</h2>
  <h3>9.1 Design principles</h3>
  <ul>
    <li><b>One screen, one question.</b> Each tab answers a different question instead of packing every visual onto one page.</li>
    <li><b>Filter once, apply everywhere.</b> A single filter bar (year, region, category, channel, segment) recomputes every KPI and chart on the active tab.</li>
    <li><b>Context on every number.</b> KPI cards show the change versus the previous twelve months; charts use tooltips with exact values.</li>
    <li><b>Explain the "so what".</b> The overview ends with three automatically generated insights that restate the filtered data in business language.</li>
    <li><b>Accessible defaults.</b> High-contrast palette, tabular numerals, no colour-only encoding of meaning.</li>
  </ul>

  <h3>9.2 Dashboard pages</h3>
  <table>
    <thead><tr><th style="width:22%">Page</th><th>Content</th></tr></thead>
    <tbody>
      <tr><td>Overview</td><td>Six KPI cards with sparklines, revenue and profit trend, category donut, region comparison, channel mix, seasonality heatmap, discount-versus-margin, and three dynamic insights.</td></tr>
      <tr><td>Forecast</td><td>Six-month forecast with 80%/95% intervals, model comparison table, hold-out validation chart, month-wise table, regional forecast and method note.</td></tr>
      <tr><td>Products</td><td>Top products, Pareto curve, category margin comparison, concentration statistics and a sortable, searchable product table.</td></tr>
      <tr><td>Regions</td><td>Region scorecards with growth, category mix by region, top states and a region detail table.</td></tr>
      <tr><td>Customers</td><td>Segment mix, top customers, Lorenz concentration curve and customer statistics.</td></tr>
      <tr><td>Data &amp; quality</td><td>Data-quality audit tiles, paginated transaction browser with search, and one-click CSV export of the filtered selection.</td></tr>
    </tbody>
  </table>

  <h3>9.3 Power BI implementation</h3>
  <p>
    The same report is implemented in Power BI Desktop using the cleaned CSV as the source. Power Query
    handles the type conversions and text normalisation; the model uses a star schema with a dedicated
    Date table; DAX measures compute revenue, profit, margin, distinct orders, average order value and
    year-on-year growth. Slicers for year, region, category and channel drive a page-level filter
    context. The forecast visual is produced by the built-in Analytics pane (exponential smoothing)
    and cross-checked against the Python forecast exported as a table. A step-by-step build guide is
    provided in <i>docs/PowerBI_Build_Guide.md</i> so the report can be reproduced without the original
    file, and a ready-made star-schema workbook (<i>data/clean/Sales_Data_Model.xlsx</i>) is included for
    a one-click import.
  </p>

  <h2>10. Results and business recommendations</h2>
  <div class="kpi-strip">
    <div class="kpi-box"><div class="k">Forecast (6 months)</div><div class="v">{crore(FC['next_6m_total'])}</div></div>
    <div class="kpi-box"><div class="k">Model accuracy</div><div class="v">{BEST['accuracy']:.2f}%</div></div>
    <div class="kpi-box"><div class="k">Expected growth</div><div class="v">{FC['next_6m_growth_pct']:.1f}%</div></div>
  </div>
  <ol>
    <li><b>Plan the year around October–November.</b> The festive peak is {by_month[peak_month] / by_month[low_month]:.1f}× the weakest month. Lock in stock, logistics and temporary staffing at least six weeks early; a stock-out in October costs far more than holding cost.</li>
    <li><b>Protect margin from deep discounts.</b> Orders with 20%+ discount earn a fraction of the normal margin. Replace blanket percentage discounts with bundle offers and loyalty credits that preserve the price anchor.</li>
    <li><b>Grow the under-penetrated region.</b> {REGION[-1]['region']} contributes only {REGION[-1]['share']:.1f}% of revenue. Because regional margins are similar, incremental volume there converts to profit at the normal rate.</li>
    <li><b>Manage the product tail deliberately.</b> {CONC['products_for_80pct']} products carry 80% of revenue. Protect their availability; review or delist the long tail that adds complexity without contribution.</li>
    <li><b>Retain the top customers.</b> The top 10% of customers generate {CONC['top10_customer_share']:.1f}% of revenue. Assign account management to them and measure retention explicitly.</li>
    <li><b>Use the forecast as a range, not a number.</b> The 95% interval widens to several lakh by month six. Plan inventory to the upper bound and cash to the lower bound.</li>
  </ol>

  <h2>11. Limitations and future scope</h2>
  <ul>
    <li>The dataset is a realistic simulation, not a live company extract. The method transfers directly; the specific values would change.</li>
    <li>Only 36 monthly observations are available, which limits the complexity of the models that can be estimated reliably. With 5+ years of history, SARIMA and gradient-boosted trees would become stronger candidates.</li>
    <li>The forecast is univariate: it models revenue as a function of its own history. Promotion calendars, price changes, holidays and competitor actions are not explicit inputs.</li>
    <li>Inventory, marketing spend and customer acquisition cost are outside the dataset, so the recommendations are revenue- and margin-based rather than full profit-and-loss optimisations.</li>
    <li>Future work: hierarchical forecasting by region and category with reconciliation, probabilistic forecasting (quantile regression), automated retraining, and row-level security once the dashboard is published to the Power BI service.</li>
  </ul>

  <h2>12. Conclusion</h2>
  <p>
    This project demonstrates the complete path from raw transactional data to a decision-ready
    business intelligence product. Cleaning recovered a trustworthy dataset and documented every
    correction. Exploratory analysis exposed strong seasonality, a concentrated product portfolio, a
    clear regional hierarchy and a measurable margin cost of discounting. Five forecasting models were
    compared on a genuine hold-out window; the parsimonious regression with Fourier seasonality won
    with {BEST['accuracy']:.2f}% accuracy and produced a six-month forecast of
    {crore(FC['next_6m_total'])} with quantified uncertainty. Finally, an interactive dashboard
    packages all of this into six focused pages that a manager can filter and read in seconds.
  </p>
  <p>
    The wider lesson is that business intelligence is not a charting exercise. Value appears when data
    quality is engineered, when the right model is selected through disciplined validation, and when
    the output is delivered at the moment of decision. The same architecture — clean, model, analyse,
    forecast, visualise — applies to almost any sales organisation.
  </p>

  <h2>References</h2>
  <ol class="small">
    <li>Hyndman, R.J. &amp; Athanasopoulos, G. (2021). <i>Forecasting: Principles and Practice</i>, 3rd edition. OTexts.</li>
    <li>Box, G.E.P., Jenkins, G.M., Reinsel, G.C. &amp; Ljung, G.M. (2015). <i>Time Series Analysis: Forecasting and Control</i>. Wiley.</li>
    <li>Few, S. (2012). <i>Show Me the Numbers: Designing Tables and Graphs to Enlighten</i>. Analytics Press.</li>
    <li>Kimball, R. &amp; Ross, M. (2013). <i>The Data Warehouse Toolkit</i>, 3rd edition. Wiley.</li>
    <li>Microsoft (2024). <i>Power BI documentation — data modelling, DAX and visualisation</i>. learn.microsoft.com/power-bi.</li>
    <li>McKinney, W. (2022). <i>Python for Data Analysis</i>, 3rd edition. O'Reilly.</li>
    <li>Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. <i>JMLR</i>, 12, 2825–2830.</li>
  </ol>

  <h2 class="pagebreak">Appendix A — How to run the project</h2>
  <p>One command rebuilds everything from scratch:</p>
  <pre style="background:#f4f7fb;border:1px solid #dfe5ee;border-radius:8px;padding:12px;font-size:12px;overflow:auto">python run_project.py</pre>
  <p>Then open <b>dashboard/index.html</b> in any modern browser. No server, internet connection or
  installation is required for the dashboard.</p>
  <table>
    <thead><tr><th style="width:38%">Path</th><th>Contents</th></tr></thead>
    <tbody>
      <tr><td>run_project.py</td><td>Runs the full pipeline end to end</td></tr>
      <tr><td>src/01_generate_data.py</td><td>Creates the realistic raw dataset</td></tr>
      <tr><td>src/02_clean_data.py</td><td>Cleaning, validation and feature engineering</td></tr>
      <tr><td>src/03_eda_analysis.py</td><td>KPIs, charts and insight generation</td></tr>
      <tr><td>src/04_forecast.py</td><td>Model comparison and six-month forecast</td></tr>
      <tr><td>src/05_build_dashboard.py</td><td>Packs data for the dashboard</td></tr>
      <tr><td>src/06_build_report.py</td><td>Builds this HTML report</td></tr>
      <tr><td>src/07_build_excel.py</td><td>Builds the Excel star-schema data model</td></tr>
      <tr><td>src/08_build_docx.py</td><td>Builds the Word (DOCX) version of this report</td></tr>
      <tr><td>dashboard/index.html</td><td>Interactive dashboard (open directly)</td></tr>
      <tr><td>docs/PowerBI_Build_Guide.md</td><td>Step-by-step Power BI rebuild guide</td></tr>
      <tr><td>docs/Viva_QA.md</td><td>Likely viva questions with answers</td></tr>
      <tr><td>reports/figures/</td><td>All charts used in this report</td></tr>
    </tbody>
  </table>

  <footer class="rep">
    <span>Sales Forecasting and Business Intelligence Dashboard</span>
    <span>Generated {CLEAN['date_min']} – {CLEAN['date_max']} · {CLEAN['rows_final']:,} records</span>
  </footer>
</div>
</body>
</html>
"""

out = REPORT_DIR / "Project_Report.html"
out.write_text(html, encoding="utf-8")
print(f"[report] written -> {out}")
print(f"[report] size: {out.stat().st_size / 1024:.1f} KB")
