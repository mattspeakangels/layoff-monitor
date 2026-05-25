"""Layoff AI Monitor — Streamlit dashboard backed by Firestore."""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from db import get_layoff_events
from etl import run_etl_with_ui
from scraper import filter_ai_related

st.set_page_config(
    page_title="Layoff AI Monitor",
    layout="wide",
    page_icon="📉",
)

# ---------- HEADER ----------
st.title("📉 Layoff AI Monitor")
st.caption(
    "Tracker di licenziamenti nel settore tech con focus AI. "
    "Fonti: Hacker News, TechCrunch, Google News. Gratuito, nessuna API key."
)

with st.expander("⚠️ Limiti dei dati — leggi prima di usare", expanded=False):
    st.markdown(
        """
        - **Fonte unica**: solo storie postate su Hacker News. Non copre tutti i layoff (es. molte PMI non finiscono in HN).
        - **Estrazione euristica**: nome azienda e numero dipendenti sono ricavati dal titolo via regex.
          Aspettati ~10-20% di errori di parsing.
        - **Filtro "AI"**: keyword matching su titolo + URL. Può includere falsi positivi (es. azienda non-AI
          la cui notizia menziona AI) e falsi negativi (azienda AI senza la parola "AI" nel titolo).
        - **NON usare per decisioni di investimento o HR**. Strumento di monitoraggio, non fonte primaria.
        """
    )

# ---------- SIDEBAR ----------
st.sidebar.header("Filtri")

days_back = st.sidebar.slider(
    "Finestra temporale (giorni)",
    min_value=7,
    max_value=365,
    value=90,
    step=7,
)

ai_only = st.sidebar.toggle("Solo AI-related", value=True)

st.sidebar.subheader("📊 Dual Scoring")
min_certainty = st.sidebar.slider(
    "Layoff Certainty (min)",
    min_value=1,
    max_value=5,
    value=2,
    help="1=unverified, 2=HN/Google News, 3=TechCrunch, 4=Reuters/Bloomberg, 5=SEC filing",
)

min_causality = st.sidebar.slider(
    "AI Causality (min)",
    min_value=1,
    max_value=5,
    value=2,
    help="1=co-occurrence, 2=AI mentioned, 3=media attributes, 4=Challenger report, 5=company statement",
)

ai_cause_filter = st.sidebar.multiselect(
    "Nesso causale AI (euristica)",
    options=["high", "medium", "low"],
    default=["high", "medium"],
    help="high = AI esplicitamente causa del layoff | medium = AI menzionata | low = solo tema tech",
)

source_options = list(__import__("scraper").RSS_SOURCES.keys()) + ["Hacker News"]
selected_sources = st.sidebar.multiselect("Fonti", options=source_options, default=source_options)

