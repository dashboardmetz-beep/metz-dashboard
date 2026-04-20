"""
Professional theme and styling for Campus Dining Operations Platform.
Locked design system — do not modify tokens or spacing without approval.
"""

import streamlit as st


# ─── Design Tokens (LOCKED) ───
BRAND = {
    # Primary palette
    "primary": "#1F2A44",
    "secondary": "#2E3A59",
    "accent": "#C7A462",
    # Surfaces
    "background": "#F7F8FA",
    "card": "#FFFFFF",
    "border": "#E5E7EB",
    # Text hierarchy
    "text_primary": "#1E293B",
    "text_secondary": "#64748B",
    "text_muted": "#94A3B8",
    # Semantic
    "success": "#16A34A",
    "warning": "#D97706",
    "danger": "#DC2626",
    # Sidebar
    "sidebar_start": "#1F2A44",
    "sidebar_end": "#2E3A59",
}


def inject_css():
    """Inject the full custom CSS theme into the Streamlit app."""
    st.markdown(
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">',
        unsafe_allow_html=True,
    )
    st.markdown(_THEME_CSS, unsafe_allow_html=True)


_THEME_CSS = """<style>
/* -- GLOBAL OVERRIDES -- */

.stApp {
    background-color: #F7F8FA;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: #1E293B;
    font-size: 14px;
}

.block-container {
    padding-top: 1.5rem !important;
    max-width: 1400px;
}

/* -- SIDEBAR -- */

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1B2540 0%, #1F2D4A 100%);
    border-right: none;
    min-width: 260px !important;
    width: 260px !important;
    padding-top: 0 !important;
}

section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
}

/* Hide default sidebar close/collapse button */
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
    display: none !important;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    color: #FFFFFF !important;
}

section[data-testid="stSidebar"] .stSelectbox label {
    color: rgba(255,255,255,0.5) !important;
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.06);
}

/* -- Sidebar nav buttons -- */
section[data-testid="stSidebar"] .stButton {
    margin: 0 !important;
    padding: 0 !important;
}
section[data-testid="stSidebar"] .stButton button {
    background: none !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 9px 20px !important;
    margin: 1px 8px !important;
    width: calc(100% - 16px) !important;
    text-align: left !important;
    justify-content: flex-start !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: rgba(255,255,255,0.55) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.55) !important;
    cursor: pointer !important;
    transition: background 0.12s ease !important;
    min-height: 0 !important;
    line-height: 1.4 !important;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(255,255,255,0.05) !important;
    color: rgba(255,255,255,0.85) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.85) !important;
}
section[data-testid="stSidebar"] .stButton button:focus {
    box-shadow: none !important;
    outline: none !important;
}

/* -- Sidebar radio subsections -- */
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] {
    gap: 0 !important;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {
    background: transparent !important;
    border: none !important;
    border-radius: 0 6px 6px 0 !important;
    padding: 7px 14px 7px 44px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: background 0.12s ease !important;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover {
    background: rgba(255,255,255,0.04) !important;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"],
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:has(input:checked) {
    background: rgba(79,125,243,0.12) !important;
    border-left: 2px solid #4F7DF3 !important;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label p {
    color: rgba(255,255,255,0.40) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.40) !important;
    font-size: 12.5px !important;
    font-weight: 400 !important;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] p,
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:has(input:checked) p {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 600 !important;
}
/* Hide radio circles */
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}

section[data-testid="stSidebar"] .stButton button p {
    color: inherit !important;
    -webkit-text-fill-color: inherit !important;
    font-size: inherit !important;
    font-weight: inherit !important;
    margin: 0 !important;
    text-align: left !important;
    width: 100% !important;
}
/* Force flexbox left-align on button internals */
section[data-testid="stSidebar"] .stButton button div {
    justify-content: flex-start !important;
    text-align: left !important;
}

/* -- PAGE HEADER -- */

.page-header {
    background: #FFFFFF;
    padding: 22px 24px;
    border-radius: 12px;
    margin-bottom: 24px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
    border-bottom: 2px solid #1F2A44;
    border-left: none;
    border-right: none;
    border-top: none;
}

.page-header * {
    text-decoration: none !important;
    -webkit-text-decoration: none !important;
    font-style: normal !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* -- STANDARDIZED CARDS -- */

.section-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    border: 1px solid #E5E7EB;
    transition: box-shadow 0.2s ease;
}
.section-card:hover {
    box-shadow: 0 8px 24px rgba(0,0,0,0.06);
}

.section-card h3 {
    color: #1E293B !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    border-bottom: 2px solid #C7A462;
    padding-bottom: 12px;
    margin-bottom: 16px !important;
}
.section-card .stPlotlyChart {
    margin-top: 4px !important;
    margin-bottom: 0 !important;
}

.section-card-accent {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    border: 1px solid #E5E7EB;
    border-left: 3px solid #C7A462;
}

/* -- KPI METRIC CARDS -- */

.kpi-container {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 16px;
}

.kpi-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 22px;
    flex: 1;
    min-width: 150px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    border: 1px solid #E5E7EB;
    text-align: center;
    transition: transform 0.15s, box-shadow 0.15s;
}

.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

.kpi-card .kpi-label {
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #94A3B8;
    margin-bottom: 8px;
}

.kpi-card .kpi-value {
    font-size: 32px;
    font-weight: 700;
    color: #1E293B;
    white-space: nowrap;
    line-height: 1.2;
}

/* KPI accent colors handled via inline styles */

/* -- STATUS BADGE -- */

.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.02em;
}

.status-draft {
    background: #EFF6FF;
    color: #1D4ED8;
}

.status-submitted {
    background: #FEF3C7;
    color: #D97706;
}

.status-returned {
    background: #FEF2F2;
    color: #DC2626;
}

.status-approved {
    background: #F0FDF4;
    color: #16A34A;
}

/* -- NAVIGATION DATE BAR -- */

.date-nav {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    border: 1px solid #E5E7EB;
}

/* -- BUTTONS -- */

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1F2A44 0%, #2E3A59 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: 0.02em;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 14px rgba(31, 42, 68, 0.25);
    color: #FFFFFF !important;
    height: 48px;
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #2E3A59 0%, #3D4E73 100%) !important;
    box-shadow: 0 6px 20px rgba(31, 42, 68, 0.35);
    transform: translateY(-2px);
}

.stButton > button:not([kind="primary"]) {
    background: linear-gradient(135deg, #1F2A44 0%, #2E3A59 100%) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    font-family: 'Inter', sans-serif !important;
    border: none !important;
    color: #FFFFFF !important;
    transition: all 0.25s ease !important;
    height: 48px;
    box-shadow: 0 4px 14px rgba(31, 42, 68, 0.25);
    letter-spacing: 0.02em;
}

.stButton > button:not([kind="primary"]):hover {
    background: linear-gradient(135deg, #2E3A59 0%, #3D4E73 100%) !important;
    color: #FFFFFF !important;
    box-shadow: 0 6px 20px rgba(31, 42, 68, 0.35);
    transform: translateY(-2px);
}

/* -- METRICS -- */

div[data-testid="stMetric"] {
    background: #FFFFFF;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border: 1px solid #E5E7EB;
    transition: all 0.25s ease;
    text-align: center;
}

div[data-testid="stMetric"]:hover {
    box-shadow: 0 6px 20px rgba(0,0,0,0.1);
    transform: translateY(-2px);
}

div[data-testid="stMetric"] label {
    color: #94A3B8 !important;
    font-weight: 600 !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #1E293B !important;
    font-weight: 700 !important;
    font-size: 26px !important;
}

/* -- TABS -- */

.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: #F7F8FA;
    padding: 6px;
    border-radius: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border: 1px solid #E5E7EB;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    font-weight: 600;
    padding: 10px 20px;
    color: #64748B;
    font-size: 13px;
    letter-spacing: 0.02em;
    transition: all 0.2s ease;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1F2A44 0%, #2E3A59 100%) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(31, 42, 68, 0.25);
    border-radius: 8px;
}

/* -- DATAFRAMES TABLES -- */

div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    border: 1px solid #E5E7EB;
}

/* -- EXPANDERS -- */

.streamlit-expanderHeader {
    background: #F7F8FA;
    border-radius: 8px;
    font-weight: 600;
    color: #1E293B;
}

div[data-testid="stExpander"] {
    background: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E5E7EB;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
}

/* -- INPUTS -- */

/* Hide +/- stepper buttons on number inputs */
.stNumberInput [data-testid="stNumberInputStepUp"],
.stNumberInput [data-testid="stNumberInputStepDown"],
.stNumberInput button {
    display: none !important;
}

.stNumberInput input {
    border-radius: 10px !important;
    border: 1.5px solid #E5E7EB !important;
    height: 56px;
    font-family: 'Inter', sans-serif !important;
    font-size: 22px !important;
    font-weight: 700 !important;
    color: #1E293B !important;
    background: #FAFBFC !important;
    padding: 10px 16px !important;
    transition: all 0.2s ease !important;
}

.stTextInput input,
.stTextArea textarea {
    border-radius: 10px !important;
    border: 1.5px solid #E5E7EB !important;
    height: 48px;
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #1E293B !important;
    background: #FAFBFC !important;
    padding: 8px 14px !important;
    transition: all 0.2s ease !important;
}

.stNumberInput input:focus,
.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: #1F2A44 !important;
    box-shadow: 0 0 0 3px rgba(31, 42, 68, 0.1) !important;
    background: #FFFFFF !important;
}

.stNumberInput label,
.stTextInput label,
.stTextArea label,
.stSelectbox label {
    font-weight: 600 !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    color: #64748B !important;
    font-family: 'Inter', sans-serif !important;
}

.stSelectbox > div > div {
    border-radius: 8px !important;
    border-color: #D1D5DB !important;
}

.stNumberInput,
.stTextInput,
.stTextArea,
.stSelectbox,
.stDateInput {
    margin-bottom: 16px !important;
}

/* -- ALERTS -- */

div[data-testid="stAlert"] {
    border-radius: 12px;
}

/* -- DIVIDERS -- */

hr {
    border-color: #E5E7EB !important;
    margin: 24px 0 !important;
}

/* -- WEATHER CARD -- */

.weather-card {
    background: #FFFFFF;
    color: #1E293B;
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 16px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
    border: 1px solid #E5E7EB;
}

.weather-card h4 {
    color: #1E293B !important;
    margin-bottom: 8px !important;
}

/* -- FLASH REPORT TABLE -- */

.flash-panel {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 22px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    border: 1px solid #E5E7EB;
}

.flash-panel h4 {
    color: #1E293B !important;
    font-weight: 700 !important;
    border-bottom: 1px solid #E5E7EB;
    padding-bottom: 12px;
}

/* -- FOOTER -- */

.app-footer {
    text-align: center;
    color: #94A3B8;
    font-size: 12px;
    font-weight: 400;
    font-family: 'Inter', sans-serif;
    padding: 40px 0 16px 0;
    border-top: 1px solid #E5E7EB;
    margin-top: 48px;
}

/* ======== DASHBOARD-SPECIFIC STYLES ======== */

/* -- Dashboard KPI Card (top row, screenshot style) -- */
.dash-kpi {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 20px 22px;
    border: 1px solid #E5E7EB;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    position: relative;
    overflow: hidden;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
    min-height: 130px;
}
.dash-kpi:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 28px rgba(0,0,0,0.09);
}
.dash-kpi::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
}
.dash-kpi.accent-blue::before { background: #3B82F6; }
.dash-kpi.accent-red::before { background: #EF4444; }
.dash-kpi.accent-amber::before { background: #F59E0B; }
.dash-kpi.accent-green::before { background: #16A34A; }
.dash-kpi.accent-purple::before { background: #8B5CF6; }
.dash-kpi.accent-teal::before { background: #14B8A6; }

.dash-kpi-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #94A3B8;
    margin-bottom: 10px;
    font-family: 'Inter', sans-serif;
}
.dash-kpi-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
}
.dash-kpi-value {
    font-size: 30px;
    font-weight: 700;
    color: #1E293B;
    line-height: 1.1;
    font-family: 'Inter', sans-serif;
}
.dash-kpi-change {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    font-size: 12px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 20px;
    margin-top: 8px;
}
.dash-kpi-change.up {
    color: #16A34A;
    background: #F0FDF4;
}
.dash-kpi-change.down {
    color: #EF4444;
    background: #FEF2F2;
}
.dash-kpi-change.neutral {
    color: #64748B;
    background: #F1F5F9;
}
.dash-kpi-badge {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 700;
    font-family: 'Inter', sans-serif;
    flex-shrink: 0;
}

/* -- Dashboard Metric Cards (bottom compact row) -- */
.dash-metric {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 18px 20px;
    border: 1px solid #E5E7EB;
    box-shadow: 0 2px 10px rgba(0,0,0,0.04);
    transition: transform 0.15s ease;
}
.dash-metric:hover {
    transform: translateY(-2px);
}
.dash-metric-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94A3B8;
    margin-bottom: 6px;
    font-family: 'Inter', sans-serif;
}
.dash-metric-row {
    display: flex;
    align-items: baseline;
    gap: 10px;
}
.dash-metric-value {
    font-size: 24px;
    font-weight: 700;
    line-height: 1.2;
    font-family: 'Inter', sans-serif;
}
.dash-metric-change {
    font-size: 12px;
    font-weight: 600;
}

/* -- Dashboard Section Header -- */
.dash-section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 32px 0 16px 0;
}
.dash-section-title {
    font-size: 18px;
    font-weight: 700;
    color: #1E293B;
    font-family: 'Inter', sans-serif;
}
.dash-section-subtitle {
    font-size: 12px;
    font-weight: 500;
    color: #94A3B8;
    letter-spacing: 0.02em;
}

/* -- Dashboard Chart Card (enhanced) -- */
.dash-chart-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 22px;
    border: 1px solid #E5E7EB;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    margin-bottom: 16px;
    transition: box-shadow 0.2s ease;
}
.dash-chart-card:hover {
    box-shadow: 0 6px 24px rgba(0,0,0,0.08);
}
.dash-chart-title {
    font-size: 15px;
    font-weight: 700;
    color: #1E293B;
    font-family: 'Inter', sans-serif;
    margin-bottom: 4px;
}
.dash-chart-subtitle {
    font-size: 12px;
    color: #94A3B8;
    font-weight: 400;
    margin-bottom: 12px;
}

/* -- Progress Bar (Target Section) -- */
.dash-progress-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 18px 20px;
    border: 1px solid #E5E7EB;
    box-shadow: 0 2px 10px rgba(0,0,0,0.04);
}
.dash-progress-label {
    font-size: 12px;
    font-weight: 500;
    color: #64748B;
    margin-bottom: 8px;
    font-family: 'Inter', sans-serif;
}
.dash-progress-value {
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 8px;
    font-family: 'Inter', sans-serif;
}
.dash-progress-bar-bg {
    width: 100%;
    height: 6px;
    background: #F1F5F9;
    border-radius: 3px;
    overflow: hidden;
}
.dash-progress-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.6s ease;
}

/* -- Department Status Row -- */
.dash-dept-status {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 16px 20px;
    border: 1px solid #E5E7EB;
    box-shadow: 0 2px 10px rgba(0,0,0,0.04);
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
    transition: all 0.15s ease;
}
.dash-dept-status:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}
.dash-dept-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 10px;
    flex-shrink: 0;
}
.dash-dept-name {
    font-size: 14px;
    font-weight: 600;
    color: #1E293B;
    font-family: 'Inter', sans-serif;
}
.dash-status-pill {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.02em;
}
.pill-draft { background: #F1F5F9; color: #64748B; }
.pill-submitted { background: #EFF6FF; color: #3B82F6; }
.pill-returned { background: #FEF3C7; color: #D97706; }
.pill-approved { background: #F0FDF4; color: #16A34A; }

/* -- Comments Card -- */
.dash-comment-item {
    padding: 10px 0;
    border-bottom: 1px solid #F1F5F9;
    font-size: 13px;
    color: #475569;
    font-family: 'Inter', sans-serif;
}
.dash-comment-item:last-child {
    border-bottom: none;
}
.dash-comment-dept {
    font-weight: 700;
    color: #1E293B;
    font-size: 13px;
    margin-bottom: 4px;
}

/* ─── Premium Budget Cards ─── */

.budget-summary-card {
    background: linear-gradient(135deg, #1F2A44 0%, #2E3A59 100%);
    border-radius: 14px;
    padding: 28px 24px;
    margin: 20px 0;
    text-align: center;
    box-shadow: 0 4px 20px rgba(31,42,68,0.18);
}
.budget-summary-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: rgba(255,255,255,0.55);
    margin-bottom: 8px;
    font-family: 'Inter', sans-serif;
}
.budget-summary-value {
    font-size: 38px;
    font-weight: 700;
    color: #FFFFFF;
    line-height: 1.2;
    font-family: 'Inter', sans-serif;
}

.budget-kpi-row {
    display: flex;
    gap: 16px;
    margin: 16px 0;
}
.budget-kpi-item {
    flex: 1;
    background: #FFFFFF;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #E5E7EB;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    text-align: center;
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.budget-kpi-item:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    transform: translateY(-1px);
}
.budget-kpi-item .kpi-accent {
    width: 32px;
    height: 3px;
    border-radius: 2px;
    margin: 0 auto 14px auto;
}
.budget-kpi-item .kpi-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #94A3B8;
    margin-bottom: 6px;
    font-family: 'Inter', sans-serif;
}
.budget-kpi-item .kpi-value {
    font-size: 26px;
    font-weight: 700;
    color: #1E293B;
    font-family: 'Inter', sans-serif;
}

/* Save button styling */
.budget-save-btn button {
    background: linear-gradient(135deg, #1F2A44 0%, #2E3A59 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    height: 48px !important;
    letter-spacing: 0.02em;
    box-shadow: 0 4px 14px rgba(31,42,68,0.25) !important;
    transition: all 0.2s ease !important;
}
.budget-save-btn button:hover {
    box-shadow: 0 6px 20px rgba(31,42,68,0.35) !important;
    transform: translateY(-2px) !important;
}

/* Draft/Submit buttons row */
.budget-action-row {
    display: flex;
    gap: 12px;
    margin-top: 24px;
}
</style>
"""


