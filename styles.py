"""
Professional theme and styling for the Metz Operations Platform.
Corporate design system — navy, gold, and neutral surfaces.
"""

import base64
import os

import streamlit as st

from config import APP_FULL_NAME, APP_NAME, APP_TAGLINE, LOGO_PATH, PLATFORM_TITLE


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
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700'
        '&family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&display=swap" rel="stylesheet">',
        unsafe_allow_html=True,
    )
    st.markdown(_THEME_CSS, unsafe_allow_html=True)


_THEME_CSS = """<style>
/* -- GLOBAL OVERRIDES -- */

.stApp {
    background-color: #F4F5F7;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -20%, rgba(199, 164, 98, 0.07), transparent),
        linear-gradient(180deg, #F7F8FA 0%, #F0F2F5 100%);
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
    background: rgba(199,164,98,0.14) !important;
    border-left: 2px solid #C7A462 !important;
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
    padding: 24px 28px;
    border-radius: 14px;
    margin-bottom: 24px;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 24px rgba(15, 23, 42, 0.06);
    border: 1px solid #E8EAED;
    border-left: 4px solid #C7A462;
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
    font-size: 11px;
    font-weight: 500;
    font-family: 'Inter', sans-serif;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 40px 0 20px 0;
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
    font-size: 13px;
    font-weight: 600;
    color: #0F172A;
    font-family: 'Inter', sans-serif;
    text-transform: uppercase;
    letter-spacing: 0.06em;
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
    border-radius: 10px;
    padding: 22px;
    border: 1px solid #E4E7EC;
    box-shadow: none;
    margin-bottom: 16px;
}
.dash-chart-card:hover {
    box-shadow: none;
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

/* ═══════════════════════════════════════════════════════
   PROFESSIONAL POLISH LAYER — final touches
   ═══════════════════════════════════════════════════════ */

/* Smoother global font rendering */
* {
    -webkit-font-smoothing: antialiased !important;
    -moz-osx-font-smoothing: grayscale !important;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {
    background: transparent !important;
    height: 0 !important;
}
.stDeployButton {display: none !important;}

/* Cleaner main content padding */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 4rem !important;
    max-width: 1440px !important;
}

/* Subtle background gradient */
.stApp {
    background: linear-gradient(180deg, #F7F8FA 0%, #F1F3F7 100%) !important;
}

/* Smooth all transitions */
button, input, select, textarea, a, .kpi-card, .section-card, .dash-kpi {
    transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Better number input — clean borders */
.stNumberInput input[type="number"],
.stTextInput input[type="text"],
.stTextArea textarea,
.stDateInput input {
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    background: #FFFFFF !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    font-size: 14px !important;
    color: #1E293B !important;
    padding: 9px 12px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
}
.stNumberInput input[type="number"]:focus,
.stTextInput input[type="text"]:focus,
.stTextArea textarea:focus,
.stDateInput input:focus {
    border-color: #C7A462 !important;
    box-shadow: 0 0 0 3px rgba(199,164,98,0.15) !important;
    outline: none !important;
}

/* Cleaner labels */
.stNumberInput label,
.stTextInput label,
.stTextArea label,
.stDateInput label,
.stSelectbox label {
    font-size: 11px !important;
    font-weight: 600 !important;
    color: #64748B !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    margin-bottom: 4px !important;
}

/* Polished primary buttons in main content */
.stApp:not(:has(section[data-testid="stSidebar"])) .stButton button,
.main .stButton button {
    background: linear-gradient(180deg, #1F2A44 0%, #1A2238 100%) !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 22px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05), 0 4px 12px rgba(31,42,68,0.08) !important;
    letter-spacing: 0.01em !important;
}
.main .stButton button:hover {
    background: linear-gradient(180deg, #2A3656 0%, #1F2A44 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.06), 0 8px 24px rgba(31,42,68,0.12) !important;
}
.main .stButton button:active {
    transform: translateY(0) !important;
}

/* Polished tables / dataframes */
.stDataFrame, [data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid #E5E7EB !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
.stDataFrame thead tr th, [data-testid="stDataFrame"] thead tr th {
    background: #F8FAFC !important;
    color: #475569 !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    border-bottom: 1px solid #E5E7EB !important;
    padding: 10px 14px !important;
}
.stDataFrame tbody tr td, [data-testid="stDataFrame"] tbody tr td {
    font-size: 13px !important;
    color: #1E293B !important;
    padding: 10px 14px !important;
    border-bottom: 1px solid #F1F5F9 !important;
}
.stDataFrame tbody tr:hover {
    background: #F8FAFC !important;
}

/* Polish tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #E5E7EB !important;
    gap: 4px !important;
    padding: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 12px 18px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #64748B !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -1px !important;
    transition: all 0.15s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #1E293B !important;
    background: #F8FAFC !important;
}
.stTabs [aria-selected="true"] {
    color: #1F2A44 !important;
    border-bottom-color: #C7A462 !important;
    font-weight: 600 !important;
    background: transparent !important;
}

/* Polish radio buttons in main content (not sidebar) */
.main .stRadio > div[role="radiogroup"] {
    gap: 4px !important;
}
.main .stRadio > div[role="radiogroup"] > label {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    padding: 8px 14px !important;
    transition: all 0.15s ease !important;
}
.main .stRadio > div[role="radiogroup"] > label:hover {
    border-color: #C7A462 !important;
    background: #FFFBF5 !important;
}
.main .stRadio > div[role="radiogroup"] > label[data-checked="true"] {
    border-color: #C7A462 !important;
    background: #FDF8F0 !important;
}

/* Selectbox polish */
.stSelectbox > div > div {
    border-radius: 8px !important;
    border: 1px solid #E2E8F0 !important;
    background: #FFFFFF !important;
    min-height: 38px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
}
.stSelectbox > div > div:hover {
    border-color: #CBD5E1 !important;
}

/* Checkbox polish */
.stCheckbox label {
    font-size: 13px !important;
    color: #1E293B !important;
}

/* Expander polish */
.streamlit-expanderHeader, [data-testid="stExpander"] summary {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    color: #1E293B !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
}
.streamlit-expanderHeader:hover, [data-testid="stExpander"] summary:hover {
    background: #F8FAFC !important;
}

/* Success / Info / Warning / Error message boxes */
.stAlert {
    border-radius: 10px !important;
    border: 1px solid !important;
    padding: 12px 16px !important;
    font-size: 13px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
}

/* Toast notifications polish */
[data-testid="stToast"] {
    border-radius: 12px !important;
    box-shadow: 0 10px 40px rgba(0,0,0,0.12) !important;
    border: 1px solid #E5E7EB !important;
}

/* KPI cards — final polish */
.kpi-card, .dash-kpi {
    border: 1px solid #E5E7EB !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.kpi-card:hover, .dash-kpi:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06), 0 12px 28px rgba(0,0,0,0.04) !important;
    border-color: #CBD5E1 !important;
}

/* Section headers — refined */
h1, h2, h3, h4 {
    font-family: 'Inter', sans-serif !important;
    letter-spacing: -0.02em !important;
}

/* Page header polish */
.page-header {
    margin-bottom: 24px !important;
}

/* Plotly chart container polish */
.stPlotlyChart {
    border-radius: 12px !important;
    background: transparent !important;
}

/* Scrollbar polish */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: #CBD5E1;
    border-radius: 5px;
}
::-webkit-scrollbar-thumb:hover {
    background: #94A3B8;
}

/* Sidebar scrollbar — darker */
section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.12);
}
section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover {
    background: rgba(255,255,255,0.20);
}

/* Mobile responsiveness */
@media (max-width: 768px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 1rem !important;
    }
    .kpi-card, .dash-kpi {
        min-width: 100% !important;
        padding: 16px !important;
    }
    .kpi-card .kpi-value {
        font-size: 24px !important;
    }
    .kpi-card .kpi-label {
        font-size: 11px !important;
    }
    /* Stack columns on mobile */
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
    }
    /* Smaller page header */
    h1 {
        font-size: 24px !important;
    }
    h2 {
        font-size: 18px !important;
    }
    /* Larger touch targets for buttons */
    .stButton button {
        min-height: 44px !important;
        font-size: 14px !important;
    }
    /* Inputs full width on mobile */
    .stNumberInput, .stTextInput, .stTextArea, .stDateInput, .stSelectbox {
        width: 100% !important;
    }
    /* Hide section dividers on mobile to save space */
    hr {
        margin: 12px 0 !important;
    }
    /* Tables horizontal scroll */
    .stDataFrame, [data-testid="stDataFrame"] {
        overflow-x: auto !important;
    }
    /* Sidebar overlay style on mobile */
    section[data-testid="stSidebar"] {
        width: 280px !important;
        min-width: 280px !important;
    }
    /* Tabs scrollable on mobile */
    .stTabs [data-baseweb="tab-list"] {
        overflow-x: auto !important;
        flex-wrap: nowrap !important;
    }
    .stTabs [data-baseweb="tab"] {
        white-space: nowrap !important;
        min-width: max-content !important;
    }
    /* Plotly charts responsive */
    .stPlotlyChart {
        height: auto !important;
    }
    /* Smaller table cells */
    .stDataFrame thead tr th, [data-testid="stDataFrame"] thead tr th {
        font-size: 10px !important;
        padding: 8px !important;
    }
    .stDataFrame tbody tr td, [data-testid="stDataFrame"] tbody tr td {
        font-size: 12px !important;
        padding: 8px !important;
    }
}

/* Tablet adjustments */
@media (max-width: 1024px) and (min-width: 769px) {
    .kpi-card, .dash-kpi {
        min-width: 45% !important;
    }
    .block-container {
        max-width: 100% !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
}

/* Print styles — clean PDF output via Cmd+P / Ctrl+P */
@media print {
    /* Hide chrome */
    section[data-testid="stSidebar"],
    header[data-testid="stHeader"],
    .stDeployButton,
    [data-testid="collapsedControl"],
    .stButton,
    .streamlit-expanderHeader,
    [data-testid="stExpander"] {
        display: none !important;
    }
    /* Reset background */
    .stApp, .main, .block-container {
        background: #FFFFFF !important;
        max-width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    /* Make sure content fits */
    .main {
        margin-left: 0 !important;
    }
    /* Avoid breaking inside cards */
    .kpi-card, .dash-kpi, .section-card {
        break-inside: avoid !important;
        page-break-inside: avoid !important;
        box-shadow: none !important;
        border: 1px solid #E5E7EB !important;
    }
    /* Force black ink for readability */
    h1, h2, h3, h4, p {
        color: #000 !important;
    }
    /* Smaller font for printing */
    body {
        font-size: 11px !important;
    }
}

/* ═══════════════════════════════════════════════════════
   CORPORATE PREMIUM — Metz Culinary Management
   ═══════════════════════════════════════════════════════ */

.stApp {
    background: #F6F7F9 !important;
    background-image: none !important;
}

.block-container {
    padding-top: 1.75rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 1320px !important;
}

/* Sidebar — executive dark */
section[data-testid="stSidebar"] {
    background: #151D2E !important;
    border-right: 1px solid rgba(255,255,255,0.04) !important;
    min-width: 272px !important;
    width: 272px !important;
}

.nav-group-label {
    color: rgba(255,255,255,0.32) !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.14em !important;
    padding: 22px 20px 8px 20px !important;
    font-family: 'Inter', sans-serif !important;
}

.nav-active-item {
    background: rgba(199,164,98,0.10) !important;
    border-left: 2px solid #C7A462 !important;
    padding: 10px 18px 10px 20px !important;
    margin: 2px 12px 2px 0 !important;
    border-radius: 0 8px 8px 0 !important;
    color: #FFFFFF !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: 0.01em !important;
}

/* Cards — flat corporate */
.section-card,
.section-card-accent,
.page-header,
.date-nav,
.flash-panel,
.weather-card {
    box-shadow: none !important;
    border: 1px solid #E4E7EC !important;
    border-radius: 10px !important;
}
.section-card:hover {
    box-shadow: none !important;
}

.page-header {
    border-left: none !important;
    border-top: 3px solid #C7A462 !important;
    padding: 26px 32px !important;
    margin-bottom: 28px !important;
}

.page-header .ph-eyebrow {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #C7A462;
    margin: 0 0 8px 0;
    font-family: 'Inter', sans-serif;
}
.page-header .ph-title {
    font-size: 26px;
    font-weight: 600;
    color: #0F172A;
    margin: 0;
    letter-spacing: -0.03em;
    line-height: 1.25;
    font-family: 'Inter', sans-serif;
}
.page-header .ph-sub {
    font-size: 14px;
    font-weight: 400;
    color: #64748B;
    margin: 8px 0 0 0;
    line-height: 1.5;
}

/* KPI — minimal */
.kpi-card, .dash-kpi, div[data-testid="stMetric"] {
    box-shadow: none !important;
    border: 1px solid #E4E7EC !important;
    border-radius: 10px !important;
    background: #FFFFFF !important;
}
.kpi-card:hover, .dash-kpi:hover, div[data-testid="stMetric"]:hover {
    transform: none !important;
    border-color: #D1D5DB !important;
    box-shadow: none !important;
}

.dash-kpi::before { height: 2px !important; }
.dash-kpi.accent-blue::before,
.dash-kpi.accent-navy::before { background: #1F2A44 !important; }
.dash-kpi.accent-gold::before { background: #C7A462 !important; }

/* Buttons — primary vs secondary */
[data-testid="stMain"] .stButton > button[kind="primary"],
[data-testid="stMain"] .stButton button[data-testid="baseButton-primary"] {
    background: #1F2A44 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: 1px solid #1F2A44 !important;
    border-radius: 8px !important;
    height: 42px !important;
    min-height: 42px !important;
    padding: 0 20px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    box-shadow: none !important;
    transform: none !important;
}
[data-testid="stMain"] .stButton > button[kind="primary"]:hover,
[data-testid="stMain"] .stButton button[data-testid="baseButton-primary"]:hover {
    background: #2A3654 !important;
    border-color: #2A3654 !important;
    box-shadow: none !important;
    transform: none !important;
}

[data-testid="stMain"] .stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]) {
    background: #FFFFFF !important;
    color: #1F2A44 !important;
    -webkit-text-fill-color: #1F2A44 !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 8px !important;
    height: 40px !important;
    min-height: 40px !important;
    padding: 0 16px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    box-shadow: none !important;
    transform: none !important;
}
[data-testid="stMain"] .stButton > button:not([kind="primary"]):not([data-testid="baseButton-primary"]):hover {
    background: #F8FAFC !important;
    border-color: #94A3B8 !important;
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    box-shadow: none !important;
    transform: none !important;
}

/* Legacy global button override — disable heavy gradients */
.stButton > button:not([kind="primary"]) {
    background: #FFFFFF !important;
    color: #1F2A44 !important;
    -webkit-text-fill-color: #1F2A44 !important;
    border: 1px solid #D1D5DB !important;
    box-shadow: none !important;
    height: 40px !important;
    transform: none !important;
}
.stButton > button[kind="primary"] {
    background: #1F2A44 !important;
    box-shadow: none !important;
    height: 42px !important;
    transform: none !important;
}

/* Tabs — underline only */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 1px solid #E4E7EC !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    padding: 0 !important;
}
.stTabs [aria-selected="true"] {
    background: transparent !important;
    color: #0F172A !important;
    box-shadow: none !important;
    border-bottom: 2px solid #C7A462 !important;
}

/* Streamlit chrome */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu, footer, .stDeployButton, [data-testid="stToolbar"] {
    display: none !important;
    visibility: hidden !important;
}

/* Alerts — subtle */
div[data-testid="stAlert"] {
    border-radius: 8px !important;
    font-size: 13px !important;
}

/* Login shell */
.metz-login-shell {
    min-height: 88vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px 24px;
}
.metz-login-card {
    background: #FFFFFF;
    border: 1px solid #E4E7EC;
    border-radius: 12px;
    padding: 48px 44px 40px;
    max-width: 420px;
    width: 100%;
    box-shadow: 0 24px 48px rgba(15, 23, 42, 0.06);
}
.metz-login-card::before {
    content: '';
    display: block;
    height: 3px;
    background: linear-gradient(90deg, #C7A462 0%, #E8D5A8 50%, #C7A462 100%);
    margin: -48px -44px 32px -44px;
    border-radius: 12px 12px 0 0;
}
.metz-login-eyebrow {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #C7A462;
    text-align: center;
    margin-bottom: 20px;
}
.metz-login-title {
    font-size: 22px;
    font-weight: 600;
    color: #0F172A;
    text-align: center;
    letter-spacing: -0.03em;
    margin: 0 0 8px 0;
}
.metz-login-sub {
    font-size: 14px;
    color: #64748B;
    text-align: center;
    line-height: 1.55;
    margin: 0 0 32px 0;
}

.app-footer {
    border-top: 1px solid #E4E7EC !important;
    color: #94A3B8 !important;
    font-size: 10px !important;
    letter-spacing: 0.1em !important;
    padding: 32px 0 24px !important;
    margin-top: 56px !important;
}
</style>
"""


