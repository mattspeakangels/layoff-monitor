"""Layoff AI Monitor — Streamlit dashboard with custom design system."""

from __future__ import annotations

from datetime import datetime, timedelta, date

import pandas as pd
import streamlit as st

from db import get_layoff_events
from etl import run_etl_with_ui
from scraper import RSS_SOURCES

from lm_style import inject_css, section_title, custom_header
from lm_charts import area_chart, hbar_chart
from lm_kpi import kpi_row

ACCENTS = {"signal": "#3a7bd5", "pulse": "#06c9c2", "radar": "#e84855"}
SOURCE_OPTIONS = ["Hacker News"] + list(RSS_SOURCES.keys())

st.set_page_config(
    page_title="Layoff AI Monitor",
    layout="wide",
    page_icon="📉",
)

# ---------- SIDEBAR: UI switchers (must run BEFORE inject_css) ----------
st.sidebar.markdown("## ⊟ Filtri")

with st.sidebar.expander("🎨 Aspetto", expanded=False):
    variant = st.radio(
        "Variante",
        ["signal", "pulse", "radar"],
        format_func=lambda v: {"signal": "⚡ Signal", "pulse": "◎ Pulse", "radar": "◉ Radar"}[v],
        horizontal=True,
    )
    light_mode = st.toggle("Tema chiaro", value=False)

THEME = "light" if light_mode else "dark"
ACCENT = ACCENTS[variant]

inject_css(variant=variant, theme=THEME)

# ---------- HEADER ----------
custom_header(
    title="Layoff AI Monitor",
    subtitle="Monitoraggio licenziamenti tech · <em>AI-related tracking</em>",
    variant=variant,
    theme=THEME,
)

with st.expander("⚠️ Limiti dei dati — leggi prima di usare", expanded=False):
    st.markdown(
        """
        - **Fonti**: Hacker News (Algolia API) + TechCrunch RSS + Google News RSS.
        - **Estrazione euristica**: nome azienda e numero dipendenti sono ricavati dal titolo via regex.
          Aspettati ~10-20% di errori di parsing.
        - **Filtro "AI"**: keyword matching su titolo + URL. Può includere falsi positivi
          e falsi negativi (azienda AI senza la parola "AI" nel titolo).
        - **NON usare per decisioni di investimento o HR**. Strumento di monitoraggio, non fonte primaria.
        """
    )

# ---------- SIDEBAR: FILTRI ----------
with st.sidebar:
    section_title("Periodo")
    days_back = st.slider(
        "Finestra temporale (giorni)",
        min_value=7, max_value=365, value=90, step=7,
        label_visibility="collapsed",
    )

    section_title("Tipo")
    ai_only = st.toggle("Solo AI-correlati", value=True)

    section_title("Soglie punteggio")
    min_certainty = st.slider(
        "Certezza ≥", 1, 5, 2,
        help="1=unverified, 2=HN/Google News, 3=TechCrunch, 4=Reuters/Bloomberg, 5=SEC filing",
    )
    min_causality = st.slider(
        "AI Causality ≥", 1, 5, 2,
        help="1=co-occurrence, 2=AI mentioned, 3=media attributes, 4=Challenger report, 5=company statement",
    )

    section_title("Nesso causale AI (euristica)")
    ai_cause_filter = st.multiselect(
        "Nesso causale AI",
        options=["high", "medium", "low"],
        default=["high", "medium"],
        help="high = AI esplicitamente causa | medium = AI menzionata | low = solo tema tech",
        label_visibility="collapsed",
    )

    section_title("Fonti")
    selected_sources = st.multiselect(
        "Fonti", options=SOURCE_OPTIONS, default=SOURCE_OPTIONS,
        label_visibility="collapsed",
    )

    section_title("Dipendenti")
    min_employees = st.number_input(
        "Minimo dipendenti coinvolti",
        min_value=0, value=0, step=50,
        label_visibility="collapsed",
    )

    st.divider()
    if st.button("↺ Forza ETL", type="primary", width="stretch"):
        run_etl_with_ui(days_back=days_back)
        st.cache_data.clear()
        st.rerun()

    st.caption("Firestore backend. ETL on demand, no auto-sync yet.")


