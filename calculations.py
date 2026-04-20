"""
All formulas and formatting helpers.
Computed fields are NEVER stored — calculated at render time here.
All divide-by-zero cases return None, displayed as 'N/A'.
"""


def safe_div(numerator, denominator):
    """Safe division; returns None on zero/missing denominator."""
    if denominator is None or denominator == 0:
        return None
    if numerator is None:
        return None
    return numerator / denominator


# ─────────────────────── Metric Calculations ───────────────────────


def calc_labor_pct(labor_dollars, revenue):
    """Labor % = (labor_dollars / revenue) * 100"""
    val = safe_div(labor_dollars, revenue)
    return val * 100 if val is not None else None


def calc_splh(revenue, labor_hours):
    """Sales Per Labor Hour = revenue / labor_hours"""
    return safe_div(revenue, labor_hours)


def calc_cos_pct(cos_dollars, total_revenue):
    """Cost of Sales % = (cos_dollars / total_revenue) * 100"""
    val = safe_div(cos_dollars, total_revenue)
    return val * 100 if val is not None else None


def calc_cpm(cos_dollars, meals_served):
    """Cost Per Meal = cos_dollars / meals_served (Residential only)"""
    return safe_div(cos_dollars, meals_served)


def calc_mplh(meals_served, labor_hours):
    """Meals Per Labor Hour = meals_served / labor_hours (Residential only)"""
    return safe_div(meals_served, labor_hours)


def calc_food_cost(invoice_total, inv_start, inv_end, adjustments=0):
    """Food Cost = invoice_total + inventory_start - inventory_end + adjustments"""
    vals = [invoice_total, inv_start, inv_end]
    if any(v is None for v in vals):
        return None
    return invoice_total + inv_start - inv_end + (adjustments or 0)


def sum_revenue_streams(board, retail, flex, catering, other):
    """Sum all revenue streams. Treats None as 0."""
    return (board or 0) + (retail or 0) + (flex or 0) + (catering or 0) + (other or 0)


# ─────────────────────── Variance Calculations ───────────────────────


def variance(current, prior):
    """Returns (difference, percent_change) tuple. Both None if inputs are None."""
    if current is None or prior is None:
        return None, None
    diff = current - prior
    pct = safe_div(diff, prior)
    pct_val = pct * 100 if pct is not None else None
    return diff, pct_val


def variance_row(budget, projection, actual):
    """
    Returns a dict with variance calculations for a single Flash Report line.
    Used for building the Flash Report table rows.
    """
    var_budget = (actual - budget) if actual is not None and budget is not None else None
    var_projection = (actual - projection) if actual is not None and projection is not None else None
    return {
        "budget": budget,
        "projection": projection,
        "actual": actual,
        "var_budget": var_budget,
        "var_projection": var_projection,
    }


# ─────────────────────── Formatting Helpers ───────────────────────


def fmt_pct(val):
    """Format as percentage string, e.g. '28.5%'. Returns 'N/A' if None."""
    if val is None:
        return "N/A"
    return "{:.1f}%".format(val)


def fmt_dollar(val):
    """Format as dollar string, e.g. '$1,234.56'. Returns 'N/A' if None."""
    if val is None:
        return "N/A"
    return "${:,.2f}".format(val)


def fmt_number(val, decimals=1):
    """Format as number with commas. Returns 'N/A' if None."""
    if val is None:
        return "N/A"
    fmt_str = "{{:,.{0}f}}".format(decimals)
    return fmt_str.format(val)


def fmt_value(val, fmt_type="dollar"):
    """Format a value based on its type (dollar, pct, number)."""
    if fmt_type == "dollar":
        return fmt_dollar(val)
    elif fmt_type == "pct":
        return fmt_pct(val)
    else:
        return fmt_number(val)


# ─── Clean formatting (no unnecessary decimals) ───


def fmt_dollar_clean(val):
    """$81,877.00 -> $81,877  |  $1,234.56 -> $1,235  |  None -> N/A"""
    if val is None:
        return "N/A"
    rounded = round(val)
    if rounded < 0:
        return "-${:,}".format(abs(rounded))
    return "${:,}".format(rounded)


def fmt_pct_clean(val):
    """36.30% -> 36.3%  |  36.00% -> 36.0%  |  None -> N/A"""
    if val is None:
        return "N/A"
    return "{:.1f}%".format(val)


def fmt_number_clean(val):
    """1,042.0 -> 1,042  |  3.5 -> 3.5  |  None -> N/A"""
    if val is None:
        return "N/A"
    if val == int(val):
        return "{:,}".format(int(val))
    return "{:,.1f}".format(val)


def fmt_clean(val, fmt_type="dollar"):
    """Clean formatter — no unnecessary decimals."""
    if fmt_type == "dollar":
        return fmt_dollar_clean(val)
    elif fmt_type == "pct":
        return fmt_pct_clean(val)
    else:
        return fmt_number_clean(val)
