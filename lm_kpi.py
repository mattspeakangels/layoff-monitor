"""
lm_kpi.py — KPI card con sparkline SVG per Layoff AI Monitor

Usa st.markdown() con HTML unsafe per replicare i KPI card del mockup,
incluse le sparkline animate SVG (nessuna dipendenza extra richiesta).

Uso:
    from lm_kpi import kpi_row

    data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8]  # 12 valori settimanali
    kpi_row([
        {"label": "Storie trovate",       "value": "142",     "sub": "ultimi 90gg",     "spark": data},
        {"label": "Dipendenti tracciati", "value": "287.441", "sub": "totale stimato",  "spark": data},
        {"label": "Aziende uniche",       "value": "38",      "sub": "aziende coinvolte","spark": data},
        {"label": "Ultimi 30 giorni",     "value": "12",      "sub": "storie recenti",  "spark": data},
    ], accent="#3a7bd5", variant="signal", theme="dark")
"""

import streamlit as st
from lm_style import VARIANTS, COLORS


def _sparkline_svg(data: list, color: str, width: int = 84, height: int = 28) -> str:
    """Genera un SVG sparkline inline da una lista di valori."""
    if not data or all(v == 0 for v in data):
        return (
            f'<svg width="{width}" height="{height}">'
            f'<line x1="0" y1="{height//2}" x2="{width}" y2="{height//2}" '
            f'stroke="{color}" stroke-opacity="0.3" stroke-width="1" stroke-dasharray="3 3"/>'
            f'</svg>'
        )

    min_v = min(data)
    max_v = max(data)
    range_v = max_v - min_v or 1
    pad = 3
    n = len(data)

    pts = [
        (
            round(i / (n - 1) * width, 1),
            round(height - pad - ((v - min_v) / range_v) * (height - 2 * pad), 1),
        )
        for i, v in enumerate(data)
    ]

    # Smooth cubic bezier path
    def smooth_path(pts_list):
        d = f"M {pts_list[0][0]},{pts_list[0][1]}"
        for i in range(len(pts_list) - 1):
            dx = (pts_list[i + 1][0] - pts_list[i][0]) / 2.5
            cp1x = round(pts_list[i][0] + dx, 1)
            cp2x = round(pts_list[i + 1][0] - dx, 1)
            d += (f" C {cp1x},{pts_list[i][1]}"
                  f" {cp2x},{pts_list[i+1][1]}"
                  f" {pts_list[i+1][0]},{pts_list[i+1][1]}")
        return d

    line_d = smooth_path(pts)
    area_d = (
        f"M 0,{height} L "
        + " L ".join(f"{x},{y}" for x, y in pts)
        + f" L {width},{height} Z"
    )

    grad_id = f"sg_{abs(hash(str(data[:4]))) % 99999}"

    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="overflow:visible">'
        f'<defs><linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0.45"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f'</linearGradient></defs>'
        f'<path d="{area_d}" fill="url(#{grad_id})"/>'
        f'<path d="{line_d}" fill="none" stroke="{color}" stroke-width="1.5" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle cx="{pts[-1][0]}" cy="{pts[-1][1]}" r="2.5" fill="{color}"/>'
        f'</svg>'
    )


def kpi_card_html(
    label:   str,
    value:   str,
    sub:     str,
    spark:   list,
    accent:  str  = "#3a7bd5",
    variant: str  = "signal",
    theme:   str  = "dark",
    tooltip: str  = "",
) -> str:
    """Restituisce l'HTML di un singolo KPI card (usa con st.markdown unsafe).

    Lo style del wrapper è collassato su una sola riga: placeholder vuoti
    (es. left_border con variant != 'signal') lasciavano linee bianche dentro
    style="…" e il parser markdown di Streamlit chiudeva il blocco HTML lì,
    mostrando il resto come testo.
    """
    v = VARIANTS.get(variant, VARIANTS["signal"])
    c = COLORS.get(theme, COLORS["dark"])
    svg = _sparkline_svg(spark, accent)

    if variant == "pulse":
        card_bg = f"background: color-mix(in srgb, {accent} 5%, {c['card']})"
    else:
        card_bg = f"background: {c['card']}"

    style_parts = [card_bg]
    if variant == "signal":
        style_parts.append(f"border-left: 2px solid {accent}")
    style_parts += [
        f"border: 1px solid {c['border']}",
        f"border-radius: {v['radius']}",
        "padding: 14px 16px",
        "display: grid",
        "grid-template-areas: 'lbl sp' 'val val' 'sub sub'",
        "grid-template-columns: 1fr auto",
        "gap: 4px 8px",
        "transition: background 0.15s",
    ]
    wrapper_style = "; ".join(style_parts)

    label_style = (
        f"grid-area:lbl; font-size:11px; font-weight:600; text-transform:uppercase; "
        f"letter-spacing:0.6px; color:{c['text2']}; align-self:center;"
    )
    val_style = (
        f"grid-area:val; font-family:{v['kpi_font']}; font-size:{v['kpi_size']}; "
        f"font-weight:700; color:{c['text1']}; line-height:1.1; "
        f"letter-spacing:-0.5px; margin-top:4px;"
    )
    sub_style = f"grid-area:sub; font-size:11px; color:{c['text3']};"

    return (
        f'<div title="{tooltip}" style="{wrapper_style}">'
        f'<div style="{label_style}">{label}</div>'
        f'<div style="grid-area:sp; align-self:center;">{svg}</div>'
        f'<div style="{val_style}">{value}</div>'
        f'<div style="{sub_style}">{sub}</div>'
        f'</div>'
    )


def kpi_row(
    cards:   list,
    accent:  str = "#3a7bd5",
    variant: str = "signal",
    theme:   str = "dark",
) -> None:
    """
    Renderizza una riga di KPI card in st.columns.

    Args:
        cards: lista di dict con chiavi: label, value, sub, spark, tooltip (opz.)
        accent, variant, theme: stile
    """
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            html = kpi_card_html(
                label   = card["label"],
                value   = str(card["value"]),
                sub     = card.get("sub", ""),
                spark   = card.get("spark", [0] * 12),
                accent  = accent,
                variant = variant,
                theme   = theme,
                tooltip = card.get("tooltip", ""),
            )
            st.markdown(html, unsafe_allow_html=True)
