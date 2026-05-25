"""
lm_cards.py — Vista a card per le notizie di layoff, con fonte URL ben visibile.

Uso:
    from lm_cards import news_cards
    news_cards(df, accent="#3a7bd5", variant="signal", theme="dark", per_page=20)

Ogni card mostra: azienda + scores in header, titolo, dipendenti/%,
dominio fonte cliccabile, eventuale link HN, data + nome fonte.
"""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

from lm_style import VARIANTS, COLORS


CERT_EMOJI = {1: "🔴", 2: "🟠", 3: "🟡", 4: "🟢", 5: "✅"}
AI_EMOJI = {1: "⚪", 2: "🔵", 3: "🟡", 4: "🟠", 5: "🔴"}


def _domain(url: str) -> str:
    """Estrae il dominio da un URL (senza www. e senza schema)."""
    if not url or not isinstance(url, str):
        return ""
    try:
        d = urlparse(url).netloc
        return d[4:] if d.startswith("www.") else d
    except Exception:
        return ""


def _fmt_date(d) -> str:
    """Formatta una data come '12 mag 2025'."""
    if pd.isna(d):
        return "—"
    try:
        if isinstance(d, str):
            d = pd.to_datetime(d)
        months_it = ["gen", "feb", "mar", "apr", "mag", "giu",
                     "lug", "ago", "set", "ott", "nov", "dic"]
        return f"{d.day} {months_it[d.month - 1]} {d.year}"
    except Exception:
        return str(d)


def _fmt_num(n) -> str:
    """Formatta numero con punto come separatore migliaia (it_IT)."""
    if pd.isna(n) or n is None:
        return ""
    try:
        return f"{int(n):,}".replace(",", ".")
    except Exception:
        return str(n)


def news_card_html(
    row: dict,
    accent: str = "#3a7bd5",
    variant: str = "signal",
    theme: str = "dark",
) -> str:
    """Restituisce l'HTML di una singola card notizia."""
    v = VARIANTS.get(variant, VARIANTS["signal"])
    c = COLORS.get(theme, COLORS["dark"])

    company = (row.get("company") or "—").upper()
    title = row.get("title") or ""
    source = row.get("source") or "—"
    url = row.get("url") or ""
    hn_url = row.get("hn_discussion") or ""
    date = row.get("date")
    employees = row.get("employees")
    pct = row.get("percent_workforce")
    cert = row.get("layoff_certainty")
    ai_caus = row.get("ai_causality")
    ai_cause = row.get("ai_cause") or "—"

    domain = _domain(url) or "fonte n/d"
    date_str = _fmt_date(date)

    # Scores con emoji
    cert_str = (
        f"{CERT_EMOJI.get(int(cert), '·')} {int(cert)}"
        if pd.notna(cert) else "—"
    )
    ai_str = (
        f"{AI_EMOJI.get(int(ai_caus), '·')} {int(ai_caus)}"
        if pd.notna(ai_caus) else "—"
    )

    # Stats line (dipendenti + %)
    stats_bits = []
    emp_str = _fmt_num(employees)
    if emp_str:
        stats_bits.append(f"<b style='color:{c['text1']}'>{emp_str}</b> dipendenti")
    if pd.notna(pct):
        stats_bits.append(f"<b style='color:{c['text1']}'>{pct:.1f}%</b> workforce")
    stats_html = " · ".join(stats_bits) if stats_bits else \
        f"<span style='color:{c['text3']}'>numero dipendenti non estratto dal titolo</span>"

    # Variante stylistic touches
    left_border = f"border-left: 2px solid {accent};" if variant == "signal" else ""
    card_bg = (
        f"background: color-mix(in srgb, {accent} 5%, {c['card']});"
        if variant == "pulse" else
        f"background: {c['card']};"
    )

    # ai_cause badge
    ai_cause_colors = {
        "high": c["red"],
        "medium": c["amber"],
        "low": c["text3"],
        "unknown": c["text3"],
    }
    badge_color = ai_cause_colors.get(ai_cause, c["text3"])
    ai_cause_badge = (
        f'<span style="font-size:9px; font-weight:600; text-transform:uppercase; '
        f'letter-spacing:0.6px; color:{badge_color}; border:1px solid {badge_color}; '
        f'padding:2px 6px; border-radius:3px;">AI cause: {ai_cause}</span>'
    )

    # Source link (dominio cliccabile)
    if url:
        source_link = (
            f'<a href="{url}" target="_blank" rel="noopener" '
            f'style="color:{accent}; text-decoration:none; font-weight:600; '
            f'font-family: \'DM Mono\', monospace; font-size:12px;">'
            f'🔗 {domain}</a>'
        )
    else:
        source_link = f'<span style="color:{c["text3"]}; font-size:12px;">🔗 fonte n/d</span>'

    # HN link (opzionale)
    hn_link = ""
    if hn_url:
        hn_link = (
            f' · <a href="{hn_url}" target="_blank" rel="noopener" '
            f'style="color:{c["text2"]}; text-decoration:none; font-size:12px;">'
            f'💬 HN discussion</a>'
        )

    return f"""
<div style="
    {card_bg}
    {left_border}
    border: 1px solid {c['border']};
    border-radius: {v['radius']};
    padding: 16px 18px;
    margin-bottom: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    transition: background 0.15s, border-color 0.15s;
">
  <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap;">
    <div style="
      font-family: 'Space Grotesk', sans-serif;
      font-size: 14px; font-weight: 700;
      color: {c['text1']}; letter-spacing: -0.3px;
    ">{company}</div>
    <div style="display:flex; gap:10px; align-items:center; font-size:11px; color:{c['text2']};
                font-family: 'DM Mono', monospace;">
      <span title="Layoff Certainty (1-5)">Cert {cert_str}</span>
      <span title="AI Causality (1-5)">AI→ {ai_str}</span>
      {ai_cause_badge}
    </div>
  </div>

  <div style="font-size:14px; line-height:1.45; color:{c['text1']}; font-weight:500;">
    {title}
  </div>

  <div style="font-size:12px; color:{c['text2']};">
    {stats_html}
  </div>

  <div style="
    padding-top: 8px;
    border-top: 1px solid {c['border']};
    display: flex; align-items: center; justify-content: space-between;
    gap: 12px; flex-wrap: wrap;
  ">
    <div>{source_link}{hn_link}</div>
    <div style="font-size:11px; color:{c['text3']}; font-family:'DM Mono', monospace;">
      📅 {date_str} · {source}
    </div>
  </div>
</div>"""