# ─── Component Helpers ───


def page_header(title, subtitle="", metadata_right=""):
    """Render a branded page header with optional right-aligned metadata."""
    sub_html = ""
    if subtitle:
        sub_html = (
            '<p style="color:#64748B;font-size:14px;font-weight:400;'
            'margin:4px 0 0 0;font-family:Inter,sans-serif;">{}</p>'
        ).format(subtitle)
    meta_html = ""
    if metadata_right:
        meta_html = (
            '<div style="text-align:right;color:#64748B;font-size:12px;'
            'font-weight:500;letter-spacing:0.04em;white-space:nowrap;">'
            '{}</div>'
        ).format(metadata_right)
    st.markdown(
        '<div class="page-header" style="display:flex;justify-content:space-between;'
        'align-items:center;">'
        '<div>'
        '<p style="color:#1E293B;font-size:28px;font-weight:700;'
        'font-family:Inter,sans-serif;margin:0;padding:0;line-height:1.3;'
        'text-decoration:none !important;font-style:normal;">{title}</p>'
        '{sub}'
        '</div>'
        '{meta}'
        '</div>'.format(title=title, sub=sub_html, meta=meta_html),
        unsafe_allow_html=True,
    )


def section_title(icon, title, anchor_id=""):
    """Render a styled section title with optional anchor for sidebar scroll-to."""
    aid = anchor_id or title.lower().replace(" ", "-").replace("/", "-")
    st.markdown(
        '<div id="{aid}" style="margin:40px 0 16px 0;scroll-margin-top:80px;">'
        '<span style="font-size:20px;font-weight:600;color:#1E293B;'
        'font-family:Inter,sans-serif;letter-spacing:-0.01em;">{title}</span>'
        '</div>'.format(aid=aid, title=title),
        unsafe_allow_html=True,
    )


