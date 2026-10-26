"""Shared visual language, safe HTML fragments and Plotly defaults."""

from html import escape

import plotly.graph_objects as go
import streamlit as st

PALETTE = ["#EBC080", "#8B9CF6", "#6CCDB1", "#73B8E8", "#D599BE", "#B7C497", "#B7A696"]

CSS = """
<style>
:root { --muted: #929BAD; --line: #272E3B; --gold: #EBC080; }
html, body, [class*="css"] { font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
.stApp { background: #0D1016; font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbarActions"], [data-testid="stAppDeployButton"] { display: none; }
[data-testid="stDecoration"], #MainMenu, footer { display: none; }
[data-testid="stMainBlockContainer"] { max-width: 1500px; padding: 2.3rem 3rem 3rem; }
[data-testid="stSidebar"] { background: #10141C; border-right: 1px solid #242B38; }
[data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 1rem; }
.brand { display: flex; gap: 12px; align-items: center; margin-bottom: 28px; }
.brand-mark { display: flex; align-items: center; justify-content: center; width: 44px; height: 44px;
 background: #EBC080; color: #242018; font-size: 20px; font-weight: 850; letter-spacing: -1.5px; border-radius: 13px; }
.brand-name { font-size: 17px; font-weight: 700; letter-spacing: -.4px; color: #F3F4F7; }
.brand-sub { color: #8993A6; font-size: 11px; margin-top: 2px; letter-spacing: 1.6px; text-transform: uppercase; }
.nav-label { color: #727F95; font-size: 10px; font-weight: 700; letter-spacing: 1.8px; margin: 10px 0 2px; }
[data-testid="stSidebar"] [role="radiogroup"] { gap: 7px; }
[data-testid="stSidebar"] [role="radiogroup"] label { width: 100%; padding: 12px 13px; margin: 0;
 border-radius: 10px; color: #A6AEBE; border: 1px solid transparent; transition: background .15s ease; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: #1A202B; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: #27251F; border-color: #49402F; color: #F3D4A1; }
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none; }
[data-testid="stSidebar"] [role="radiogroup"] label p { font-size: 13px; font-weight: 550; }
.workspace-card { border: 1px solid #2B3240; background: #161C26; border-radius: 12px; padding: 14px; margin-top: 26px; }
.workspace-card strong { font-size: 12px; display: block; margin-bottom: 6px; }
.workspace-card p { font-size: 11px; color: #8E9AAD; line-height: 1.7; margin: 0; }
.status-dot { display: inline-block; width: 6px; height: 6px; background: #6CCDB1; border-radius: 50%; margin-right: 6px; }
.sidebar-foot { font-size: 10px; color: #68768D; margin-top: 26px; letter-spacing: .7px; }
.eyebrow { color: #8A95AA; font-size: 10px; letter-spacing: 2px; font-weight: 650; text-transform: uppercase; margin-bottom: 8px; }
.stApp h1.page-title { font-size: clamp(26px, 3vw, 34px) !important; font-weight: 650; letter-spacing: -1.2px; line-height: 1.2; margin: 0 0 10px !important; padding: 0 !important; }
.stApp p.page-subtitle { color: #939DB0; font-size: 13px !important; line-height: 1.7; margin: 0 0 12px !important; }
.top-meta { text-align: right; padding-top: 8px; color: #A3ADC0; font-size: 12px; }
.top-meta span { display: block; font-size: 10px; color: #69768E; margin-top: 5px; text-transform: uppercase; letter-spacing: 1px; }
.metric-grid { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 16px; margin: 12px 0 22px; }
.metric-card { background: linear-gradient(135deg,#191F29,#141923); border: 1px solid #29303D; border-radius: 15px; padding: 19px 20px; min-height: 143px; }
.metric-card.featured { background: linear-gradient(135deg,#2D2A24,#1D1D1F); border-color: #514330; }
.metric-top { display: flex; align-items: center; justify-content: space-between; color: #A8B1C2; font-size: 12px; gap: 4px; }
.metric-icon { color: #B1BACA; border: 1px solid #343D4C; width: 28px; height: 28px; border-radius: 8px; display: grid; place-items: center; }
.featured .metric-icon { color: #EBC080; border-color: #574C3B; }
.metric-value { font-size: clamp(21px,2.4vw,30px); font-weight: 650; letter-spacing: -1px; margin: 13px 0 8px; white-space: nowrap; }
.metric-value small { color: #8996AB; font-size: 13px; letter-spacing: 0; font-weight: 450; }
.metric-detail { color: #92A0B6; font-size: 11px; line-height: 1.5; }
.metric-detail.positive { color: #80D5BA; }
.section-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.stApp h2.section-title { font-size: 16px !important; letter-spacing: -.3px; font-weight: 620; margin: 0 !important; padding: 0 !important; line-height: 1.6; }
.stApp p.section-caption { font-size: 12px !important; color: #95A1B5; margin: 3px 0 0 !important; line-height: 1.6; }
.section-head [data-testid="stHeaderActionElements"] { display: none; }
.section-chip { color: #8C99B0; padding: 5px 9px; border: 1px solid #2A3444; border-radius: 6px; font-size: 9px; white-space: nowrap; }
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"]:first-child .section-head),
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"]:first-child .order-head) {
 background: #131821; border: 1px solid #29303D; border-radius: 14px; padding: 19px;
}
[data-testid="stForm"] { background: #141923; border: 1px solid #29303D; border-radius: 14px; padding: 22px; }
[data-testid="stForm"] [data-testid="stVerticalBlock"] { background: transparent; border: 0; padding: 0; border-radius: 0; }
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button { margin-top: 8px; }
.stButton button, .stDownloadButton button, .stFormSubmitButton button { border-radius: 9px; font-size: 12px; min-height: 39px; }
button[kind="primary"], [data-testid="stBaseButton-primaryFormSubmit"] { font-weight: 650; color: #241E15; }
[data-testid="stWidgetLabel"] p { font-size: 12px; color: #B6BFCF; }
[data-baseweb="input"] input, [data-baseweb="select"] { font-size: 13px; }
[data-testid="stCaptionContainer"] p { font-size: 11px; color: #8895AA; line-height: 1.7; }
.order-head { display: flex; align-items: center; gap: 12px; margin-bottom: 13px; }
.avatar { width: 38px; height: 38px; border: 1px solid #3B3D4F; background: #252738; color: #B8BDF1; border-radius: 11px;
 display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 650; flex-shrink: 0; }
.order-client { font-size: 13px; font-weight: 600; color: #E2E7EF; line-height: 1.6; overflow-wrap: anywhere; }
.order-meta { font-size: 11px; color: #95A1B5; line-height: 1.7; }
.order-summary { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin: 12px 0; }
.order-amount { font-size: 20px; font-weight: 600; letter-spacing: -.6px; }
.order-amount small { font-size: 10px; color: #8895AA; font-weight: 450; }
.badge { display: inline-block; border-radius: 6px; padding: 4px 8px; font-size: 9px; font-weight: 550; white-space: nowrap; }
.badge-new { color: #A9BCFF; background: #232C47; }
.badge-production { color: #E9C282; background: #3D3222; }
.badge-ready { color: #BFAEEC; background: #30263F; }
.badge-done { color: #82D9B9; background: #1D3A33; }
.badge-cancelled { color: #ACB2BE; background: #2B303B; }
.empty-state { text-align: center; padding: 43px 15px; color: #8895AA; font-size: 12px; line-height: 1.8; }
.empty-state strong { display: block; color: #D7DEEA; font-size: 15px; font-weight: 550; margin: 12px 0 5px; }
.empty-symbol { margin: auto; width: 44px; height: 44px; display: grid; place-items: center; color: #D8B67D;
 border: 1px solid #4A4031; background: #24231F; border-radius: 13px; font-size: 20px; }
.price-card { padding: 28px 26px; border: 1px solid #5B4B32; border-radius: 16px; background: linear-gradient(140deg,#302A21,#191C23); }
.price-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1.7px; color: #C5AF8C; }
.price-number { font-size: 46px; font-weight: 650; letter-spacing: -2px; margin: 15px 0 3px; color: #F3D5A5; }
.price-number small { font-size: 16px; letter-spacing: 0; color: #B9A68A; }
.price-note { font-size: 11px; color: #9E9D9E; margin-bottom: 24px; line-height: 1.7; }
.price-row { display: flex; justify-content: space-between; gap: 10px; padding: 11px 0; border-top: 1px solid #39362F; font-size: 12px; color: #AAAEB7; }
.price-row strong { color: #DFE3EA; font-weight: 550; }
.info-box { color: #8F9DB2; font-size: 11px; border-left: 2px solid #4D526B; padding: 4px 12px; margin-top: 16px; line-height: 1.8; }
.table-label { color: #748199; text-transform: uppercase; letter-spacing: 1px; font-size: 9px; font-weight: 600; }
.footer-note { border-top: 1px solid #222A38; padding-top: 16px; margin-top: 24px; font-size: 10px; color: #64728B;
 display: flex; justify-content: space-between; gap: 12px; }
@media (max-width: 1000px) {
 [data-testid="stMainBlockContainer"] { padding: 2rem 1.5rem; }
 .metric-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }
 .metric-value { font-size: 26px; }
}
@media (max-width: 640px) {
 [data-testid="stMainBlockContainer"] { padding: 2rem 1rem; }
 .metric-grid { gap: 9px; }
 .metric-card { padding: 14px; min-height: 130px; }
 .metric-value { font-size: 22px; }
 .top-meta { display: none; }
 .price-number { font-size: 38px; }
}
</style>
"""