# ---------- DATA LOAD ----------
@st.cache_data(ttl=300, show_spinner="Carico eventi da Firestore…")
def load_events(days: int) -> pd.DataFrame:
    events = get_layoff_events(days_back=days)
    if not events:
        return pd.DataFrame()
    df = pd.DataFrame(events)
    df["date"] = pd.to_datetime(df["date"])
    return df


try:
    df_all = load_events(days_back)
except Exception as e:
    st.error(f"Errore nel caricamento da Firestore: {e}")
    st.stop()

# ---------- APPLY FILTERS ----------
df = df_all.copy()

if not df.empty:
    if ai_only and "ai_cause" in df.columns:
        df = df[df["ai_cause"].isin(["high", "medium"])]
    if "layoff_certainty" in df.columns:
        df = df[df["layoff_certainty"].fillna(0) >= min_certainty]
    if "ai_causality" in df.columns:
        df = df[df["ai_causality"].fillna(0) >= min_causality]
    if ai_cause_filter and "ai_cause" in df.columns:
        df = df[df["ai_cause"].isin(ai_cause_filter)]
    if selected_sources and "source" in df.columns:
        df = df[df["source"].isin(selected_sources)]
    if min_employees > 0 and "employees" in df.columns:
        df = df[df["employees"].fillna(0) >= min_employees]


# ---------- KPI HELPERS ----------
def weekly_spark(d: pd.DataFrame, col: str = "count", n: int = 12) -> list[int]:
    """Aggrega per settimana e restituisce gli ultimi n valori (per sparkline)."""
    if d.empty:
        return [0] * n
    d2 = d.copy()
    d2["week"] = pd.to_datetime(d2["date"]).dt.tz_localize(None).dt.to_period("W")
    if col == "count":
        g = d2.groupby("week").size()
    else:
        g = d2.groupby("week")[col].sum()
    idx = pd.period_range(end=pd.Timestamp.today(), periods=n, freq="W")
    return [int(g.get(w, 0)) for w in idx]


def weekly_agg(d: pd.DataFrame, col: str = "count", n: int = 24) -> tuple[list[int], list[str]]:
    """Aggrega per settimana e restituisce (valori, labels) per chart."""
    if d.empty:
        idx = pd.period_range(end=pd.Timestamp.today(), periods=n, freq="W")
        return [0] * n, [w.start_time.strftime("%-d %b") for w in idx]
    d2 = d.copy()
    d2["week"] = pd.to_datetime(d2["date"]).dt.tz_localize(None).dt.to_period("W")
    if col == "count":
        g = d2.groupby("week").size()
    else:
        g = d2.groupby("week")[col].sum()
    idx = pd.period_range(end=pd.Timestamp.today(), periods=n, freq="W")
    vals = [int(g.get(w, 0)) for w in idx]
    labels = [w.start_time.strftime("%-d %b") for w in idx]
    return vals, labels


# ---------- KPI ROW ----------
total_stories = len(df)
total_employees = int(df["employees"].fillna(0).sum()) if not df.empty else 0
unique_companies = df["company"].nunique() if not df.empty else 0
if not df.empty:
    cutoff_30 = (datetime.now() - timedelta(days=30)).date()
    last_30 = df[df["date"].dt.date >= cutoff_30]
else:
    last_30 = df

kpi_row(
    [
        {
            "label": "Storie trovate",
            "value": f"{total_stories:,}".replace(",", "."),
            "sub": f"ultimi {days_back} gg",
            "spark": weekly_spark(df, "count"),
            "tooltip": "Stories found — total events matching filters",
        },
        {
            "label": "Dipendenti tracciati",
            "value": f"{total_employees:,}".replace(",", "."),
            "sub": "totale stimato",
            "spark": weekly_spark(df, "employees"),
            "tooltip": "Workers tracked — sum of employees affected",
        },
        {
            "label": "Aziende uniche",
            "value": f"{unique_companies:,}".replace(",", "."),
            "sub": "aziende coinvolte",
            "spark": weekly_spark(df, "count"),
            "tooltip": "Unique companies in current filter",
        },
        {
            "label": "Ultimi 30 giorni",
            "value": f"{len(last_30):,}".replace(",", "."),
            "sub": "storie recenti",
            "spark": weekly_spark(last_30, "count"),
            "tooltip": "Events in the last 30 days",
        },
    ],
    accent=ACCENT, variant=variant, theme=THEME,
)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ---------- CHARTS ----------
col_trend, col_companies = st.columns([3, 2])