def scroll_to_section(section_name):
    """Inject JS to scroll to a section anchor on the page."""
    aid = section_name.lower().replace(" ", "-").replace("/", "-")
    st.markdown(
        '<script>'
        'window.addEventListener("load", function() {{'
        '  var el = document.getElementById("{aid}");'
        '  if (el) {{ el.scrollIntoView({{behavior: "smooth", block: "start"}}); }}'
        '}});'
        '</script>'.format(aid=aid),
        unsafe_allow_html=True,
    )


def kpi_card(label, value, change="", color_class=""):
    """Render a KPI card with optional variance indicator and accent color.

    Args:
        label: Metric name (rendered uppercase)
        value: Main display value
        change: Optional variance text (e.g. "+5.2% vs LY"). Auto-colored green/red.
        color_class: Accent color class (kpi-green, kpi-blue, kpi-amber, kpi-red).
    """
    _ACCENT_MAP = {
        "kpi-green": "#16A34A",
        "kpi-blue": "#3B82F6",
        "kpi-amber": "#D97706",
        "kpi-red": "#DC2626",
    }
    accent = _ACCENT_MAP.get(color_class, "#C7A462")

    change_html = ""
    if change and str(change) not in ("kpi-green", "kpi-blue", "kpi-amber", "kpi-red"):
        change_str = str(change)
        change_color = "#1E293B"
        if change_str.startswith("+"):
            change_color = "#16A34A"
        elif change_str.startswith("-"):
            change_color = "#DC2626"
        change_html = (
            '<div style="font-size:13px;font-weight:500;color:{};margin-top:4px;">'
            '{}</div>'
        ).format(change_color, change_str)

    st.markdown(
        '<div style="background:#FFFFFF;border-radius:12px;padding:22px;'
        'border:1px solid #E5E7EB;box-shadow:0 4px 12px rgba(0,0,0,0.04);'
        'text-align:center;border-top:3px solid {accent};'
        'transition:box-shadow 0.2s ease;">'
        '<div style="font-size:12px;font-weight:500;text-transform:uppercase;'
        'letter-spacing:0.04em;color:#94A3B8;margin-bottom:8px;'
        'font-family:Inter,sans-serif;">{label}</div>'
        '<div style="font-size:32px;font-weight:700;color:#1E293B;'
        'white-space:nowrap;line-height:1.2;font-family:Inter,sans-serif;">'
        '{value}</div>'
        '{change}'
        '</div>'.format(accent=accent, label=label, value=value, change=change_html),
        unsafe_allow_html=True,
    )


