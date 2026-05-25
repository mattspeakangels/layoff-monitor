"""
lm_style.py — CSS injection per Layoff AI Monitor (Streamlit)

Uso:
    from lm_style import inject_css, VARIANTS
    inject_css("signal")   # chiamare PRIMA di qualsiasi st.* nel tuo script

Varianti disponibili: "signal", "pulse", "radar"
"""

import streamlit as st

# ── Palette per variante ──────────────────────────────────────────
VARIANTS = {
    "signal": {
        "accent":   "#3a7bd5",
        "radius":   "3px",
        "kpi_size": "28px",
        "kpi_font": "'DM Mono', monospace",
    },
    "pulse": {
        "accent":   "#06c9c2",
        "radius":   "8px",
        "kpi_size": "36px",
        "kpi_font": "'Space Grotesk', sans-serif",
    },
    "radar": {
        "accent":   "#e84855",
        "radius":   "12px",
        "kpi_size": "48px",
        "kpi_font": "'Space Grotesk', sans-serif",
    },
}

COLORS = {
    "dark": {
        "bg":      "#070c18",
        "surface": "#0d1526",
        "card":    "#111e33",
        "border":  "#1c2e48",
        "text1":   "#e2ecf8",
        "text2":   "#6b88a8",
        "text3":   "#3d5a78",
        "amber":   "#f5a623",
        "green":   "#34c759",
        "red":     "#e84855",
    },
    "light": {
        "bg":      "#f4f7fb",
        "surface": "#ffffff",
        "card":    "#ffffff",
        "border":  "#dde3ed",
        "text1":   "#0d1526",
        "text2":   "#4a6282",
        "text3":   "#8ba3be",
        "amber":   "#d97706",
        "green":   "#16a34a",
        "red":     "#dc2626",
    },
}


