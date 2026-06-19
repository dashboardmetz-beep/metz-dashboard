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
/* Colored top accent bars unified to a subtle gold inline border on hover.
   Removed bright per-color top strips for premium corporate consistency. */
.dash-kpi::before { content: none; }
.dash-kpi:hover { border-color: #C9A34E; }

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
   PREMIUM CORPORATE LAYER — Bloomberg / McKinsey aesthetic
   ═══════════════════════════════════════════════════════ */

/* Load editorial serif for headlines */
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+Pro:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

/* App background — soft warm white, not gray */
.stApp {
    background: #FAFAF7 !important;
}

/* Body font tightening for corporate feel */
body, .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-feature-settings: "ss01", "ss02", "cv01", "cv11" !important;
    color: #0F172A !important;
    letter-spacing: -0.005em !important;
}

/* Headlines use editorial serif */
h1, h2, h3 {
    font-family: 'Source Serif Pro', 'Times New Roman', Georgia, serif !important;
    color: #0B1929 !important;
    letter-spacing: -0.02em !important;
    font-weight: 600 !important;
}

h1 { font-size: 30px !important; line-height: 1.15 !important; }
h2 { font-size: 22px !important; line-height: 1.25 !important; }
h3 { font-size: 17px !important; line-height: 1.3 !important; }

/* Numbers use tabular monospace for alignment */
.kpi-value, .dash-kpi-value, [class*="kpi"] [class*="value"] {
    font-variant-numeric: tabular-nums !important;
    font-feature-settings: "tnum" !important;
    letter-spacing: -0.025em !important;
}

/* Section labels — more refined */
.section-label, [class*="section-label"] {
    font-size: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: #8B7355 !important;  /* sophisticated taupe */
}

/* Cards — sharper, less rounded, refined borders */
.kpi-card, .dash-kpi, .section-card, .section-card-accent {
    border-radius: 4px !important;
    border: 1px solid #E4E2DC !important;
    background: #FFFFFF !important;
    box-shadow: 0 1px 0 rgba(11,25,41,0.02) !important;
}

.kpi-card:hover, .dash-kpi:hover {
    transform: none !important;  /* no bouncing */
    border-color: #C9C5BA !important;
    box-shadow: 0 2px 8px rgba(11,25,41,0.04) !important;
}

/* Form inputs — corporate-grade refinement */
.stNumberInput input[type="number"],
.stTextInput input[type="text"],
.stTextArea textarea,
.stDateInput input,
.stSelectbox > div > div {
    border: 1px solid #D6D3CA !important;
    border-radius: 3px !important;
    background: #FFFFFF !important;
    font-family: 'IBM Plex Mono', 'SF Mono', Menlo, monospace !important;
    font-size: 13px !important;
    color: #0F172A !important;
    padding: 10px 12px !important;
    box-shadow: inset 0 1px 0 rgba(11,25,41,0.02) !important;
    transition: border-color 0.15s ease !important;
}

.stNumberInput input[type="number"]:focus,
.stTextInput input[type="text"]:focus,
.stTextArea textarea:focus,
.stDateInput input:focus {
    border-color: #B8965A !important;
    box-shadow: 0 0 0 3px rgba(184,150,90,0.10) !important;
    outline: none !important;
}

/* Labels — uppercase mini-caps style */
.stNumberInput label,
.stTextInput label,
.stTextArea label,
.stDateInput label,
.stSelectbox label,
.stRadio label,
.stCheckbox label {
    font-size: 10px !important;
    font-weight: 700 !important;
    color: #5B5246 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    margin-bottom: 6px !important;
    font-family: 'Inter', sans-serif !important;
}

/* Primary buttons — sharp, weighted, executive */
.main .stButton button {
    background: #0B1929 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: none !important;
    border-radius: 3px !important;
    padding: 11px 24px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    letter-spacing: 0.04em !important;
    text-transform: none !important;
    box-shadow: 0 1px 0 rgba(11,25,41,0.10) !important;
    transition: background 0.12s ease !important;
}
.main .stButton button:hover {
    background: #1E2D3E !important;
    transform: none !important;
    box-shadow: 0 2px 4px rgba(11,25,41,0.15) !important;
}

/* Tables — editorial data table aesthetic */
.stDataFrame, [data-testid="stDataFrame"] {
    border-radius: 4px !important;
    border: 1px solid #E4E2DC !important;
    box-shadow: none !important;
}
.stDataFrame thead tr th, [data-testid="stDataFrame"] thead tr th {
    background: #F5F3EE !important;
    color: #5B5246 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.10em !important;
    border-bottom: 1px solid #D6D3CA !important;
    padding: 12px 14px !important;
}
.stDataFrame tbody tr td, [data-testid="stDataFrame"] tbody tr td {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 12px !important;
    font-variant-numeric: tabular-nums !important;
    color: #0F172A !important;
    padding: 11px 14px !important;
    border-bottom: 1px solid #F1EFE9 !important;
}
.stDataFrame tbody tr:hover {
    background: #FAFAF7 !important;
}

/* Tabs — refined editorial */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 1px solid #D6D3CA !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    padding: 13px 22px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    color: #5B5246 !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -1px !important;
    letter-spacing: 0.02em !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #0B1929 !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #0B1929 !important;
    border-bottom-color: #B8965A !important;
    font-weight: 600 !important;
    background: transparent !important;
}

/* Expander — refined */
.streamlit-expanderHeader, [data-testid="stExpander"] summary {
    background: #FFFFFF !important;
    border: 1px solid #E4E2DC !important;
    border-radius: 3px !important;
    padding: 14px 18px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    color: #0B1929 !important;
    box-shadow: none !important;
    letter-spacing: -0.005em !important;
}

/* Radio buttons in main */
.main .stRadio > div[role="radiogroup"] > label {
    background: #FFFFFF !important;
    border: 1px solid #D6D3CA !important;
    border-radius: 3px !important;
    padding: 9px 16px !important;
}
.main .stRadio > div[role="radiogroup"] > label[data-checked="true"],
.main .stRadio > div[role="radiogroup"] > label:has(input:checked) {
    border-color: #B8965A !important;
    background: #FAF7EF !important;
}

/* Alert boxes — corporate restraint */
.stAlert {
    border-radius: 3px !important;
    border-left-width: 3px !important;
    padding: 14px 18px !important;
    font-size: 13px !important;
    box-shadow: none !important;
    font-family: 'Inter', sans-serif !important;
}

/* Plotly charts — clean container */
.stPlotlyChart {
    background: #FFFFFF !important;
    border: 1px solid #E4E2DC !important;
    border-radius: 4px !important;
    padding: 16px !important;
}

/* Block container tightening for executive density */
.block-container {
    max-width: 1480px !important;
    padding-top: 2.5rem !important;
}

/* Subtle gold accent line under page header */
[data-testid="stMarkdownContainer"] h1 + p,
.page-header {
    border-bottom: 1px solid #E4E2DC !important;
    padding-bottom: 16px !important;
    margin-bottom: 24px !important;
}

/* Hover row highlight subtle */
.stDataFrame tbody tr:hover td {
    background: #FAF7EF !important;
}

/* Sidebar refinement */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B1929 0%, #11253C 100%) !important;
    border-right: 1px solid #1E2D3E !important;
}

/* Replace bright accents with gold */
.section-card h3 {
    border-bottom-color: #B8965A !important;
    font-family: 'Source Serif Pro', serif !important;
    font-weight: 600 !important;
}
.section-card-accent {
    border-left-color: #B8965A !important;
}
.kpi-card .kpi-label {
    color: #8B7355 !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 0.14em !important;
}
.kpi-card .kpi-value {
    font-family: 'Source Serif Pro', serif !important;
    color: #0B1929 !important;
}

/* ═══════════════════════════════════════════════════════
   SIDEBAR REFINEMENT — Linear / Stripe / Notion grade
   ═══════════════════════════════════════════════════════ */

/* Sidebar background: deep editorial navy with subtle warmth */
section[data-testid="stSidebar"] {
    background: #0A1525 !important;
    border-right: 1px solid rgba(255,255,255,0.04) !important;
    box-shadow: inset -1px 0 0 rgba(255,255,255,0.02) !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
    padding-bottom: 32px !important;
}

/* Section labels — refined micro-typography */
section[data-testid="stSidebar"] [class*="section-label"],
section[data-testid="stSidebar"] .stMarkdown div[style*="text-transform:uppercase"],
section[data-testid="stSidebar"] .stMarkdown div[style*="text-transform: uppercase"] {
    font-size: 10px !important;
    font-weight: 600 !important;
    color: rgba(255,255,255,0.32) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.14em !important;
    padding: 22px 20px 8px !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
}