def status_badge(status):
    """Render a colored status badge."""
    cls_map = {
        "Draft": "status-draft",
        "Submitted": "status-submitted",
        "Returned": "status-returned",
        "Approved": "status-approved",
    }
    cls = cls_map.get(status, "status-draft")
    return '<span class="status-badge {}">{}</span>'.format(cls, status)


def mini_divider():
    """Thin visual separator (24px spacing)."""
    st.markdown(
        '<div style="height:1px;background:#E5E7EB;margin:24px 0;"></div>',
        unsafe_allow_html=True,
    )


def chart_card_start(title=""):
    """Emit the opening HTML for a white card container with an optional title.

    Must be paired with chart_card_end(). Place Streamlit widgets between calls.
    """
    title_html = ""
    if title:
        title_html = "<h3>{}</h3>".format(title)
    st.markdown(
        '<div class="section-card">'
        '{}'.format(title_html),
        unsafe_allow_html=True,
    )


def chart_card_end():
    """Emit the closing tag for a chart_card_start() block."""
    st.markdown("</div>", unsafe_allow_html=True)


def empty_state(message, subtitle=""):
    """Render a muted empty-state placeholder for pages with no data."""
    sub_html = ""
    if subtitle:
        sub_html = (
            '<p style="color:#94A3B8;font-size:13px;margin:4px 0 0 0;">{}</p>'
        ).format(subtitle)
    st.markdown(
        '<div style="text-align:center;padding:48px 24px;color:#64748B;'
        'font-size:15px;font-weight:500;background:#F7F8FA;border-radius:12px;'
        'border:1px dashed #D1D5DB;font-family:Inter,sans-serif;">'
        '<p style="margin:0;">{}</p>'
        '{}'
        '</div>'.format(message, sub_html),
        unsafe_allow_html=True,
    )


