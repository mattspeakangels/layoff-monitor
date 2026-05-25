"""
lm_charts.py — Plotly chart templates per Layoff AI Monitor

Uso:
    from lm_charts import area_chart, hbar_chart
    st.plotly_chart(area_chart(data, labels, color="#3a7bd5"), use_container_width=True)
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── Tema base Plotly condiviso ────────────────────────────────────
def _base_layout(theme: str = "dark", title: str = "") -> dict:
    is_dark = theme == "dark"
    return dict(
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "rgba(0,0,0,0)",
        font          = dict(family="'DM Sans', sans-serif", color="#6b88a8" if is_dark else "#4a6282", size=11),
        title         = dict(text=title, font=dict(family="'Space Grotesk', sans-serif",
                             color="#e2ecf8" if is_dark else "#0d1526", size=14), x=0, pad=dict(l=0)),
        margin        = dict(l=40, r=12, t=40 if title else 20, b=36),
        showlegend    = False,
        hoverlabel    = dict(
            bgcolor   = "#1a2235" if is_dark else "#ffffff",
            bordercolor = "#1c2e48" if is_dark else "#dde3ed",
            font      = dict(family="'DM Sans', sans-serif", color="#e2ecf8" if is_dark else "#0d1526"),
        ),
        xaxis = dict(
            showgrid    = False,
            zeroline    = False,
            tickfont    = dict(size=9, color="#3d5a78" if is_dark else "#8ba3be"),
            linecolor   = "#1c2e48" if is_dark else "#dde3ed",
            tickcolor   = "#1c2e48" if is_dark else "#dde3ed",
        ),
        yaxis = dict(
            showgrid    = True,
            gridcolor   = "#1c2e48" if is_dark else "#e8eef5",
            gridwidth   = 0.5,
            zeroline    = False,
            tickfont    = dict(size=9, color="#3d5a78" if is_dark else "#8ba3be"),
            linecolor   = "rgba(0,0,0,0)",
        ),
    )


def area_chart(
    data:     list,
    labels:   list,
    color:    str  = "#3a7bd5",
    title:    str  = "",
    y_title:  str  = "",
    theme:    str  = "dark",
    variant:  str  = "signal",
    height:   int  = 220,
) -> go.Figure:
    """
    Area chart con gradiente verticale — replica del trend temporale del mockup.

    Args:
        data:    lista di valori numerici (settimanali)
        labels:  lista di etichette asse X (stessa lunghezza di data)
        color:   colore hex della linea e del fill
        title:   titolo opzionale del chart
        y_title: etichetta asse Y
        theme:   "dark" | "light"
        variant: "signal" | "pulse" | "radar" (cambia spessore linea e fill opacity)
        height:  altezza in pixel
    """
    area_opacity = {"signal": 0.20, "pulse": 0.38, "radar": 0.50}.get(variant, 0.30)
    line_width   = {"signal": 1.5,  "pulse": 2.5,  "radar": 3.0 }.get(variant, 2.0)

    # colore hex → rgba per fill
    hex_c = color.lstrip("#")
    r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
    fill_color_top = f"rgba({r},{g},{b},{area_opacity})"
    fill_color_bot = f"rgba({r},{g},{b},0)"

    fig = go.Figure()

    # Area fill (due trace sovrapposte per simulare gradiente verticale)
    fig.add_trace(go.Scatter(
        x=labels, y=data,
        fill="tozeroy",
        fillcolor=fill_color_top,
        line=dict(color="rgba(0,0,0,0)", width=0),
        hoverinfo="skip",
        showlegend=False,
    ))

    # Linea principale con hover
    fig.add_trace(go.Scatter(
        x=labels, y=data,
        mode="lines+markers",
        line=dict(color=color, width=line_width, shape="spline", smoothing=0.8),
        marker=dict(color=color, size=5 if len(data) <= 16 else 0,
                    line=dict(color=color, width=1)),
        hovertemplate=f"<b>%{{x}}</b><br>%{{y}}<extra></extra>",
        showlegend=False,
    ))

    layout = _base_layout(theme, title)
    if y_title:
        layout["yaxis"]["title"] = dict(text=y_title, font=dict(size=10))

    fig.update_layout(height=height, **layout)
    return fig


def hbar_chart(
    companies: list,
    color:     str = "#3a7bd5",
    title:     str = "Top aziende",
    theme:     str = "dark",
    variant:   str = "signal",
    height:    int = None,
) -> go.Figure:
    """
    Horizontal bar chart — replica del 'Top aziende per dipendenti coinvolti'.

    Args:
        companies: lista di dict [{"company": str, "employees": int}, ...]
        color:     colore hex delle barre
        title:     titolo del chart
        theme:     "dark" | "light"
        variant:   variante design
        height:    altezza auto se None (calcolata da numero di voci)
    """
    if not companies:
        return go.Figure()

    df = pd.DataFrame(companies).sort_values("employees", ascending=True)

    hex_c = color.lstrip("#")
    r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
    bar_color   = [f"rgba({r},{g},{b},{0.5 + 0.5 * (i / max(len(df)-1, 1)):.2f})"
                   for i in range(len(df))]
    bar_color[-1] = color  # barra più grande = colore pieno

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["employees"],
        y=df["company"],
        orientation="h",
        marker=dict(
            color=bar_color,
            line=dict(color="rgba(0,0,0,0)", width=0),
        ),
        text=[f"{v:,.0f}".replace(",", ".") for v in df["employees"]],
        textposition="outside",
        textfont=dict(family="'DM Mono', monospace", size=10,
                      color="#6b88a8" if theme == "dark" else "#4a6282"),
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} dipendenti<extra></extra>",
    ))

    auto_height = max(220, len(df) * 36 + 60)
    layout = _base_layout(theme, title)
    layout["xaxis"]["showgrid"] = True
    layout["xaxis"]["gridcolor"] = "#1c2e48" if theme == "dark" else "#e8eef5"
    layout["yaxis"]["showgrid"] = False
    layout["yaxis"]["tickfont"]["size"] = 11
    layout["margin"]["r"] = 60  # spazio per text labels

    fig.update_layout(height=height or auto_height, **layout)
    return fig


def sparkline_figure(
    data:   list,
    color:  str = "#3a7bd5",
    theme:  str = "dark",
) -> go.Figure:
    """
    Mini sparkline come figura Plotly (alternativa all'SVG inline).
    Usa con st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}).
    Altezza consigliata: 60px.
    """
    hex_c = color.lstrip("#")
    r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=data, mode="lines",
        fill="tozeroy",
        fillcolor=f"rgba({r},{g},{b},0.25)",
        line=dict(color=color, width=1.5, shape="spline", smoothing=0.8),
        hoverinfo="skip",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        height=50,
    )
    return fig