def inject_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def money(value: float, currency: bool = True) -> str:
    text = f"{float(value):,.2f}".replace(",", " ").replace(".", ",")
    return text + (" zł" if currency else "")


def number(value: float) -> str:
    return f"{int(value):,}".replace(",", " ")


def section(title: str, caption: str = "", chip: str = "") -> None:
    st.markdown(
        f'<div class="section-head"><div><h2 class="section-title">{escape(title)}</h2>'
        f'<p class="section-caption">{escape(caption)}</p></div>'
        + (f'<span class="section-chip">{escape(chip)}</span>' if chip else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def empty_state(title: str, text: str, symbol: str = "↗") -> None:
    st.markdown(
        f'<div class="empty-state"><div class="empty-symbol">{escape(symbol)}</div>'
        f'<strong>{escape(title)}</strong>{escape(text)}</div>',
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    style = {
        "Nowe": "new", "W produkcji": "production", "Gotowe": "ready",
        "Zrealizowane": "done", "Anulowane": "cancelled",
    }.get(status, "new")
    return f'<span class="badge badge-{style}">{escape(status)}</span>'


def kpi_cards(stats: dict) -> None:
    cards = [
        ("Przychód netto", money(stats["revenue"], False), "PLN", "Zrealizowane zlecenia", "↗", True),
        ("Wydatki brutto", money(stats["expenses"], False), "PLN", "Zaksięgowane koszty", "↘", False),
        ("Czysty zysk*", money(stats["profit"], False), "PLN", "Przychód netto − wydatki brutto", "◎", False),
        ("Zlecenia w toku", str(stats["in_progress"]), "zleceń", "Nowe · w produkcji · gotowe", "▤", False),
    ]
    html = '<div class="metric-grid">'
    for label, value, unit, detail, icon, featured in cards:
        html += (
            f'<div class="metric-card {"featured" if featured else ""}">'
            f'<div class="metric-top">{label}<span class="metric-icon">{icon}</span></div>'
            f'<div class="metric-value">{value} <small>{unit}</small></div>'
            f'<div class="metric-detail">{detail}</div></div>'
        )
    st.markdown(html + "</div>", unsafe_allow_html=True)


def chart_layout(fig: go.Figure, height: int = 285) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=0, r=10, t=14, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color="#8F9CB1", size=10),
        colorway=PALETTE, separators=", ",
        hoverlabel=dict(bgcolor="#242B38", bordercolor="#3A4455", font_color="#F0F2F7"),
        legend=dict(orientation="h", y=-.17, x=0, font_size=10),
        xaxis=dict(showgrid=False, zeroline=False, tickfont_size=10),
        yaxis=dict(gridcolor="#252D3A", zeroline=False, tickfont_size=10),
    )
    return fig


def show_chart(fig: go.Figure, key: str) -> None:
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)