def event_reminders(conn):
    """Show upcoming dining-impacting events as a banner at the top of any page."""
    from datetime import date, timedelta
    try:
        import db
        today = date.today()
        upcoming = db.fetch_upcoming_events(conn, today.isoformat(), days_ahead=7)
        dining_events = [e for e in upcoming if e.get("affects_dining")]
    except Exception:
        return

    if not dining_events:
        return

    items_html = ""
    for ev in dining_events:
        impact = ev.get("dining_impact", "")
        impact_html = " &mdash; <em>{}</em>".format(impact) if impact else ""
        items_html += (
            '<div style="padding:4px 0;border-bottom:1px solid #E5E7EB;">'
            '<strong>{date}</strong> &nbsp; {title}{impact}'
            '</div>'
        ).format(date=ev["event_date"], title=ev["title"], impact=impact_html)

    st.markdown(
        '<div style="background:#FFFFFF;color:#1E293B;'
        'padding:16px 20px;border-radius:12px;margin-bottom:16px;font-size:14px;'
        'border:1px solid #E5E7EB;box-shadow:0 4px 12px rgba(0,0,0,0.04);'
        'font-family:Inter,sans-serif;">'
        '<div style="font-weight:600;margin-bottom:8px;font-size:12px;'
        'text-transform:uppercase;letter-spacing:0.04em;color:#94A3B8;">'
        'Upcoming Dining Alerts (Next 7 Days)</div>'
        '{}</div>'.format(items_html),
        unsafe_allow_html=True,
    )