with col_trend:
    tab_stories, tab_emp = st.tabs(["📈 Storie/settimana", "👥 Dipendenti/settimana"])

    with tab_stories:
        vals, labels = weekly_agg(df, "count", 24)
        st.plotly_chart(
            area_chart(vals, labels, color=ACCENT, title="Storie per settimana",
                       y_title="n. storie", theme=THEME, variant=variant),
            width="stretch", config={"displayModeBar": False},
        )

    with tab_emp:
        vals, labels = weekly_agg(df, "employees", 24)
        st.plotly_chart(
            area_chart(vals, labels, color=ACCENT, title="Dipendenti per settimana",
                       y_title="dipendenti", theme=THEME, variant=variant),
            width="stretch", config={"displayModeBar": False},
        )

with col_companies:
    if not df.empty:
        top = (
            df.dropna(subset=["employees"])
            .groupby("company", as_index=False)["employees"]
            .sum()
            .sort_values("employees", ascending=False)
            .head(10)
            .to_dict("records")
        )
    else:
        top = []
    st.plotly_chart(
        hbar_chart(top, color=ACCENT, title="Top aziende per dipendenti",
                   theme=THEME, variant=variant),
        width="stretch", config={"displayModeBar": False},
    )

# ---------- TABLE ----------
st.markdown("---")

search = st.text_input("🔍 Cerca azienda, titolo, fonte…", placeholder="es. Google, Salesforce…")

if df.empty:
    st.info("Nessun dato con i filtri correnti. Prova ad ampliare la finestra temporale o premi ↺ Forza ETL.")
else:
    df_show = df.copy()
    if search:
        mask = (
            df_show["company"].astype(str).str.contains(search, case=False, na=False)
            | df_show["title"].astype(str).str.contains(search, case=False, na=False)
            | df_show["source"].astype(str).str.contains(search, case=False, na=False)
        )
        df_show = df_show[mask]

    cert_emoji = {1: "🔴 1", 2: "🟠 2", 3: "🟡 3", 4: "🟢 4", 5: "✅ 5"}
    ai_emoji = {1: "⚪ 1", 2: "🔵 2", 3: "🟡 3", 4: "🟠 4", 5: "🔴 5"}

    df_display = pd.DataFrame({
        "Data": df_show["date"].dt.date,
        "Fonte": df_show["source"],
        "Azienda": df_show["company"],
        "Cert.": df_show.get("layoff_certainty", pd.Series([None] * len(df_show))).map(
            lambda x: cert_emoji.get(int(x), "—") if pd.notna(x) else "—"
        ),
        "AI →": df_show.get("ai_causality", pd.Series([None] * len(df_show))).map(
            lambda x: ai_emoji.get(int(x), "—") if pd.notna(x) else "—"
        ),
        "Dipendenti": df_show["employees"].apply(
            lambda x: f"{int(x):,}".replace(",", ".") if pd.notna(x) else "—"
        ),
        "% WF": df_show.get("percent_workforce", pd.Series([None] * len(df_show))).apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "—"
        ),
        "Titolo": df_show["title"],
        "Articolo": df_show["url"],
        "HN": df_show.get("hn_discussion", pd.Series([None] * len(df_show))),
    })

    st.dataframe(
        df_display,
        width="stretch",
        hide_index=True,
        height=min(500, 60 + 35 * len(df_display)),
        column_config={
            "Articolo": st.column_config.LinkColumn("Articolo", display_text="Apri ↗"),
            "HN": st.column_config.LinkColumn("HN", display_text="↗"),
            "Data": st.column_config.DateColumn("Data"),
        },
    )

    col_info, col_export = st.columns([4, 1])
    with col_info:
        st.caption(f"{len(df_display)} risultati")
    with col_export:
        csv = df_show.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="↓ Esporta CSV",
            data=csv,
            file_name=f"layoff-monitor-{date.today()}.csv",
            mime="text/csv",
            width="stretch",
        )

st.markdown("---")
st.caption(
    "Built with Streamlit • Data: Hacker News Algolia API + TechCrunch + Google News • "
    "Open-source, no API key required."
)