min_employees = st.sidebar.number_input(
    "Minimo dipendenti coinvolti (0 = mostra tutto)",
    min_value=0,
    value=0,
    step=50,
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Forza ETL (fetch + score + write)"):
    run_etl_with_ui(days_back=days_back)
    st.rerun()

st.sidebar.caption("Firestore backend. ETL on demand, no auto-sync yet.")

# ---------- DATA LOAD ----------
try:
    # Load from Firestore
    firestore_events = get_layoff_events(days_back=days_back)
    if not firestore_events:
        st.warning(
            "Nessun evento in Firestore. Usa il bottone 🔄 per eseguire ETL."
        )
        st.stop()

    df_all = pd.DataFrame(firestore_events)
    # Ensure date column is datetime
    df_all["date"] = pd.to_datetime(df_all["date"])

except Exception as e:
    st.error(f"Errore nel caricamento da Firestore: {e}")
    st.stop()

# Apply filters
df = df_all.copy()

# AI-related filter (by ai_cause heuristic)
if ai_only and "ai_cause" in df.columns:
    df = df[df["ai_cause"].isin(["high", "medium"])]

# Dual scoring filters
if "layoff_certainty" in df.columns:
    df = df[df["layoff_certainty"].fillna(0) >= min_certainty]
if "ai_causality" in df.columns:
    df = df[df["ai_causality"].fillna(0) >= min_causality]

# Heuristic AI cause filter
if ai_cause_filter and "ai_cause" in df.columns:
    df = df[df["ai_cause"].isin(ai_cause_filter)]

# Source filter
if selected_sources and "source" in df.columns:
    df = df[df["source"].isin(selected_sources)]

# Employee count filter
if min_employees > 0 and "employees" in df.columns:
    df = df[df["employees"].fillna(0) >= min_employees]

if df.empty:
    st.warning("Nessun risultato per i filtri selezionati.")
    st.stop()

# ---------- KPI ----------
col1, col2, col3, col4 = st.columns(4)
total_stories = len(df)
total_employees = int(df["employees"].fillna(0).sum())
unique_companies = df["company"].nunique()
last_30d = df[df["date"].dt.date >= datetime.now().date() - timedelta(days=30)]

col1.metric("Storie trovate", f"{total_stories:,}")
col2.metric("Dipendenti tracciati", f"{total_employees:,}", help="Somma dei conteggi estratti dai titoli — sottostima")
col3.metric("Aziende uniche", f"{unique_companies:,}")
col4.metric("Ultimi 30 giorni", f"{len(last_30d):,}")

# ---------- CHARTS ----------
st.subheader("📊 Trend temporale")

df_chart = df.copy()
df_chart["date"] = pd.to_datetime(df_chart["date"])
weekly = (
    df_chart.set_index("date")
    .resample("W")
    .agg(stories=("title", "count"), employees=("employees", "sum"))
    .fillna(0)
)

tab1, tab2 = st.tabs(["Storie/settimana", "Dipendenti/settimana"])
with tab1:
    st.bar_chart(weekly["stories"], use_container_width=True)
with tab2:
    st.bar_chart(weekly["employees"], use_container_width=True)

# ---------- TOP COMPANIES ----------
st.subheader("🏢 Top aziende per dipendenti coinvolti")
top_companies = (
    df.dropna(subset=["employees"])
    .groupby("company", as_index=False)["employees"]
    .sum()
    .sort_values("employees", ascending=False)
    .head(15)
)
if not top_companies.empty:
    st.bar_chart(top_companies.set_index("company"), use_container_width=True)
else:
    st.info("Nessun dato sui dipendenti estraibile dai titoli per questo filtro.")

# ---------- TABLE ----------
st.subheader("📰 Tutte le storie")

df_display = df.copy()
df_display["employees"] = df_display["employees"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "—")
df_display["percent_workforce"] = df_display["percent_workforce"].apply(
    lambda x: f"{x:.1f}%" if pd.notna(x) else "—"
)

# Format dual scores with labels
def format_certainty(score):
    if pd.isna(score):
        return "—"
    score = int(score)
    labels = {1: "🔴 Unverif", 2: "🟡 HN/News", 3: "🟠 TechCrunch", 4: "🟢 Reuters", 5: "🟢🟢 SEC"}
    return f"{score} {labels.get(score, '')}"

def format_causality(score):
    if pd.isna(score):
        return "—"
    score = int(score)
    labels = {1: "⚪ Co-occur", 2: "🔵 Mentioned", 3: "🟣 Media attr", 4: "🟠 Challenger", 5: "🔴 Statement"}
    return f"{score} {labels.get(score, '')}"

df_display["certainty"] = df_display.get("layoff_certainty", 0).apply(format_certainty)
df_display["causality"] = df_display.get("ai_causality", 0).apply(format_causality)

st.dataframe(
    df_display[["date", "source", "company", "certainty", "causality", "title", "employees", "percent_workforce", "url", "hn_discussion"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "url": st.column_config.LinkColumn("Articolo"),
        "hn_discussion": st.column_config.LinkColumn("HN"),
        "date": st.column_config.DateColumn("Data"),
        "certainty": st.column_config.TextColumn("Certainty", help="1-5: data source credibility"),
        "causality": st.column_config.TextColumn("AI Causality", help="1-5: AI cause evidence"),
        "source": st.column_config.TextColumn("Fonte"),
    },
)

# ---------- EXPORT ----------
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "💾 Scarica CSV",
    data=csv,
    file_name=f"layoffs_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
)

st.markdown("---")
st.caption(
    "Built with Streamlit • Data: Hacker News Algolia API • "
    "Codice opensource, nessuna API key richiesta."
)