/* Sidebar buttons — tight, minimal, no chunky pills */
section[data-testid="stSidebar"] .stButton {
    margin: 0 !important;
    padding: 0 !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 7px 14px !important;
    margin: 1px 12px !important;
    width: calc(100% - 24px) !important;
    text-align: left !important;
    justify-content: flex-start !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    color: rgba(255,255,255,0.62) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.62) !important;
    letter-spacing: -0.005em !important;
    line-height: 1.4 !important;
    min-height: 30px !important;
    box-shadow: none !important;
    transition: background 0.10s ease, color 0.10s ease !important;
    text-transform: none !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.04) !important;
    color: rgba(255,255,255,0.92) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.92) !important;
    transform: none !important;
    box-shadow: none !important;
}
section[data-testid="stSidebar"] .stButton > button p {
    font-size: inherit !important;
    color: inherit !important;
    -webkit-text-fill-color: inherit !important;
    font-weight: inherit !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Active nav item — refined gold left mark + subtle bg */
.nav-active-item {
    background: rgba(255,255,255,0.05) !important;
    border-left: 2px solid #B8965A !important;
    padding: 7px 14px 7px 16px !important;
    margin: 1px 12px 1px 0 !important;
    border-radius: 0 6px 6px 0 !important;
    color: #FFFFFF !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: -0.005em !important;
    line-height: 1.4 !important;
    min-height: 30px !important;
    display: flex !important;
    align-items: center !important;
}

/* Subsection radio — flat, indented, minimal */
section[data-testid="stSidebar"] .stRadio {
    margin: 2px 0 8px !important;
    padding: 0 !important;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] {
    gap: 0 !important;
    padding: 2px 0 0 0 !important;
    background: transparent !important;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {
    background: transparent !important;
    border: none !important;
    border-left: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 0 !important;
    padding: 6px 12px 6px 30px !important;
    margin: 0 12px 0 24px !important;
    cursor: pointer !important;
    min-height: 28px !important;
    transition: background 0.10s ease, color 0.10s ease, border-color 0.10s ease !important;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover {
    background: rgba(255,255,255,0.03) !important;
    border-left-color: rgba(255,255,255,0.18) !important;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"],
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:has(input:checked) {
    background: transparent !important;
    border-left: 2px solid #B8965A !important;
    padding-left: 29px !important;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label > div:first-child {
    display: none !important;  /* hide radio circles */
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label p {
    font-family: 'Inter', sans-serif !important;
    font-size: 12.5px !important;
    font-weight: 400 !important;
    color: rgba(255,255,255,0.48) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.48) !important;
    letter-spacing: -0.005em !important;
    line-height: 1.4 !important;
    margin: 0 !important;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover p {
    color: rgba(255,255,255,0.85) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.85) !important;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] p,
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:has(input:checked) p {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* Brand block at top — refined */
section[data-testid="stSidebar"] [class*="sidebar-brand"],
section[data-testid="stSidebar"] .stMarkdown img + div,
section[data-testid="stSidebar"] [class*="brand"] {
    border-bottom: 1px solid rgba(255,255,255,0.06) !important;
    padding-bottom: 18px !important;
    margin-bottom: 8px !important;
}

/* Remove default horizontal rules in sidebar */
section[data-testid="stSidebar"] hr {
    border: none !important;
    border-top: 1px solid rgba(255,255,255,0.05) !important;
    margin: 14px 20px !important;
}

/* User card / footer in sidebar — refined */
section[data-testid="stSidebar"] [class*="user-card"],
section[data-testid="stSidebar"] [class*="user-info"] {
    border-top: 1px solid rgba(255,255,255,0.06) !important;
    padding: 16px 20px !important;
    margin-top: 16px !important;
}

/* ═══════════════════════════════════════════════════════
   TOP BAR — search + breadcrumbs + user
   ═══════════════════════════════════════════════════════ */

.topbar-crumb {
    display: flex;
    align-items: center;
    gap: 10px;
    height: 38px;
    font-family: 'Inter', sans-serif;
    margin-bottom: 4px;
}
.topbar-crumb .tb-section {
    font-size: 10px;
    font-weight: 700;
    color: #8B7355;
    letter-spacing: 0.14em;
}
.topbar-crumb .tb-sep {
    color: #CBD5E1;
    font-size: 13px;
}
.topbar-crumb .tb-current {
    font-size: 13px;
    font-weight: 500;
    color: #0B1929;
    letter-spacing: -0.005em;
}

.tb-user {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 12px;
    height: 38px;
}
.tb-user-info {
    text-align: right;
    line-height: 1.2;
}
.tb-user-name {
    font-size: 12px;
    font-weight: 600;
    color: #0B1929;
    letter-spacing: -0.005em;
}
.tb-user-role {
    font-size: 9.5px;
    font-weight: 700;
    color: #8B7355;
    letter-spacing: 0.14em;
    margin-top: 2px;
}
.tb-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #0B1929 0%, #1E2D3E 100%);
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    letter-spacing: 0.02em;
    border: 1px solid #D6D3CA;
    box-shadow: 0 1px 2px rgba(11,25,41,0.06);
}

.tb-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, #E4E2DC 12%, #E4E2DC 88%, transparent 100%);
    margin: 14px 0 24px;
}

/* Style the search input inside the top bar */
.stTextInput:has(input[aria-label="Search"]) input {
    background: #FFFFFF !important;
    border: 1px solid #E4E2DC !important;
    border-radius: 4px !important;
    padding: 9px 14px 9px 36px !important;
    font-size: 13px !important;
    font-family: 'Inter', sans-serif !important;
    color: #0B1929 !important;
    box-shadow: 0 1px 2px rgba(11,25,41,0.02) !important;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%238B7355' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='11' cy='11' r='8'/><path d='m21 21-4.3-4.3'/></svg>") !important;
    background-repeat: no-repeat !important;
    background-position: 12px center !important;
}
.stTextInput:has(input[aria-label="Search"]) input::placeholder {
    color: #94A3B8 !important;
    font-weight: 400 !important;
}
.stTextInput:has(input[aria-label="Search"]) input:focus {
    border-color: #B8965A !important;
    box-shadow: 0 0 0 3px rgba(184,150,90,0.10) !important;
}

.tb-search-results {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 4px;
    margin-top: 4px;
    box-shadow: 0 4px 12px rgba(11,25,41,0.06);
    padding: 4px;
}
.tb-search-item {
    padding: 8px 12px;
    font-size: 12px;
    color: #5B5246;
    font-family: 'Inter', sans-serif;
    border-radius: 3px;
}

/* ═══════════════════════════════════════════════════════
   METZ TOP HEADER — Dark bar + horizontal nav
   ═══════════════════════════════════════════════════════ */

/* Hide default Streamlit sidebar entirely */
section[data-testid="stSidebar"] {
    display: none !important;
}
[data-testid="collapsedControl"] {
    display: none !important;
}
.main {
    margin-left: 0 !important;
    padding-top: 0 !important;
}

/* NUCLEAR: Strip all Streamlit container padding via maximum specificity */
html body #root section.stMain,
html body #root .stApp,
html body #root .main,
html body #root .block-container,
html body #root [data-testid="stAppViewContainer"],
html body #root [data-testid="stApp"],
html body #root [data-testid="stMain"],
html body #root [data-testid="stMainBlockContainer"],
html body #root [class*="block-container"],
html body #root [class*="ea3mdgi"],
html body #root [class*="appview-container"] {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
    width: 100% !important;
}

.stApp {
    margin: 0 !important;
    padding: 0 !important;
    width: 100vw !important;
    overflow-x: hidden !important;
}

.main {
    margin-left: 0 !important;
    margin-right: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}

.main .block-container {
    padding-top: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    padding-bottom: 4rem !important;
    max-width: 100% !important;
    width: 100% !important;
}

/* Streamlit hides sidebar via display:none but the main still has left-margin */
section[data-testid="stSidebar"] + .main,
section[data-testid="stSidebar"] ~ .main {
    margin-left: 0 !important;
    padding-left: 0 !important;
    width: 100vw !important;
}

/* Remove header bar + toolbar entirely */
.stApp > header,
[data-testid="stHeader"],
[data-testid="stToolbar"],
.stApp [data-testid="stStatusWidget"] {
    display: none !important;
    height: 0 !important;
}

/* Body should have no margin */
body { margin: 0 !important; padding: 0 !important; }

/* ═══════════════════════════════════════════════════════
   METZ NAV SHELL — premium corporate (mockup-accurate)
   Tokens: Navy #0B1628 / Gold #C9A34E
           Cream #F5F1E8 (nav row bg) / Bg #FAFAF7
           Text #101827 / Border #E5E7EB / Radius ≤ 10px
   ═══════════════════════════════════════════════════════ */

/* DARK HEADER — full-width navy bar */
.metz-shell {
    width: 100vw !important;
    margin-left: calc(-50vw + 50%) !important;
    box-sizing: border-box !important;
    background: #0B1628;
    color: #FFFFFF;
    display: flex;
    align-items: center;
    gap: 18px;
    padding: 0 28px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    font-family: 'Inter', sans-serif;
    min-height: 70px;
}
.metz-shell .ms-brand { padding: 12px 0; }
/* Push search to flex-grow so it stretches between primary nav and admin */
.metz-shell .ms-search { flex: 1 1 auto; margin-left: 12px; max-width: 380px; padding: 8px 12px; }
.metz-shell .ms-admin { padding: 12px 0; }

/* Brand — official Metz logo on a light pill so dark wordmark reads on navy */
.ms-brand { display: flex; align-items: center; flex-shrink: 0; }
.ms-logo-pill {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 8px 14px;
    display: inline-flex;
    align-items: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.18);
}
.ms-logo-pill img {
    height: 44px;
    width: auto;
    display: block;
}
@media (max-width: 1100px) {
    .ms-logo-pill img { height: 36px; }
    .ms-logo-pill { padding: 6px 10px; }
}
@media (max-width: 720px) {
    .ms-logo-pill img { height: 30px; }
}
/* legacy classes (kept harmless in case anything else references them) */
.ms-laurel { width: 54px; height: 54px; flex-shrink: 0; }
.ms-brand-text { display: none; }

/* Search — centered between brand and admin */
.ms-search {
    flex: 1;
    display: flex; align-items: center; gap: 10px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 10px 14px;
    color: rgba(255,255,255,0.55);
    max-width: 720px;
    margin: 0 auto;
}
.ms-search input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: rgba(255,255,255,0.85);
    font-family: 'Inter', sans-serif;
    font-size: 13px;
}
.ms-search input::placeholder { color: rgba(255,255,255,0.42); }
.ms-kbd {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 10.5px;
    color: rgba(255,255,255,0.60);
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
}

/* Admin cluster */
.ms-admin { display: flex; align-items: center; gap: 14px; flex-shrink: 0; }
.ms-bell {
    position: relative;
    background: transparent; border: none;
    color: rgba(255,255,255,0.70);
    cursor: pointer;
    padding: 8px;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    transition: background .12s ease, color .12s ease;
}
.ms-bell:hover { background: rgba(255,255,255,0.08); color: #FFFFFF; }
.ms-bell-dot {
    position: absolute;
    top: 6px; right: 7px;
    width: 7px; height: 7px;
    background: #DC2626;
    border-radius: 50%;
    border: 1.5px solid #0B1628;
}
.ms-userinfo { display: flex; flex-direction: column; text-align: right; line-height: 1.2; }
.ms-uname { font-size: 13px; font-weight: 600; color: #FFFFFF; }
.ms-urole { font-size: 10.5px; font-weight: 500; color: rgba(255,255,255,0.55); margin-top: 2px; }
.ms-avatar {
    width: 36px; height: 36px;
    border-radius: 50%;
    background: #C9A34E;
    color: #0B1628;
    font-size: 13px; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    letter-spacing: 0.02em;
}
.ms-chev { color: rgba(255,255,255,0.55); }

/* Responsive */
@media (max-width: 1180px) {
    .ms-search { max-width: 360px; }
    .ms-userinfo { display: none; }
}
@media (max-width: 880px) {
    .ms-search { display: none; }
    .ms-sub { display: none; }
}

/* ─── INLINE PRIMARY NAV (plain text tabs inside dark header) ─── */
.ms-primary-nav {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
}
.ms-pnav-link {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 22px 16px;
    color: rgba(255,255,255,0.65) !important;
    font-family: 'Inter', sans-serif;
    font-size: 13.5px;
    font-weight: 500;
    letter-spacing: -0.005em;
    text-decoration: none !important;
    transition: color .12s ease;
    white-space: nowrap;
}
.ms-pnav-link:link, .ms-pnav-link:visited, .ms-pnav-link:hover,
.ms-pnav-link:focus, .ms-pnav-link:active {
    text-decoration: none !important;
}
.ms-pnav-link:hover { color: #FFFFFF !important; }
.ms-pnav-link.active {
    color: #C9A34E !important;
    font-weight: 600;
}
.ms-pnav-link.active::after {
    content: "";
    position: absolute;
    left: 16px;
    right: 16px;
    bottom: 0;
    height: 2px;
    background: #C9A34E;
    border-radius: 1px;
}
.ms-pnav-badge {
    background: #DC2626;
    color: #FFFFFF;
    font-size: 10px;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 9px;
    line-height: 1.5;
    min-width: 18px;
    text-align: center;
}


/* ─── SECONDARY SUBNAV ROW — pure anchor links (slim white) ─── */
.ms-subnav-row {
    width: 100vw;
    margin-left: calc(-50vw + 50%);
    background: #FFFFFF;
    padding: 0 28px;
    box-sizing: border-box;
    border-bottom: 1px solid #E5E7EB;
    display: flex;
    gap: 0;
    align-items: stretch;
    overflow-x: auto;
}
.ms-subnav-link {
    flex: 1 1 0;
    text-align: center;
    padding: 13px 18px;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 500;
    color: #6B7280 !important;
    text-decoration: none !important;
    border-bottom: 2px solid transparent;
    letter-spacing: -0.005em;
    cursor: pointer;
    transition: color .12s ease, border-color .12s ease;
}
.ms-subnav-link:link,
.ms-subnav-link:visited,
.ms-subnav-link:hover,
.ms-subnav-link:focus,
.ms-subnav-link:active {
    text-decoration: none !important;
}
.ms-subnav-link:hover { color: #101827 !important; }
.ms-subnav-link.active {
    color: #0B1628 !important;
    font-weight: 600;
    border-bottom-color: #C9A34E;
}

/* ─── BREADCRUMB ROW ─── */
[data-testid="stHorizontalBlock"]:has(.ms-breadcrumb),
[data-testid="stHorizontalBlock"]:has([class*="st-key-ms_select_date"]) {
    background: #FFFFFF !important;
    padding: 12px 32px !important;
    width: 100vw !important;
    margin-left: calc(-50vw + 50%) !important;
    box-sizing: border-box !important;
    border-bottom: 1px solid #E5E7EB;
    align-items: center !important;
    gap: 12px !important;
}
.ms-breadcrumb {
    display: flex; align-items: center; gap: 10px;
    font-family: 'Inter', sans-serif;
}
.ms-breadcrumb .bc-section {
    font-size: 10.5px;
    font-weight: 700;
    color: #C9A34E;
    letter-spacing: 0.16em;
}
.ms-breadcrumb .bc-sep { color: #CBD5E1; font-size: 12px; }
.ms-breadcrumb .bc-current {
    font-size: 12.5px;
    font-weight: 500;
    color: #0B1628;
    letter-spacing: -0.005em;
}
/* Select Date button */
html body .stApp [data-testid="stMain"] .st-key-ms_select_date .stButton > button {
    background: #FFFFFF !important;
    color: #0B1628 !important;
    -webkit-text-fill-color: #0B1628 !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 7px 14px !important;
    height: auto !important;
    min-height: 0 !important;
    box-shadow: 0 1px 2px rgba(11,22,40,0.04) !important;
}
html body .stApp [data-testid="stMain"] .st-key-ms_select_date .stButton > button:hover {
    border-color: #C9A34E !important;
    background: #FAF6EB !important;
}

/* Hide invisible CSS-injection markdown wrappers so they don't add gap */
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has([data-testid="stMarkdownContainer"] > style:first-child),
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has([data-testid="stMarkdownContainer"] > link:first-child) {
    display: none !important;
}

/* Default page-content padding */
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
    padding: 0 32px !important;
}
/* Header rows span full width — no lateral padding */
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"]:has(.metz-shell),
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"]:has(.ms-subnav-row) {
    padding: 0 !important;
}
/* Hide the empty markdown stElementContainer wrapping nav rows from contributing extra gap */
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(.metz-shell),
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(.ms-subnav-row) {
    margin: 0 !important;
    padding: 0 !important;
}

/* ═══════════════════════════════════════════════════════
   OPERATIONS DASHBOARD — premium layout
   ═══════════════════════════════════════════════════════ */

.ops-page-header { padding: 12px 32px 16px; }
.ops-h1 {
    font-family: 'Source Serif Pro', Georgia, serif !important;
    font-size: 26px !important;
    font-weight: 700 !important;
    color: #0B1929 !important;
    letter-spacing: -0.025em !important;
    margin: 0 0 4px 0 !important;
}
.ops-h1-sub {
    font-size: 13px;
    color: #5B5246;
    letter-spacing: -0.005em;
}

.period-display {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 6px;
    padding: 9px 14px;
    text-align: center;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: #0B1929;
}
.period-compare {
    font-size: 11px;
    color: #94A3B8;
    text-align: center;
    margin: 6px 0 18px;
    padding: 0 32px;
    font-style: italic;
}

/* KPI cards — premium with icon circle */
.kpi-premium {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 8px;
    padding: 18px 20px;
    height: 100%;
    transition: box-shadow 0.12s ease, border-color 0.12s ease;
}
.kpi-premium:hover {
    border-color: #CBC6B8;
    box-shadow: 0 2px 8px rgba(11,25,41,0.04);
}
.kpi-row {
    display: flex;
    align-items: flex-start;
    gap: 14px;
}
.kpi-icon-circle {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.kpi-meta { flex: 1; min-width: 0; }
.kpi-label-sm {
    font-size: 10px;
    font-weight: 600;
    color: #8B7355;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.kpi-value-big {
    font-family: 'Source Serif Pro', Georgia, serif;
    font-size: 26px;
    font-weight: 700;
    color: #0B1929;
    line-height: 1.1;
    letter-spacing: -0.025em;
    font-variant-numeric: tabular-nums;
}
.kpi-delta {
    font-size: 11px;
    font-weight: 600;
    margin-top: 6px;
    letter-spacing: -0.005em;
}
.kpi-budget {
    font-size: 11px;
    color: #94A3B8;
    margin-top: 4px;
    font-family: 'IBM Plex Mono', monospace;
    font-variant-numeric: tabular-nums;
}

/* Panel cards (chart + alerts + summary + spend) */
.panel-card {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 8px;
    padding: 20px 22px;
    margin-top: 16px;
    height: 100%;
}
.panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
}
.panel-title {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 600;
    color: #0B1929;
    letter-spacing: -0.005em;
}
.panel-title-row {
    display: flex; align-items: center; gap: 8px;
}
.panel-link {
    font-size: 11px;
    color: #B8965A;
    text-decoration: none;
    font-weight: 600;
    letter-spacing: 0.02em;
}
.panel-link:hover { color: #8B7355; }

.ai-badge {
    background: #FAF7EF;
    color: #B8965A;
    border: 1px solid #E8D9B5;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 9.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.10em;
    margin-left: 6px;
}

/* Alerts list */
.alert-list { display: flex; flex-direction: column; gap: 12px; }
.alert-row {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid #F1EFE9;
}
.alert-row:last-child { border-bottom: none; }
.alert-dot {
    width: 28px; height: 28px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px;
    flex-shrink: 0;
}
.alert-body { flex: 1; min-width: 0; }
.alert-title {
    font-size: 13px;
    font-weight: 600;
    color: #0B1929;
    letter-spacing: -0.005em;
}
.alert-detail {
    font-size: 12px;
    color: #64748B;
    margin-top: 2px;
}
.alert-time {
    font-size: 11px;
    color: #94A3B8;
    flex-shrink: 0;
    font-family: 'IBM Plex Mono', monospace;
}

/* Executive Summary list */
.es-list { display: flex; flex-direction: column; gap: 14px; margin-top: 6px; }
.es-row {
    display: flex;
    gap: 12px;
    align-items: flex-start;
}
.es-icon {
    width: 28px; height: 28px;
    border-radius: 50%;
    background: #F5F3EE;
    color: #B8965A;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.es-text { flex: 1; min-width: 0; }
.es-main {
    font-size: 13px;
    font-weight: 500;
    color: #0B1929;
    letter-spacing: -0.005em;
}
.es-sub {
    font-size: 12px;
    color: #64748B;
    margin-top: 2px;
}

/* Allowable Spend table tabs */
.spend-tabs {
    display: flex;
    gap: 0;
    border-bottom: 1px solid #E4E2DC;
    margin-bottom: 12px;
}
.spend-tab {
    padding: 10px 16px;
    font-size: 12px;
    font-weight: 500;
    color: #5B5246;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    transition: all 0.12s ease;
    margin-bottom: -1px;
    letter-spacing: -0.005em;
}
.spend-tab:hover { color: #0B1929; }
.spend-tab.active {
    color: #0B1929;
    border-bottom-color: #B8965A;
    font-weight: 600;
}

/* Spend table */
.spend-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Inter', sans-serif;
}
.spend-table thead th {
    text-align: left;
    padding: 10px 8px;
    font-size: 10px;
    font-weight: 700;
    color: #8B7355;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    border-bottom: 1px solid #E4E2DC;
}
.spend-table tbody td {
    padding: 14px 8px;
    font-size: 12.5px;
    color: #0B1929;
    border-bottom: 1px solid #F1EFE9;
    font-family: 'IBM Plex Mono', monospace;
    font-variant-numeric: tabular-nums;
}
.spend-table .t-unit {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500;
}
.spend-table .t-num { text-align: right; }
.spend-table .t-allow .t-allow-main {
    font-weight: 600;
}
.spend-table .t-allow .t-allow-sub {
    font-size: 10px;
    color: #94A3B8;
    margin-top: 2px;
}
.spend-table .t-used-row {
    display: flex;
    align-items: center;
    gap: 8px;
}
.spend-table .t-pct {
    font-size: 11px;
    font-weight: 600;
}
.spend-table .t-total td {
    border-top: 2px solid #B8965A;
    background: #FAF7EF;
    padding-top: 14px;
    padding-bottom: 14px;
}


/* ═══════════════════════════════════════════════════════
   DAILY ENTRY — Mockup-accurate layout
   ═══════════════════════════════════════════════════════ */

/* ─── Global Streamlit selectbox restyle to match the premium card look ─── */
html body .stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div,
html body .stApp [data-testid="stSelectbox"] [data-baseweb="select"] [data-baseweb="input"] {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 2px rgba(11,22,40,0.03) !important;
    min-height: 38px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    color: #0B1628 !important;
}
html body .stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div:hover {
    border-color: #C9A34E !important;
}
html body .stApp [data-testid="stSelectbox"] label {
    font-family: 'Inter', sans-serif !important;
    font-size: 10.5px !important;
    font-weight: 700 !important;
    letter-spacing: 0.14em !important;
    color: #8B7E66 !important;
    text-transform: uppercase !important;
}
/* Same for multiselect + date_input + text_input outer container */
html body .stApp [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
html body .stApp [data-testid="stDateInput"] [data-baseweb="input"],
html body .stApp [data-testid="stTextInput"] [data-baseweb="input"] {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 2px rgba(11,22,40,0.03) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
}
html body .stApp [data-testid="stMultiSelect"] [data-baseweb="select"] > div:hover,
html body .stApp [data-testid="stDateInput"] [data-baseweb="input"]:hover,
html body .stApp [data-testid="stTextInput"] [data-baseweb="input"]:hover {
    border-color: #C9A34E !important;
}

/* ─── Style Streamlit's native st.tabs to match the slim white subnav ─── */
html body .stApp [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #E5E7EB !important;
    gap: 4px !important;
    padding: 0 !important;
    margin-bottom: 14px !important;
}
html body .stApp [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    color: #6B7280 !important;
    -webkit-text-fill-color: #6B7280 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 12.5px !important;
    font-weight: 500 !important;
    letter-spacing: -0.005em !important;
    padding: 11px 18px !important;
    margin: 0 !important;
    height: auto !important;
    min-height: 0 !important;
    transition: color .12s ease, border-color .12s ease !important;
}
html body .stApp [data-baseweb="tab"]:hover {
    color: #101827 !important;
    -webkit-text-fill-color: #101827 !important;
    background: transparent !important;
}
html body .stApp [data-baseweb="tab"][aria-selected="true"] {
    color: #0B1628 !important;
    -webkit-text-fill-color: #0B1628 !important;
    font-weight: 600 !important;
    border-bottom-color: #C9A34E !important;
    background: transparent !important;
}
/* hide Streamlit's own underline indicator (we use border-bottom instead) */
html body .stApp [data-baseweb="tab-highlight"],
html body .stApp [data-baseweb="tab-border"] { display: none !important; }

/* ─── Flash Report sub-tab button row → same slim white look ─── */
html body .stApp [data-testid="stMain"] [class*="st-key-fr_subtab_"] .stButton > button {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    color: #6B7280 !important;
    -webkit-text-fill-color: #6B7280 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 12.5px !important;
    font-weight: 500 !important;
    padding: 11px 18px !important;
    margin: 0 !important;
    box-shadow: none !important;
    min-height: 0 !important;
    height: auto !important;
    width: 100% !important;
}
html body .stApp [data-testid="stMain"] [class*="st-key-fr_subtab_"] .stButton > button:hover {
    color: #101827 !important;
    -webkit-text-fill-color: #101827 !important;
    background: transparent !important;
}
html body .stApp [data-testid="stMain"] [class*="st-key-fr_subtab_"] .stButton > button[kind="primary"] {
    color: #0B1628 !important;
    -webkit-text-fill-color: #0B1628 !important;
    font-weight: 600 !important;
    border-bottom: 2px solid #C9A34E !important;
    background: transparent !important;
}
[data-testid="stHorizontalBlock"]:has([class*="st-key-fr_subtab_"]) {
    border-bottom: 1px solid #E5E7EB !important;
    gap: 0 !important;
    margin-bottom: 14px !important;
}

/* ─── Daily Entry step buttons (1 Overview / 2 Sales / etc.) ─── */
html body .stApp [data-testid="stMain"] [class*="st-key-de_step_"] .stButton > button {
    background: #FFFFFF !important;
    color: #6B7280 !important;
    -webkit-text-fill-color: #6B7280 !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 12.5px !important;
    font-weight: 500 !important;
    padding: 12px 14px !important;
    height: auto !important;
    min-height: 44px !important;
    box-shadow: 0 1px 2px rgba(11,22,40,0.03) !important;
    text-align: left !important;
}
html body .stApp [data-testid="stMain"] [class*="st-key-de_step_"] .stButton > button:hover {
    border-color: #C9A34E !important;
    color: #0B1628 !important;
    -webkit-text-fill-color: #0B1628 !important;
    background: #FAF6EB !important;
}
/* Active step (only the current one — needs type="primary" wiring in app) */
html body .stApp [data-testid="stMain"] [class*="st-key-de_step_"] .stButton > button[kind="primary"] {
    background: #0B1628 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: 1px solid #0B1628 !important;
    font-weight: 600 !important;
}

/* Daily Entry inner cards (Weather / Staffing Impact / Communication Notes) */
.de-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 1px 2px rgba(11,22,40,0.03);
    transition: border-color .15s ease;
}
.de-card:hover { border-color: #C9A34E; }
.de-card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.de-card-title {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: #0B1628;
}
.de-card-sub {
    font-size: 11.5px;
    color: #6B7280;
    margin-bottom: 12px;
}

/* ─── Slim corporate footer ─── */
.ms-footer {
    width: 100vw;
    margin-left: calc(-50vw + 50%);
    background: #0B1628;
    color: rgba(255,255,255,0.55);
    padding: 14px 28px;
    margin-top: 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    font-family: 'Inter', sans-serif;
    font-size: 11.5px;
    letter-spacing: 0.02em;
    border-top: 1px solid rgba(255,255,255,0.06);
}
.ms-footer-left, .ms-footer-right { display: flex; align-items: center; gap: 10px; }
.ms-footer-brand {
    color: #C9A34E;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-size: 10.5px;
}
.ms-footer-co { color: rgba(255,255,255,0.75); }
.ms-footer-dot { color: rgba(255,255,255,0.30); }
.ms-footer-right { color: rgba(255,255,255,0.40); font-size: 11px; }
@media (max-width: 720px) {
    .ms-footer { flex-direction: column; gap: 6px; text-align: center; }
}

/* ─── Gmail connection panel (Data Import) ─── */
.gc-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 8px 0 14px;
    box-shadow: 0 1px 2px rgba(11,22,40,0.03);
}
.gc-row { display: flex; align-items: flex-start; gap: 14px; }
.gc-icon {
    width: 42px; height: 42px;
    border-radius: 10px;
    background: #C9A34E;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.gc-body { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.gc-title {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 600;
    color: #0B1628;
    display: flex; align-items: center; gap: 10px;
    letter-spacing: -0.005em;
}
.gc-badge {
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.04em;
    padding: 2px 9px;
    border-radius: 999px;
    text-transform: none;
}
.gc-badge.ok   { background: #DCFCE7; color: #166534; }
.gc-badge.warn { background: #FEF3C7; color: #92400E; }
.gc-badge.err  { background: #FEE2E2; color: #991B1B; }
.gc-msg {
    font-family: 'Inter', sans-serif;
    font-size: 12.5px;
    color: #6B7280;
}
.gc-meta {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    color: #8B7E66;
    margin-top: 2px;
}
.gc-meta code {
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 10.5px;
    background: #F5F1E8;
    padding: 1px 6px;
    border-radius: 4px;
    color: #0B1628;
}
html body .stApp [data-testid="stMain"] .st-key-gmail_reconnect .stButton > button {
    background: #0B1628 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: 1px solid #0B1628 !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 12px 14px !important;
    height: auto !important;
    min-height: 46px !important;
    box-shadow: 0 1px 2px rgba(11,22,40,0.05) !important;
}
html body .stApp [data-testid="stMain"] .st-key-gmail_reconnect .stButton > button:hover {
    background: #1a2540 !important;
    border-color: #C9A34E !important;
}

/* Solo hero (no right-side controls) */
.de-hero-solo {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 18px 24px;
    margin: 16px 0 14px;
    box-shadow: 0 1px 3px rgba(11,22,40,0.04);
}

/* HERO HEADER CARD v2 — icon + title on left, date controls inline on right */
[data-testid="stHorizontalBlock"]:has(.de-hero-left-only) {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 12px !important;
    padding: 18px 24px !important;
    margin: 16px 0 14px !important;
    align-items: center !important;
    box-shadow: 0 1px 3px rgba(11,22,40,0.04) !important;
    gap: 16px !important;
}
.de-hero-left-only {
    display: flex;
    align-items: center;
    gap: 16px;
}
.de-hero-icon {
    width: 48px; height: 48px;
    border-radius: 10px;
    background: #C9A34E;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.de-hero-text { display: flex; flex-direction: column; min-width: 0; }
.de-date-display {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 9px 14px;
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 500;
    color: #0B1628;
    box-shadow: 0 1px 2px rgba(11,22,40,0.03);
    cursor: pointer;
    white-space: nowrap;
}

/* Hero prev/next button styling — applies to all hero-row prev/next keys */
html body .stApp [data-testid="stMain"] .st-key-de_prev_day .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-de_next_day .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-we_prev_week .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-we_next_week .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-fr_prev_week .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-fr_next_week .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-fc_prev_week .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-fc_next_week .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-yoy_prev_week .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-yoy_next_week .stButton > button {
    background: #FFFFFF !important;
    color: #0B1628 !important;
    -webkit-text-fill-color: #0B1628 !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 9px 12px !important;
    height: auto !important;
    min-height: 0 !important;
    box-shadow: 0 1px 2px rgba(11,22,40,0.03) !important;
}
html body .stApp [data-testid="stMain"] .st-key-de_prev_day .stButton > button:hover,
html body .stApp [data-testid="stMain"] .st-key-de_next_day .stButton > button:hover,
html body .stApp [data-testid="stMain"] .st-key-we_prev_week .stButton > button:hover,
html body .stApp [data-testid="stMain"] .st-key-we_next_week .stButton > button:hover,
html body .stApp [data-testid="stMain"] .st-key-fr_prev_week .stButton > button:hover,
html body .stApp [data-testid="stMain"] .st-key-fr_next_week .stButton > button:hover,
html body .stApp [data-testid="stMain"] .st-key-fc_prev_week .stButton > button:hover,
html body .stApp [data-testid="stMain"] .st-key-fc_next_week .stButton > button:hover,
html body .stApp [data-testid="stMain"] .st-key-yoy_prev_week .stButton > button:hover,
html body .stApp [data-testid="stMain"] .st-key-yoy_next_week .stButton > button:hover {
    border-color: #C9A34E !important;
    background: #FAF6EB !important;
}
/* Hero save/primary buttons (dark navy) */
html body .stApp [data-testid="stMain"] .st-key-de_save_all .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-we_save_all_v2 .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-fr_save_all_v2 .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-fc_save_v2 .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-yoy_export_v2 .stButton > button {
    background: #0B1628 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: 1px solid #0B1628 !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 9px 14px !important;
    height: auto !important;
    min-height: 0 !important;
}
html body .stApp [data-testid="stMain"] .st-key-de_save_all .stButton > button:hover,
html body .stApp [data-testid="stMain"] .st-key-we_save_all_v2 .stButton > button:hover,
html body .stApp [data-testid="stMain"] .st-key-fr_save_all_v2 .stButton > button:hover,
html body .stApp [data-testid="stMain"] .st-key-fc_save_v2 .stButton > button:hover,
html body .stApp [data-testid="stMain"] .st-key-yoy_export_v2 .stButton > button:hover {
    background: #1a2540 !important;
    border-color: #1a2540 !important;
}

/* keep old class so we don't break leftover refs */
.de-hero {
    position: relative;
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-left: 4px solid #C9A34E;
    border-radius: 12px;
    padding: 28px 32px;
    margin: 24px 0 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(11,22,40,0.04);
}
.de-hero-content { flex: 1; min-width: 0; z-index: 2; }
.de-hero-eyebrow {
    font-size: 11px;
    font-weight: 700;
    color: #C9A34E;
    letter-spacing: 0.18em;
    margin-bottom: 6px;
}
.de-hero-title {
    font-family: 'Source Serif Pro', Georgia, serif !important;
    font-size: 26px !important;
    font-weight: 700 !important;
    color: #0B1628 !important;
    letter-spacing: -0.02em !important;
    margin: 0 0 2px 0 !important;
    line-height: 1.15 !important;
}
.de-hero-sub {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    color: #6B7280;
}
.de-hero-art { flex-shrink: 0; opacity: 0.85; pointer-events: none; }
.de-mountain { width: 360px; height: 100px; display: block; }
@media (max-width: 1100px) {
    .de-mountain { width: 240px; }
}
@media (max-width: 820px) {
    .de-hero-art { display: none; }
}

/* DATE NAV ROW */
[data-testid="stHorizontalBlock"]:has(.st-key-de_prev_day, .st-key-de_next_day) {
    align-items: center !important;
    margin-bottom: 4px !important;
}
html body .stApp [data-testid="stMain"] .st-key-de_prev_day .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-de_next_day .stButton > button {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    color: #0B1628 !important;
    -webkit-text-fill-color: #0B1628 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 9px 12px !important;
    height: auto !important;
    min-height: 0 !important;
    box-shadow: 0 1px 2px rgba(11,22,40,0.04) !important;
}
html body .stApp [data-testid="stMain"] .st-key-de_prev_day .stButton > button:hover,
html body .stApp [data-testid="stMain"] .st-key-de_next_day .stButton > button:hover {
    border-color: #C9A34E !important;
    background: #FAF6EB !important;
}
.de-date-label {
    font-size: 10.5px;
    font-weight: 700;
    color: #8B7E66;
    letter-spacing: 0.14em;
    text-align: right;
    padding-right: 6px;
}
.de-date-pill {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 9px 14px;
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    font-family: 'IBM Plex Mono', ui-monospace, monospace;
    font-size: 13px;
    font-weight: 500;
    color: #0B1628;
    box-shadow: 0 1px 2px rgba(11,22,40,0.03);
}
.de-date-caption {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin: 10px 0 16px;
    color: #8B7E66;
    font-size: 12px;
    font-family: 'Inter', sans-serif;
}

/* SECTION BAR */
.de-section-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 22px 0 12px;
}
.de-section-title {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 700;
    color: #0B1628;
    letter-spacing: 0.18em;
}
.de-section-title .dim {
    color: #8B7E66;
    font-weight: 500;
}
.de-section-link {
    font-family: 'Inter', sans-serif;
    font-size: 11.5px;
    font-weight: 600;
    color: #C9A34E !important;
    text-decoration: none !important;
}
.de-section-link:hover { color: #B7892E !important; }

/* LIVE WEATHER GRID */
.de-weather-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 14px;
    margin-bottom: 10px;
}
@media (max-width: 1100px) {
    .de-weather-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 720px) {
    .de-weather-grid { grid-template-columns: repeat(2, 1fr); }
}
.de-wcard {
    display: flex;
    align-items: center;
    gap: 14px;
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 16px 18px;
    box-shadow: 0 1px 2px rgba(11,22,40,0.03);
    transition: border-color .15s ease, transform .15s ease;
}
.de-wcard:hover { border-color: #C9A34E; }
.de-wcard-icon {
    width: 42px; height: 42px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.de-wcard-body { display: flex; flex-direction: column; min-width: 0; }
.de-wcard-label {
    font-family: 'Inter', sans-serif;
    font-size: 10.5px;
    font-weight: 700;
    color: #8B7E66;
    letter-spacing: 0.14em;
}
.de-wcard-val {
    font-family: 'Source Serif Pro', Georgia, serif;
    font-size: 22px;
    font-weight: 700;
    color: #0B1628;
    margin-top: 4px;
    letter-spacing: -0.015em;
}

/* QUICK ACTIONS */
[data-testid="stHorizontalBlock"]:has(.st-key-qa_add_entry, .st-key-qa_labor_log, .st-key-qa_sales_log, .st-key-qa_weather_log, .st-key-qa_view_reports) {
    align-items: stretch !important;
    gap: 14px !important;
}
[data-testid="stHorizontalBlock"]:has(.st-key-qa_add_entry, .st-key-qa_labor_log, .st-key-qa_sales_log, .st-key-qa_weather_log, .st-key-qa_view_reports) [data-testid="stColumn"] {
    position: relative;
    min-height: 70px !important;
}
[data-testid="stHorizontalBlock"]:has(.st-key-qa_add_entry, .st-key-qa_labor_log, .st-key-qa_sales_log, .st-key-qa_weather_log, .st-key-qa_view_reports) [data-testid="stColumn"] [data-testid="stVerticalBlock"] {
    min-height: 70px !important;
}
.de-qa-card {
    display: flex;
    align-items: center;
    gap: 12px;
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 14px 16px;
    cursor: pointer;
    transition: border-color .15s ease, box-shadow .15s ease;
    pointer-events: none;
    box-shadow: 0 1px 2px rgba(11,22,40,0.03);
    min-height: 56px;
}
.de-qa-icon {
    width: 36px; height: 36px;
    border-radius: 50%;
    background: #FAF6EB;
    color: #C9A34E;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
    font-weight: 700;
    flex-shrink: 0;
}
.de-qa-label {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: #0B1628;
    letter-spacing: -0.005em;
}
.de-qa-card:hover { border-color: #C9A34E; }
.de-qa-card * { pointer-events: none !important; }

/* Invisible overlay button for quick action click — covers entire card */
html body .stApp [data-testid="stMain"] .st-key-qa_add_entry,
html body .stApp [data-testid="stMain"] .st-key-qa_labor_log,
html body .stApp [data-testid="stMain"] .st-key-qa_sales_log,
html body .stApp [data-testid="stMain"] .st-key-qa_weather_log,
html body .stApp [data-testid="stMain"] .st-key-qa_view_reports {
    position: absolute !important;
    top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important;
    z-index: 5 !important;
    margin: 0 !important;
    padding: 0 !important;
    display: block !important;
}
html body .stApp [data-testid="stMain"] .st-key-qa_add_entry .stButton,
html body .stApp [data-testid="stMain"] .st-key-qa_labor_log .stButton,
html body .stApp [data-testid="stMain"] .st-key-qa_sales_log .stButton,
html body .stApp [data-testid="stMain"] .st-key-qa_weather_log .stButton,
html body .stApp [data-testid="stMain"] .st-key-qa_view_reports .stButton {
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    display: block !important;
}
html body .stApp [data-testid="stMain"] .st-key-qa_add_entry .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-qa_labor_log .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-qa_sales_log .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-qa_weather_log .stButton > button,
html body .stApp [data-testid="stMain"] .st-key-qa_view_reports .stButton > button {
    width: 100% !important;
    height: 100% !important;
    background: transparent !important;
    border: none !important;
    opacity: 0 !important;
    cursor: pointer !important;
    padding: 0 !important;
    margin: 0 !important;
    min-height: 0 !important;
    display: block !important;
}

.de-form-divider {
    height: 1px;
    background: #E5E7EB;
    margin: 28px 0 18px;
}

/* Legacy DE classes (kept for fold-out step form) */
.de-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px 0 8px;
}
.de-icon-circle {
    width: 44px; height: 44px;
    border-radius: 10px;
    background: linear-gradient(135deg, #B8965A, #C7A462);
    color: #FFFFFF;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.de-title {
    font-family: 'Source Serif Pro', Georgia, serif !important;
    font-size: 24px !important;
    font-weight: 700 !important;
    color: #0B1929 !important;
    margin: 0 !important;
    letter-spacing: -0.025em !important;
    line-height: 1.1 !important;
}
.de-sub {
    font-size: 13px;
    color: #5B5246;
    margin-top: 2px;
}

.de-date-display {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 8px;
    padding: 11px 16px;
    display: flex; align-items: center; gap: 10px;
    font-size: 13px; font-weight: 500;
    color: #0B1929;
    margin-top: 18px;
}

/* Step tabs */
.de-step-divider {
    height: 1px;
    background: #E4E2DC;
    margin: 0 0 20px;
}

/* Style the step buttons */
[data-testid="stHorizontalBlock"] .stButton button[key^="de_step_"] {
    background: #FFFFFF !important;
    border: 1px solid #E4E2DC !important;
    border-radius: 8px !important;
    color: #5B5246 !important;
    -webkit-text-fill-color: #5B5246 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 10px 14px !important;
    margin: 8px 0 !important;
    box-shadow: none !important;
    text-transform: none !important;
    letter-spacing: -0.005em !important;
}
[data-testid="stHorizontalBlock"] .stButton button[key^="de_step_"]:hover {
    border-color: #B8965A !important;
    background: #FAF7EF !important;
    color: #0B1929 !important;
    -webkit-text-fill-color: #0B1929 !important;
    transform: none !important;
}

/* Cards for overview step */
.de-card {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 10px;
    padding: 18px 20px;
    height: auto;
    margin-bottom: 0;
}
.de-card-header {
    display: flex; align-items: center; gap: 8px;
    margin-bottom: 6px;
}
.de-card-title {
    font-size: 14px;
    font-weight: 600;
    color: #0B1929;
    letter-spacing: -0.005em;
}
.de-card-sub {
    font-size: 12px;
    color: #64748B;
    margin-bottom: 12px;
}

/* Weather card */
.weather-big {
    font-family: 'Source Serif Pro', Georgia, serif;
    font-size: 36px;
    font-weight: 700;
    color: #0B1929;
    line-height: 1.1;
    margin: 8px 0 2px;
    letter-spacing: -0.025em;
}
.weather-cond {
    font-size: 14px;
    color: #5B5246;
    font-weight: 500;
    margin-bottom: 16px;
}
.weather-stats {
    display: flex;
    gap: 16px;
    border-top: 1px solid #F1EFE9;
    padding-top: 14px;
}
.ws-item {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
}
.ws-label {
    font-size: 10px;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
}
.ws-val {
    font-size: 13px;
    font-weight: 600;
    color: #0B1929;
    font-variant-numeric: tabular-nums;
}

/* Char counter */
.char-counter {
    font-size: 11px;
    color: #94A3B8;
    text-align: right;
    margin-top: 4px;
    font-family: 'IBM Plex Mono', monospace;
}

/* Section header */
.de-section-header {
    font-family: 'Source Serif Pro', Georgia, serif;
    font-size: 17px;
    font-weight: 600;
    color: #0B1929;
    margin: 28px 0 14px;
    letter-spacing: -0.015em;
}

/* At a glance cards */
.glance-card {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 10px;
    padding: 18px 20px;
    height: 100%;
    transition: border-color 0.12s ease, box-shadow 0.12s ease;
}
.glance-card:hover {
    border-color: #CBC6B8;
    box-shadow: 0 2px 8px rgba(11,25,41,0.04);
}
.glance-icon {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 12px;
}
.glance-label {
    font-size: 10px;
    color: #8B7355;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 4px;
}
.glance-value {
    font-family: 'Source Serif Pro', Georgia, serif;
    font-size: 24px;
    font-weight: 700;
    color: #0B1929;
    line-height: 1.1;
    letter-spacing: -0.025em;
    font-variant-numeric: tabular-nums;
}
.glance-delta {
    font-size: 11px;
    color: #64748B;
    margin-top: 4px;
    font-variant-numeric: tabular-nums;
}

/* Info banner */
.info-banner {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 8px;
    padding: 12px 16px;
    margin-top: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 13px;
    color: #1E40AF;
}

/* Sales total banner */
.sales-total {
    background: #FAF7EF;
    border: 1px solid #E8D9B5;
    border-radius: 8px;
    padding: 14px 18px;
    margin-top: 14px;
    font-size: 15px;
    color: #0B1929;
    font-family: 'Source Serif Pro', serif;
}

/* Impact buttons (Step 1) */
.stButton button[key^="im_"] {
    background: #FFFFFF !important;
    color: #5B5246 !important;
    -webkit-text-fill-color: #5B5246 !important;
    border: 1px solid #E4E2DC !important;
}
.stButton button[key="im_no"] {
    background: #ECFDF5 !important;
    color: #16A34A !important;
    -webkit-text-fill-color: #16A34A !important;
    border-color: #86EFAC !important;
    font-weight: 600 !important;
}

/* ═══════════════════════════════════════════════════════
   WEEKLY BUDGET ENTRY — Premium layout
   ═══════════════════════════════════════════════════════ */

.we-header { padding: 16px 0 8px; }
.we-title {
    font-family: 'Source Serif Pro', Georgia, serif !important;
    font-size: 24px !important;
    font-weight: 700 !important;
    color: #0B1929 !important;
    margin: 0 !important;
    letter-spacing: -0.025em !important;
    line-height: 1.1 !important;
}
.we-sub {
    font-size: 13px;
    color: #5B5246;
    margin-top: 2px;
}

.we-week-display {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 8px;
    padding: 11px 16px;
    display: flex; align-items: center; gap: 10px;
    font-size: 13px; font-weight: 500;
    color: #0B1929;
    margin: 18px 0 8px;
}

/* Department tab buttons */
.stButton button[key^="we_dept_"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    color: #5B5246 !important;
    -webkit-text-fill-color: #5B5246 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 12px 14px !important;
    margin: 0 !important;
    box-shadow: none !important;
    text-transform: none !important;
    letter-spacing: -0.005em !important;
    text-align: center !important;
    justify-content: center !important;
}
.stButton button[key^="we_dept_"]:hover {
    color: #0B1929 !important;
    -webkit-text-fill-color: #0B1929 !important;
    background: #FAF7EF !important;
    transform: none !important;
}

/* KPI cards */
.we-kpi-card {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 10px;
    padding: 16px 18px;
    transition: border-color 0.12s ease;
    height: 100%;
}
.we-kpi-card:hover { border-color: #CBC6B8; }
.we-kpi-row { display: flex; align-items: flex-start; gap: 12px; }
.we-kpi-icon {
    width: 40px; height: 40px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.we-kpi-meta { flex: 1; min-width: 0; }
.we-kpi-label {
    font-size: 10px;
    color: #8B7355;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 4px;
}
.we-kpi-value {
    font-family: 'Source Serif Pro', Georgia, serif;
    font-size: 22px;
    font-weight: 700;
    color: #0B1929;
    line-height: 1.1;
    letter-spacing: -0.025em;
    font-variant-numeric: tabular-nums;
}
.we-kpi-delta {
    font-size: 11px;
    color: #94A3B8;
    margin-top: 6px;
}

/* Revenue table section */
.we-section-card {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 10px;
    padding: 18px 20px 8px;
    margin-top: 16px;
}
.we-section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 14px;
    border-bottom: 1px solid #F1EFE9;
}
.we-section-title {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 600;
    color: #0B1929;
    letter-spacing: -0.005em;
}
.we-section-sub {
    font-size: 12px;
    color: #94A3B8;
    margin-left: 10px;
    font-weight: 400;
}

/* Mode toggle buttons */
.stButton button[key="we_mode_amt"],
.stButton button[key="we_mode_pct"] {
    background: #F5F3EE !important;
    border: 1px solid #E4E2DC !important;
    color: #5B5246 !important;
    -webkit-text-fill-color: #5B5246 !important;
    font-size: 12px !important;
    padding: 6px 12px !important;
    border-radius: 6px !important;
    box-shadow: none !important;
    min-height: 32px !important;
}

/* Revenue table */
.we-revenue-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Inter', sans-serif;
    margin-top: 14px;
}
.we-revenue-table thead th {
    text-align: center;
    padding: 10px 8px;
    font-size: 10px;
    font-weight: 700;
    color: #8B7355;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    border-bottom: 1px solid #E4E2DC;
}
.we-revenue-table thead th.t-cat {
    text-align: left;
    padding-left: 12px;
}
.we-revenue-table thead th .t-day-name {
    font-size: 10px;
    color: #5B5246;
    margin-bottom: 2px;
}
.we-revenue-table thead th .t-day-date {
    font-size: 10px;
    color: #94A3B8;
    font-weight: 500;
    text-transform: none;
    letter-spacing: 0;
}
.we-revenue-table tbody td {
    padding: 14px 8px;
    font-size: 13px;
    text-align: center;
    border-bottom: 1px solid #F1EFE9;
    font-family: 'IBM Plex Mono', monospace;
    font-variant-numeric: tabular-nums;
    color: #0B1929;
}
.we-revenue-table tbody td.t-cat {
    text-align: left;
    padding-left: 12px;
    font-family: 'Inter', sans-serif !important;
}
.we-revenue-table tbody td.t-cell {
    background: #FAFAF7;
    border: 1px solid #E4E2DC;
    border-radius: 4px;
    margin: 4px;
}
.we-revenue-table tbody td.t-total-cell {
    font-weight: 700;
    color: #0B1929;
    background: #FAF7EF;
}
.we-revenue-table .t-cat-label {
    display: flex; align-items: center; gap: 8px;
    font-weight: 500;
    color: #0B1929;
}
.we-revenue-table .t-cat-label span {
    color: #5B5246;
    font-weight: 500;
}
.we-revenue-table .t-total-row td {
    border-top: 2px solid #B8965A !important;
    background: #FAF7EF;
    padding-top: 14px;
    padding-bottom: 14px;
}

/* Footer save status */
.we-save-status {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 10px;
    font-size: 12px;
}
.ws-check { display: inline-flex; align-items: center; }
.ws-text { color: #16A34A; font-weight: 500; }
.ws-time { color: #94A3B8; }

/* ═══════════════════════════════════════════════════════
   FLASH REPORT — Premium layout
   ═══════════════════════════════════════════════════════ */

.fr-header { padding: 16px 0 8px; }
.fr-title {
    font-family: 'Source Serif Pro', Georgia, serif !important;
    font-size: 24px !important;
    font-weight: 700 !important;
    color: #0B1929 !important;
    margin: 0 !important;
    letter-spacing: -0.025em !important;
    line-height: 1.1 !important;
}
.fr-sub {
    font-size: 13px;
    color: #5B5246;
    margin-top: 2px;
}

.fr-week-display {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 8px;
    padding: 11px 16px;
    display: flex; align-items: center; gap: 10px;
    font-size: 13px; font-weight: 500;
    color: #0B1929;
    margin: 18px 0 8px;
}

/* Info bar */
.fr-info-bar {
    background: #FAFAF7;
    border: 1px solid #E4E2DC;
    border-radius: 8px;
    padding: 12px 18px;
    display: flex;
    align-items: center;
    gap: 28px;
    margin-top: 16px;
    flex-wrap: wrap;
}
.fr-info-item {
    display: flex; align-items: center; gap: 8px;
    font-size: 12px;
}
.fii-label {
    color: #94A3B8;
    margin-right: 4px;
}
.fii-value {
    color: #0B1929;
    font-variant-numeric: tabular-nums;
}
.fr-badge-imported {
    background: #ECFDF5;
    color: #16A34A;
    border: 1px solid #86EFAC;
    padding: 2px 10px;
    border-radius: 10px;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* KPI cards */
.fr-kpi {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 10px;
    padding: 16px 18px;
    transition: border-color 0.12s ease;
    margin-top: 16px;
    height: 100%;
}
.fr-kpi:hover { border-color: #CBC6B8; }
.fr-kpi-row { display: flex; align-items: flex-start; gap: 12px; }
.fr-kpi-icon {
    width: 40px; height: 40px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.fr-kpi-meta { flex: 1; }
.fr-kpi-label {
    font-size: 10px;
    color: #8B7355;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 4px;
}
.fr-kpi-value {
    font-family: 'Source Serif Pro', Georgia, serif;
    font-size: 22px;
    font-weight: 700;
    color: #0B1929;
    line-height: 1.1;
    letter-spacing: -0.025em;
    font-variant-numeric: tabular-nums;
}
.fr-kpi-delta {
    font-size: 11px;
    margin-top: 6px;
}

/* Subtabs */
.stButton button[key^="fr_subtab_"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    color: #5B5246 !important;
    -webkit-text-fill-color: #5B5246 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 12px 14px !important;
    margin: 0 !important;
    box-shadow: none !important;
    text-transform: none !important;
}
.stButton button[key^="fr_subtab_"]:hover {
    color: #0B1929 !important;
    -webkit-text-fill-color: #0B1929 !important;
    background: #FAF7EF !important;
    transform: none !important;
}
.fr-subtab-divider {
    height: 1px;
    background: #E4E2DC;
    margin-top: -1px;
    margin-bottom: 20px;
}

/* Summary card + table */
.fr-card {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 10px;
    padding: 18px 20px;
    margin-top: 16px;
}
.fr-card-header {
    display: flex;
    align-items: center;
    gap: 6px;
    padding-bottom: 14px;
    border-bottom: 1px solid #F1EFE9;
    margin-bottom: 8px;
}
.fr-card-title {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 600;
    color: #0B1929;
    letter-spacing: -0.005em;
}

.fr-summary-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Inter', sans-serif;
}
.fr-summary-table thead th {
    text-align: right;
    padding: 12px 8px;
    font-size: 10px;
    font-weight: 700;
    color: #8B7355;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    border-bottom: 1px solid #E4E2DC;
}
.fr-summary-table thead th.t-li {
    text-align: left;
    padding-left: 12px;
}
.fr-summary-table tbody td {
    padding: 14px 8px;
    font-size: 13px;
    border-bottom: 1px solid #F1EFE9;
    font-family: 'IBM Plex Mono', monospace;
    font-variant-numeric: tabular-nums;
    color: #0B1929;
}
.fr-summary-table tbody td.t-li {
    font-family: 'Inter', sans-serif !important;
    padding-left: 12px;
}
.fr-summary-table tbody td.t-num {
    text-align: right;
}
.fr-summary-table .t-li-label {
    display: flex; align-items: center; gap: 10px;
    color: #0B1929;
}
.fr-summary-table .t-section-header td.t-section {
    padding: 14px 12px 6px;
    font-size: 10px;
    font-weight: 700;
    color: #8B7355;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    border-bottom: none;
    background: transparent;
}
.fr-summary-table .t-total-row td {
    border-top: 2px solid #B8965A !important;
    background: #FAF7EF;
    padding-top: 14px;
    padding-bottom: 14px;
}

/* Collapsible cost rows */
.fr-collapsible {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 10px;
    padding: 14px 20px;
    margin-top: 12px;
    cursor: pointer;
    transition: border-color 0.12s ease;
}
.fr-collapsible:hover { border-color: #CBC6B8; }
.fr-collapsible-row {
    display: flex;
    align-items: center;
    gap: 8px;
}
.fr-collapsible-meta {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 22px;
    font-size: 13px;
    color: #0B1929;
    font-variant-numeric: tabular-nums;
}

/* ═══════════════════════════════════════════════════════
   FORECAST & ALLOWABLE — Premium layout
   ═══════════════════════════════════════════════════════ */

.fc-header { padding: 16px 0 8px; }
.fc-title {
    font-family: 'Source Serif Pro', Georgia, serif !important;
    font-size: 24px !important;
    font-weight: 700 !important;
    color: #0B1929 !important;
    margin: 0 !important;
    letter-spacing: -0.025em !important;
    line-height: 1.1 !important;
    display: flex; align-items: center; gap: 8px;
}
.fc-sub {
    font-size: 13px;
    color: #5B5246;
    margin-top: 2px;
}
.fc-week-display {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 8px;
    padding: 11px 16px;
    display: flex; align-items: center; gap: 10px;
    font-size: 13px; font-weight: 500;
    color: #0B1929;
    margin: 18px 0 8px;
}

.fc-kpi {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 10px;
    padding: 16px 18px;
    margin-top: 16px;
    transition: border-color 0.12s ease;
    height: 100%;
}
.fc-kpi:hover { border-color: #CBC6B8; }
.fc-kpi-row { display: flex; align-items: flex-start; gap: 12px; }
.fc-kpi-icon {
    width: 40px; height: 40px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.fc-kpi-meta { flex: 1; min-width: 0; }
.fc-kpi-label {
    font-size: 10px;
    color: #8B7355;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 4px;
}
.fc-kpi-value {
    font-family: 'Source Serif Pro', Georgia, serif;
    font-size: 22px;
    font-weight: 700;
    color: #0B1929;
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
}
.fc-kpi-sub {
    font-size: 11px;
    color: #94A3B8;
    margin-top: 4px;
}

.fc-targets-row {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 10px;
    padding: 14px 18px;
    margin-top: 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.fc-targets-left {
    display: flex; align-items: center; gap: 8px;
    font-size: 13px; color: #0B1929;
}
.fc-targets-chev { color: #94A3B8; font-size: 10px; }
.fc-targets-sub {
    color: #94A3B8;
    font-weight: 400;
    margin-left: 8px;
    font-size: 12px;
}

.fc-section-header {
    margin: 20px 0 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.fc-section-title {
    font-family: 'Source Serif Pro', Georgia, serif;
    font-size: 17px;
    font-weight: 600;
    color: #0B1929;
    letter-spacing: -0.015em;
}
.fc-section-meta {
    font-size: 11px;
    color: #94A3B8;
    font-style: italic;
}

.fc-spend-card {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 10px;
    padding: 18px 20px;
    transition: border-color 0.12s ease;
    height: 100%;
}
.fc-spend-card:hover { border-color: #CBC6B8; }
.fc-spend-label {
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 6px;
}
.fc-spend-value {
    font-family: 'Source Serif Pro', Georgia, serif;
    font-size: 26px;
    font-weight: 700;
    color: #0B1929;
    line-height: 1.1;
    letter-spacing: -0.025em;
    font-variant-numeric: tabular-nums;
}
.fc-spend-sub {
    font-size: 11px;
    color: #94A3B8;
    margin-top: 6px;
}

.fc-banner {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 10px;
    padding: 14px 18px;
    margin-top: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
}
.fc-banner-text { font-size: 13px; color: #1E40AF; }
.fc-banner-text span { color: #3B82F6; font-size: 12px; }
.fc-banner-action {
    background: #FFFFFF;
    border: 1px solid #BFDBFE;
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 12px;
    font-weight: 600;
    color: #1E40AF;
    cursor: pointer;
}
.fc-footer-note {
    margin-top: 18px;
    font-size: 11px;
    color: #94A3B8;
    text-align: left;
    font-style: italic;
}

/* ═══════════════════════════════════════════════════════
   YEAR-OVER-YEAR & ALERTS — Premium layout
   ═══════════════════════════════════════════════════════ */

.yoy-header { padding: 16px 0 8px; }
.yoy-title {
    font-family: 'Source Serif Pro', Georgia, serif !important;
    font-size: 24px !important;
    font-weight: 700 !important;
    color: #0B1929 !important;
    margin: 0 !important;
    letter-spacing: -0.025em !important;
    line-height: 1.1 !important;
    display: flex; align-items: center; gap: 8px;
}
.yoy-sub {
    font-size: 13px;
    color: #5B5246;
    margin-top: 2px;
}
.yoy-week-display {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 8px;
    padding: 11px 16px;
    display: flex; align-items: center; gap: 10px;
    font-size: 13px; font-weight: 500;
    color: #0B1929;
    margin: 18px 0 8px;
}

.yoy-kpi {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 10px;
    padding: 16px 18px;
    margin-top: 16px;
    transition: border-color 0.12s ease;
    height: 100%;
}
.yoy-kpi:hover { border-color: #CBC6B8; }
.yoy-kpi-row { display: flex; align-items: flex-start; gap: 12px; }
.yoy-kpi-icon {
    width: 38px; height: 38px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.yoy-kpi-meta { flex: 1; min-width: 0; }
.yoy-kpi-label {
    font-size: 11px;
    color: #5B5246;
    font-weight: 500;
}
.yoy-kpi-value {
    font-family: 'Source Serif Pro', Georgia, serif;
    font-size: 22px;
    font-weight: 700;
    color: #0B1929;
    line-height: 1.1;
    margin-top: 2px;
    font-variant-numeric: tabular-nums;
}
.yoy-kpi-py {
    font-size: 11px;
    color: #94A3B8;
    margin-top: 4px;
    font-variant-numeric: tabular-nums;
}
.yoy-kpi-delta {
    font-size: 11px;
    font-weight: 600;
    margin-top: 4px;
    font-variant-numeric: tabular-nums;
}

.yoy-flags-card {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 10px;
    padding: 16px 20px;
    margin-top: 18px;
}
.yoy-flags-header {
    display: flex; align-items: center; gap: 8px;
    padding-bottom: 12px;
    border-bottom: 1px solid #F1EFE9;
}
.yoy-flags-title {
    font-weight: 600;
    color: #0B1929;
    font-size: 14px;
    letter-spacing: -0.005em;
}
.yoy-flags-link {
    margin-left: auto;
    font-size: 12px;
    color: #B8965A;
    text-decoration: none;
    font-weight: 600;
}
.yoy-flag-empty {
    background: #EFF6FF;
    border-radius: 6px;
    padding: 12px 14px;
    margin-top: 12px;
    display: flex; align-items: center; gap: 10px;
    font-size: 12px;
    color: #1E40AF;
}
.yoy-flag-row {
    background: #FAFAF7;
    border-left: 3px solid #DC2626;
    border-radius: 4px;
    padding: 10px 14px;
    margin-top: 10px;
    font-size: 13px;
    color: #0B1929;
}
.yoy-flag-row span { color: #64748B; }

.yoy-card {
    background: #FFFFFF;
    border: 1px solid #E4E2DC;
    border-radius: 10px;
    padding: 18px 20px;
    margin-top: 18px;
    height: 100%;
}
.yoy-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 14px;
    border-bottom: 1px solid #F1EFE9;
    margin-bottom: 12px;
}
.yoy-card-title {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 600;
    color: #0B1929;
    letter-spacing: -0.005em;
}
.yoy-card-meta {
    font-size: 11px;
    color: #94A3B8;
    background: #FAFAF7;
    border: 1px solid #E4E2DC;
    padding: 4px 10px;
    border-radius: 6px;
}

.yoy-sum-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid #F1EFE9;
}
.yoy-sum-row:last-of-type { border-bottom: none; }
.yoy-sum-name {
    display: flex; align-items: center; gap: 8px;
    font-size: 13px;
    color: #0B1929;
    font-weight: 500;
}
.yoy-sum-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    display: inline-block;
}
.yoy-sum-vals {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 12px;
    font-variant-numeric: tabular-nums;
}
.yoy-sum-this { font-weight: 600; color: #0B1929; }
.yoy-sum-py { color: #94A3B8; }
.yoy-sum-delta { font-weight: 600; }

.yoy-insight-box {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 8px;
    padding: 14px 16px;
    margin-top: 16px;
}
.yoy-insight-title {
    display: flex; align-items: center; gap: 6px;
    font-size: 12px;
    font-weight: 600;
    color: #1E40AF;
    margin-bottom: 6px;
}
.yoy-insight-body {
    font-size: 12px;
    color: #1E40AF;
    line-height: 1.5;
}

.yoy-footer-note {
    margin-top: 18px;
    font-size: 11px;
    color: #94A3B8;
    font-style: italic;
}

/* ═══════════════════════════════════════════════════════
   END METZ TOP HEADER
   ═══════════════════════════════════════════════════════ */

/* ═══════════════════════════════════════════════════════
   END PREMIUM CORPORATE LAYER
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
    padding: 28px 44px 32px;
    max-width: 420px;
    width: 100%;
    box-shadow: 0 24px 48px rgba(15, 23, 42, 0.06);
}
.metz-login-card::before {
    content: '';
    display: block;
    height: 3px;
    background: linear-gradient(90deg, #C7A462 0%, #E8D5A8 50%, #C7A462 100%);
    margin: -28px -44px 18px -44px;
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


def hero_header(title, subtitle, render_right=None, left_ratio=5, right_ratio=5):
    """Premium hero card matching Daily Entry layout.

    Left: gold calendar icon + serif title + Inter subtitle.
    Right: caller-supplied Streamlit controls (date display, prev/next, save).
    If render_right is None, title takes the full hero width.
    """
    left_html = (
        '<div class="de-hero-left-only">'
        '<div class="de-hero-icon">'
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" '
        'stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round">'
        '<rect x="3" y="4" width="18" height="18" rx="2"/>'
        '<line x1="16" y1="2" x2="16" y2="6"/>'
        '<line x1="8" y1="2" x2="8" y2="6"/>'
        '<line x1="3" y1="10" x2="21" y2="10"/></svg>'
        '</div>'
        '<div class="de-hero-text">'
        '<h1 class="de-hero-title">{t}</h1>'
        '<div class="de-hero-sub">{s}</div>'
        '</div>'
        '</div>'.format(t=title, s=subtitle)
    )
    if render_right is None:
        st.markdown(
            '<div class="de-hero-solo">{}</div>'.format(left_html),
            unsafe_allow_html=True,
        )
        return
    hcol1, hcol2 = st.columns([left_ratio, right_ratio])
    with hcol1:
        st.markdown(left_html, unsafe_allow_html=True)
    with hcol2:
        render_right()


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
    """Slim corporate footer: branding + copyright."""
    from datetime import date as _date
    yr = _date.today().year
    st.markdown(
        '<footer class="ms-footer">'
        '<div class="ms-footer-left">'
        '<span class="ms-footer-brand">{platform}</span>'
        '<span class="ms-footer-dot">·</span>'
        '<span class="ms-footer-co">{company}</span>'
        '</div>'
        '<div class="ms-footer-right">'
        '<span>© {yr} Metz Culinary Management. All rights reserved.</span>'
        '</div>'
        '</footer>'.format(
            platform=PLATFORM_TITLE, company=APP_FULL_NAME, yr=yr,
        ),
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