# ─── Component Helpers ───


def page_header(title, subtitle="", metadata_right=""):
    """Render a branded corporate page header."""
    sub_html = ""
    if subtitle:
        sub_html = '<p class="ph-sub">{}</p>'.format(subtitle)
    meta_html = ""
    if metadata_right:
        meta_html = (
            '<div style="text-align:right;font-size:12px;font-weight:500;'
            'color:#64748B;letter-spacing:0.02em;white-space:nowrap;'
            'padding-top:4px;">{}</div>'
        ).format(metadata_right)
    st.markdown(
        '<div class="page-header" style="display:flex;justify-content:space-between;'
        'align-items:flex-start;">'
        '<div>'
        '<p class="ph-eyebrow">{}</p>'
        '<h1 class="ph-title">{}</h1>'
        '{}'
        '</div>'
        '{}'
        '</div>'.format(APP_NAME.upper(), title, sub_html, meta_html),
        unsafe_allow_html=True,
    )


def section_title(icon, title, anchor_id=""):
    """Render a styled section title with optional anchor for sidebar scroll-to."""
    aid = anchor_id or title.lower().replace(" ", "-").replace("/", "-")
    st.markdown(
        '<div id="{aid}" style="margin:36px 0 14px 0;scroll-margin-top:80px;'
        'padding-bottom:10px;border-bottom:1px solid #E4E7EC;">'
        '<span style="font-size:13px;font-weight:600;color:#0F172A;'
        'font-family:Inter,sans-serif;letter-spacing:0.04em;'
        'text-transform:uppercase;">{title}</span>'
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
        '<div class="kpi-card" style="padding:20px 22px;text-align:left;'
        'border-top:2px solid {accent};">'
        '<div style="font-size:10px;font-weight:600;text-transform:uppercase;'
        'letter-spacing:0.1em;color:#94A3B8;margin-bottom:10px;'
        'font-family:Inter,sans-serif;">{label}</div>'
        '<div style="font-size:28px;font-weight:600;color:#0F172A;'
        'letter-spacing:-0.02em;line-height:1.2;font-family:Inter,sans-serif;">'
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
        'font-size:14px;font-weight:500;background:#FAFBFC;border-radius:10px;'
        'border:1px solid #E4E7EC;font-family:Inter,sans-serif;">'
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

def sidebar_brand():
    """Render Metz logo and product name at the top of the sidebar."""
    logo_html = (
        '<div style="width:40px;height:40px;border-radius:10px;'
        'background:linear-gradient(145deg,#3D2B1F 0%,#5C4033 100%);'
        'display:flex;align-items:center;justify-content:center;'
        'font-size:11px;font-weight:800;color:#C7A462;flex-shrink:0;'
        'letter-spacing:0.04em;border:1px solid rgba(199,164,98,0.35);">M</div>'
    )
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        logo_html = (
            '<img src="data:image/png;base64,{}" alt="Metz" '
            'style="width:40px;height:40px;object-fit:contain;flex-shrink:0;'
            'border-radius:8px;background:#fff;padding:4px;"/>'
        ).format(b64)

    st.sidebar.markdown(
        '<div style="padding:24px 20px 20px;border-bottom:1px solid rgba(255,255,255,0.06);">'
        '<div style="display:flex;align-items:center;gap:14px;">'
        '{logo}'
        '<div style="min-width:0;">'
        '<div style="font-size:14px;font-weight:600;color:#FFFFFF;'
        'letter-spacing:-0.02em;font-family:Inter,sans-serif;">{name}</div>'
        '<div style="font-size:9px;font-weight:600;color:rgba(199,164,98,0.85);'
        'text-transform:uppercase;letter-spacing:0.14em;margin-top:4px;">'
        '{tag}</div></div></div>'
        '<div style="height:1px;background:linear-gradient(90deg,transparent,'
        'rgba(199,164,98,0.5),transparent);margin-top:18px;"></div>'
        '</div>'.format(logo=logo_html, name=APP_NAME, tag=APP_TAGLINE),
        unsafe_allow_html=True,
    )


def app_footer():
    """Render app footer."""
    st.markdown(
        '<div class="app-footer">'
        '{platform} &middot; {company}'
        '</div>'.format(platform=PLATFORM_TITLE, company=APP_FULL_NAME),
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