"""
analysis.py - all financial maths is done HERE in plain Python, never by the AI.
(AI is good at reading text, but can make arithmetic mistakes.)
"""
import pandas as pd
from schema import CreditReport


def _ratio(a, b):
    """a / b, or None if a number is missing or b is zero."""
    if a is None or b in (None, 0):
        return None
    return a / b


def compute_metrics(report: CreditReport) -> pd.DataFrame:
    rows = []
    previous_revenue = None
    for y in report.financials:
        growth = None
        if previous_revenue not in (None, 0) and y.revenue is not None:
            growth = (y.revenue - previous_revenue) / previous_revenue * 100
        margin = _ratio(y.ebitda, y.revenue)
        net_margin = _ratio(y.net_profit, y.revenue)
        rows.append({
            "Year": y.year,
            "Revenue": y.revenue,
            "EBITDA": y.ebitda,
            "Net Profit": y.net_profit,
            "Total Debt": y.total_debt,
            "Net Worth": y.net_worth,
            "Revenue Growth %": growth,
            "EBITDA Margin %": None if margin is None else margin * 100,
            "Net Margin %": None if net_margin is None else net_margin * 100,
            "Debt / Equity (x)": _ratio(y.total_debt, y.net_worth),
            "Interest Cover (x)": _ratio(y.ebitda, y.interest_expense),
        })
        previous_revenue = y.revenue
    return pd.DataFrame(rows)


def health_flags(metrics: pd.DataFrame) -> list[str]:
    """Simple rule-based warnings looking at the latest year."""
    if metrics.empty:
        return []
    latest = metrics.iloc[-1]
    flags = []
    de, icr, margin = latest["Debt / Equity (x)"], latest["Interest Cover (x)"], latest["EBITDA Margin %"]
    if pd.notna(de) and de > 2:
        flags.append(f"High leverage: debt/equity is {de:.1f}x (above 2x)")
    if pd.notna(icr) and icr < 2:
        flags.append(f"Weak interest cover: {icr:.1f}x (below 2x)")
    if pd.notna(margin) and margin < 10:
        flags.append(f"Thin operating margin: {margin:.1f}% (below 10%)")
    if pd.notna(latest["Revenue Growth %"]) and latest["Revenue Growth %"] < 0:
        flags.append(f"Revenue fell {abs(latest['Revenue Growth %']):.1f}% in the latest year")
    return flags