def inject_css(variant: str = "signal", theme: str = "dark") -> None:
    """
    Inietta Google Fonts + CSS overrides nel DOM Streamlit.
    Chiama questa funzione come PRIMA istruzione del tuo script.
    """
    v = VARIANTS.get(variant, VARIANTS["signal"])
    c = COLORS.get(theme, COLORS["dark"])
    accent = v["accent"]

    css = f"""
    /* ── Google Fonts ─────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=DM+Sans:ital,wght@0,400;0,500;1,400&family=DM+Mono:wght@400;500&display=swap');

    /* ── Nascondi chrome Streamlit non necessario ─────────────── */
    #MainMenu {{ visibility: hidden; }}
    footer    {{ visibility: hidden; }}
    header    {{ visibility: hidden; }}

    /* ── Font base ────────────────────────────────────────────── */
    html, body, [class*="css"] {{
        font-family: 'DM Sans', sans-serif;
    }}

    /* ── Layout principale ────────────────────────────────────── */
    .main .block-container {{
        max-width: 1400px;
        padding: 1.5rem 2rem 3rem;
    }}

    /* ── Sidebar ──────────────────────────────────────────────── */
    [data-testid="stSidebar"] {{
        background: {c['surface']} !important;
        border-right: 1px solid {c['border']} !important;
    }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        font-weight: 600;
        color: {c['text2']};
        margin-bottom: 4px;
    }}

    /* ── st.metric → KPI card ─────────────────────────────────── */
    [data-testid="metric-container"] {{
        background: {c['card']};
        border: 1px solid {c['border']};
        border-radius: {v['radius']};
        padding: 14px 16px;
        transition: background 0.15s;
    }}
    {'[data-testid="metric-container"] { border-left: 2px solid ' + accent + ' !important; }' if variant == "signal" else ''}
    [data-testid="metric-container"]:hover {{
        background: color-mix(in srgb, {accent} 5%, {c['card']});
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 11px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: {c['text2']} !important;
    }}
    [data-testid="stMetricValue"] {{
        font-family: {v['kpi_font']} !important;
        font-size: {v['kpi_size']} !important;
        font-weight: 700 !important;
        color: {c['text1']} !important;
        letter-spacing: -0.5px;
    }}
    [data-testid="stMetricDelta"] {{
        font-size: 11px !important;
        color: {c['text3']} !important;
    }}

    /* ── Tabs ─────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {{
        background: {c['surface']};
        border-bottom: 1px solid {c['border']};
        gap: 0;
    }}
    .stTabs [data-baseweb="tab"] {{
        font-family: 'DM Sans', sans-serif;
        font-size: 12px;
        font-weight: 500;
        color: {c['text3']};
        border-bottom: 2px solid transparent;
        padding: 10px 16px;
    }}
    .stTabs [aria-selected="true"] {{
        color: {accent} !important;
        border-bottom-color: {accent} !important;
        background: transparent !important;
    }}

    /* ── Plotly chart container ───────────────────────────────── */
    [data-testid="stPlotlyChart"] {{
        background: {c['card']};
        border: 1px solid {c['border']};
        border-radius: {v['radius']};
        overflow: hidden;
    }}

    /* ── Dataframe/Table ──────────────────────────────────────── */
    [data-testid="stDataFrame"] {{
        border: 1px solid {c['border']};
        border-radius: {v['radius']};
        overflow: hidden;
    }}
    [data-testid="stDataFrame"] th {{
        background: {c['surface']} !important;
        font-size: 10px !important;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: {c['text3']} !important;
        font-weight: 600 !important;
        border-bottom: 1px solid {c['border']} !important;
    }}
    [data-testid="stDataFrame"] td {{
        font-size: 12px !important;
        color: {c['text2']} !important;
        border-bottom: 1px solid {c['border']} !important;
    }}

    /* ── Buttons ──────────────────────────────────────────────── */
    .stButton > button {{
        background: transparent;
        border: 1px solid {c['border']};
        border-radius: 5px;
        color: {c['text2']};
        font-family: 'DM Sans', sans-serif;
        font-size: 12px;
        font-weight: 500;
        padding: 6px 16px;
        transition: all 0.15s;
    }}
    .stButton > button:hover {{
        background: {c['card']};
        border-color: {accent};
        color: {c['text1']};
    }}
    .stButton > button[kind="primary"] {{
        background: {accent};
        border-color: {accent};
        color: #fff;
        font-weight: 600;
    }}

    /* ── Sliders ──────────────────────────────────────────────── */
    [data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {{
        background: {accent} !important;
    }}
    [data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stTickBar"] {{
        color: {c['text3']};
    }}

    /* ── Expander (Disclaimer) ────────────────────────────────── */
    .streamlit-expanderHeader {{
        background: color-mix(in srgb, {c['amber']} 10%, {c['surface']}) !important;
        border: 1px solid color-mix(in srgb, {c['amber']} 20%, {c['border']}) !important;
        border-radius: {v['radius']} !important;
        font-size: 12px !important;
        color: {c['text2']} !important;
    }}
    .streamlit-expanderContent {{
        background: color-mix(in srgb, {c['amber']} 5%, {c['surface']}) !important;
        border: 1px solid {c['border']} !important;
        border-top: none !important;
        font-size: 12px !important;
        color: {c['text3']} !important;
        line-height: 1.6;
    }}

    /* ── Selectbox / Multiselect ──────────────────────────────── */
    [data-baseweb="select"] > div {{
        background: {c['card']} !important;
        border-color: {c['border']} !important;
        border-radius: 5px !important;
    }}
    [data-baseweb="tag"] {{
        background: color-mix(in srgb, {accent} 20%, transparent) !important;
        color: {accent} !important;
    }}

    /* ── Divider ──────────────────────────────────────────────── */
    hr {{
        border-color: {c['border']} !important;
        margin: 1.5rem 0 !important;
    }}

    /* ── Sezione sidebar titolo ───────────────────────────────── */
    .sidebar-section-title {{
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: {c['text3']};
        margin: 1.2rem 0 0.4rem;
        padding-bottom: 4px;
        border-bottom: 1px solid {c['border']};
    }}
    """

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def section_title(label: str) -> None:
    """Titolo di sezione sidebar stilizzato."""
    st.markdown(f'<div class="sidebar-section-title">{label}</div>', unsafe_allow_html=True)


def custom_header(title: str = "📉 Layoff AI Monitor",
                  subtitle: str = "Monitoraggio licenziamenti tech · <em>AI-related tracking</em>",
                  variant: str = "signal",
                  theme: str = "dark") -> None:
    """Header custom sopra il contenuto principale."""
    v = VARIANTS.get(variant, VARIANTS["signal"])
    c = COLORS.get(theme, COLORS["dark"])
    accent = v["accent"]

    left_border = f"border-left: 3px solid {accent}; padding-left: 12px;" if variant == "signal" else ""

    st.markdown(f"""
    <div style="
        display: flex; align-items: flex-start; gap: 12px;
        margin-bottom: 1.5rem; {left_border}
    ">
        <div style="font-size: 28px; line-height: 1;">📉</div>
        <div>
            <div style="
                font-family: 'Space Grotesk', sans-serif;
                font-size: 22px; font-weight: 700;
                color: {c['text1']}; letter-spacing: -0.5px;
            ">{title}</div>
            <div style="
                font-size: 12px; color: {c['text3']}; margin-top: 2px;
            ">{subtitle}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