def app_footer():
    """Render app footer."""
    st.markdown(
        '<div class="app-footer">'
        'Campus Dining Operations Platform &middot; Metz Culinary Management'
        '</div>',
        unsafe_allow_html=True,
    )


# ─── Premium Budget Helpers ───


def budget_summary_metric(label, value):
    """Dark navy gradient hero card for totals (e.g. Total Revenue)."""
    st.markdown(
        '<div class="budget-summary-card">'
        '<div class="budget-summary-label">{label}</div>'
        '<div class="budget-summary-value">{value}</div>'
        '</div>'.format(label=label, value=value),
        unsafe_allow_html=True,
    )


_KPI_ACCENT_COLORS = {
    "blue": "#3B82F6",
    "amber": "#D97706",
    "red": "#EF4444",
    "green": "#16A34A",
    "purple": "#8B5CF6",
    "teal": "#0D9488",
    "navy": "#1F2A44",
}


def budget_kpi_row(items):
    """Render a row of premium KPI metric cards.

    Args:
        items: list of (label, value, accent) tuples.
               accent is a color key: blue, amber, red, green, purple, teal, navy.
    """
    cards_html = ""
    for label, value, accent in items:
        color = _KPI_ACCENT_COLORS.get(accent, accent)
        cards_html += (
            '<div class="budget-kpi-item">'
            '<div class="kpi-accent" style="background:{color};"></div>'
            '<div class="kpi-label">{label}</div>'
            '<div class="kpi-value">{value}</div>'
            '</div>'
        ).format(color=color, label=label, value=value)
    st.markdown(
        '<div class="budget-kpi-row">{}</div>'.format(cards_html),
        unsafe_allow_html=True,
    )