def news_cards(
    df: pd.DataFrame,
    accent: str = "#3a7bd5",
    variant: str = "signal",
    theme: str = "dark",
    per_page: int = 20,
    columns: int = 2,
    state_key: str = "news_page",
) -> None:
    """
    Renderizza una griglia di card notizie con paginazione.

    Args:
        df: DataFrame con colonne company, title, url, hn_discussion, date, source,
            employees, percent_workforce, layoff_certainty, ai_causality, ai_cause
        accent, variant, theme: stile (deve essere coerente con inject_css)
        per_page: card per pagina (default 20)
        columns: numero colonne griglia (default 2; 1 per layout stretto)
        state_key: chiave session_state per la paginazione (univoca per istanza)
    """
    if df.empty:
        st.info("Nessuna notizia con i filtri correnti.")
        return

    # Ordina per data desc per default
    df = df.sort_values("date", ascending=False).reset_index(drop=True)

    total = len(df)
    total_pages = max(1, (total + per_page - 1) // per_page)

    # Inizializza state
    if state_key not in st.session_state:
        st.session_state[state_key] = 0
    page = min(st.session_state[state_key], total_pages - 1)

    start = page * per_page
    end = min(start + per_page, total)
    df_page = df.iloc[start:end]

    # Render griglia
    if columns <= 1:
        for _, row in df_page.iterrows():
            st.markdown(
                news_card_html(row.to_dict(), accent=accent, variant=variant, theme=theme),
                unsafe_allow_html=True,
            )
    else:
        rows_list = df_page.to_dict("records")
        for i in range(0, len(rows_list), columns):
            cols = st.columns(columns)
            for j, col in enumerate(cols):
                if i + j < len(rows_list):
                    with col:
                        st.markdown(
                            news_card_html(rows_list[i + j], accent=accent,
                                           variant=variant, theme=theme),
                            unsafe_allow_html=True,
                        )

    # Paginazione
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("◀ Precedenti", disabled=(page == 0), key=f"{state_key}_prev",
                     width="stretch"):
            st.session_state[state_key] = max(0, page - 1)
            st.rerun()
    with c2:
        st.markdown(
            f"<div style='text-align:center; font-size:12px; color:#6b88a8; "
            f"font-family:DM Mono, monospace; padding-top:8px;'>"
            f"{start + 1}–{end} di {total} · pagina {page + 1}/{total_pages}"
            f"</div>",
            unsafe_allow_html=True,
        )
    with c3:
        if st.button("Successive ▶", disabled=(page >= total_pages - 1),
                     key=f"{state_key}_next", width="stretch"):
            st.session_state[state_key] = min(total_pages - 1, page + 1)
            st.rerun()