def budget_save_start():
    """Open a styled save-button wrapper. Pair with budget_save_end()."""
    st.markdown('<div class="budget-save-btn">', unsafe_allow_html=True)


def budget_save_end():
    """Close the styled save-button wrapper."""
    st.markdown('</div>', unsafe_allow_html=True)


# ─── Dashboard-specific Component Helpers ───


def dash_kpi_card(label, value, change="", accent="blue", badge_text="", badge_bg="#EFF6FF", badge_color="#3B82F6"):
    """Render a dashboard KPI card matching the minimal dashboard screenshot style.

    Args:
        label: Metric name (uppercase label)
        value: Main display value
        change: Variance text (e.g. "+5.2% vs LY"). Auto-colored green/red.
        accent: Color accent (blue, red, amber, green, purple, teal)
        badge_text: Optional text for circular badge on the right
        badge_bg: Badge background color
        badge_color: Badge text color
    """
    # Build change HTML
    change_html = ""
    if change:
        ch = str(change)
        if ch.startswith("+"):
            cls = "up"
            arrow = "&#9650;"
        elif ch.startswith("-"):
            cls = "down"
            arrow = "&#9660;"
        else:
            cls = "neutral"
            arrow = ""
        change_html = (
            '<div class="dash-kpi-change {cls}">'
            '{arrow} {text}</div>'
        ).format(cls=cls, arrow=arrow, text=ch)

    # Build badge HTML
    badge_html = ""
    if badge_text:
        badge_html = (
            '<div class="dash-kpi-badge" '
            'style="background:{bg};color:{color};">{text}</div>'
        ).format(bg=badge_bg, color=badge_color, text=badge_text)

    st.markdown(
        '<div class="dash-kpi accent-{accent}">'
        '<div class="dash-kpi-label">{label}</div>'
        '<div class="dash-kpi-row">'
        '<div>'
        '<div class="dash-kpi-value">{value}</div>'
        '{change}'
        '</div>'
        '{badge}'
        '</div>'
        '</div>'.format(
            accent=accent, label=label, value=value,
            change=change_html, badge=badge_html,
        ),
        unsafe_allow_html=True,
    )


def dash_metric_card(label, value, change="", value_color="#1E293B"):
    """Render a compact metric card for the secondary row.

    Args:
        label: Metric name
        value: Main display value
        change: Optional change text
        value_color: Color for the main value
    """
    change_html = ""
    if change:
        ch = str(change)
        if ch.startswith("+"):
            color = "#16A34A"
        elif ch.startswith("-"):
            color = "#EF4444"
        else:
            color = "#64748B"
        change_html = (
            '<span class="dash-metric-change" style="color:{};">{}</span>'
        ).format(color, ch)

    st.markdown(
        '<div class="dash-metric">'
        '<div class="dash-metric-label">{label}</div>'
        '<div class="dash-metric-row">'
        '<span class="dash-metric-value" style="color:{vc};">{value}</span>'
        '{change}'
        '</div>'
        '</div>'.format(label=label, value=value, vc=value_color, change=change_html),
        unsafe_allow_html=True,
    )


def dash_section_header(title, subtitle=""):
    """Render a section header for the dashboard."""
    sub_html = ""
    if subtitle:
        sub_html = '<span class="dash-section-subtitle">{}</span>'.format(subtitle)
    st.markdown(
        '<div class="dash-section-header">'
        '<span class="dash-section-title">{}</span>'
        '{}'
        '</div>'.format(title, sub_html),
        unsafe_allow_html=True,
    )


def dash_chart_start(title="", subtitle=""):
    """Open a dashboard chart card container."""
    title_html = ""
    if title:
        title_html = '<div class="dash-chart-title">{}</div>'.format(title)
    sub_html = ""
    if subtitle:
        sub_html = '<div class="dash-chart-subtitle">{}</div>'.format(subtitle)
    st.markdown(
        '<div class="dash-chart-card">'
        '{}{}'.format(title_html, sub_html),
        unsafe_allow_html=True,
    )


def dash_chart_end():
    """Close a dashboard chart card container."""
    st.markdown("</div>", unsafe_allow_html=True)


def dash_progress_card(label, pct, color="#3B82F6"):
    """Render a progress bar card (like the Target Section in the screenshot).

    Args:
        label: What this progress bar represents
        pct: Percentage value (0-100)
        color: Progress bar fill color
    """
    clamped = max(0, min(100, pct if pct is not None else 0))
    st.markdown(
        '<div class="dash-progress-card">'
        '<div class="dash-progress-value" style="color:{color};">{pct:.0f}%</div>'
        '<div class="dash-progress-bar-bg">'
        '<div class="dash-progress-bar-fill" '
        'style="width:{pct:.0f}%;background:{color};"></div>'
        '</div>'
        '<div class="dash-progress-label">{label}</div>'
        '</div>'.format(color=color, pct=clamped, label=label),
        unsafe_allow_html=True,
    )


def dash_dept_status_row(dept_name, status, dept_color="#1F2A44"):
    """Render a single department status row."""
    pill_cls = {
        "Draft": "pill-draft",
        "Submitted": "pill-submitted",
        "Returned": "pill-returned",
        "Approved": "pill-approved",
    }.get(status, "pill-draft")
    st.markdown(
        '<div class="dash-dept-status">'
        '<div style="display:flex;align-items:center;">'
        '<span class="dash-dept-dot" style="background:{dc};"></span>'
        '<span class="dash-dept-name">{name}</span>'
        '</div>'
        '<span class="dash-status-pill {pill}">{status}</span>'
        '</div>'.format(dc=dept_color, name=dept_name, pill=pill_cls, status=status),
        unsafe_allow_html=True,
    )