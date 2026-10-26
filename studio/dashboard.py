"""Operational overview and interactive, date-filtered analytics."""

from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from studio.analytics import daily_revenue, filter_period, period_start, sold_products, summarize
from studio.ui import PALETTE, chart_layout, empty_state, kpi_cards, money, number, section, show_chart, status_badge


def render_dashboard(orders: pd.DataFrame, expenses: pd.DataFrame) -> None:
    period_col, note = st.columns([1.1, 2.3])
    with period_col:
        period = st.selectbox("Okres analizy", ["Cały okres", "Ten miesiąc", "Ten kwartał", "Ten rok"], label_visibility="collapsed")
    with note:
        st.caption("KPI w wybranym okresie · zlecenia według daty utworzenia")
    start = period_start(period)
    selected_orders = filter_period(orders, start)
    selected_expenses = filter_period(expenses, start)
    stats = summarize(selected_orders, selected_expenses)
    kpi_cards(stats)

    revenue_col, products_col = st.columns([1.75, 1], gap="medium")
    with revenue_col, st.container(border=True):
        revenue = daily_revenue(selected_orders)
        monthly = len(revenue) > 60
        section("Przychody w czasie", "Netto · tylko zrealizowane zlecenia", "MIESIĘCZNIE" if monthly else "DZIENNIE")
        if revenue.empty:
            empty_state("Tu pojawi się Twój pierwszy przychód", "Zrealizuj zlecenie, aby zobaczyć wyniki pracowni.")
        else:
            if monthly:
                revenue = revenue.set_index("date").resample("MS")["revenue"].sum().reset_index()
            fig = go.Figure(go.Scatter(
                x=revenue["date"], y=revenue["revenue"], mode="lines+markers",
                line=dict(color=PALETTE[0], width=2.5), marker=dict(size=5, color=PALETTE[0]),
                fill="tozeroy", fillcolor="rgba(235,192,128,0.09)",
                hovertemplate="%{x|%d.%m.%Y}<br><b>%{y:,.2f} zł netto</b><extra></extra>",
            ))
            chart_layout(fig, 285)
            fig.update_layout(hovermode="x unified")
            fig.update_xaxes(tickformat="%m.%Y" if monthly else "%d.%m", nticks=6)
            fig.update_yaxes(ticksuffix=" zł", rangemode="tozero", nticks=5)
            show_chart(fig, "revenue_chart")

    with products_col, st.container(border=True):
        section("Co sprzedajesz?", "Struktura zrealizowanej produkcji", "SZTUKI")
        products = sold_products(selected_orders)
        if products.empty:
            empty_state("Produkty czekają na swój wykres", "Udziały pojawią się po realizacji zleceń.", "◉")
        else:
            total = int(products["quantity"].sum())
            fig = go.Figure(go.Pie(
                labels=products["product"], values=products["quantity"], hole=.76,
                sort=False, textinfo="none", marker=dict(colors=PALETTE, line=dict(color="#151A23", width=4)),
                hovertemplate="<b>%{label}</b><br>%{value} szt. · %{percent}<extra></extra>",
            ))
            chart_layout(fig, 285)
            fig.update_layout(
                margin=dict(l=0, r=0, t=5, b=10),
                annotations=[dict(text=f'<b>{number(total)}</b><br><span style="font-size:10px;color:#8F9CB1">sprzedanych sztuk</span>',
                                  x=.5, y=.5, showarrow=False, font=dict(size=26, color="#EDF0F5"))],
                legend=dict(orientation="h", x=.5, xanchor="center", y=-.08, font_size=10),
            )
            show_chart(fig, "products_chart")

    st.caption("* Czysty zysk to uproszczony wynik: przychody netto minus wydatki brutto. Nie uwzględnia podatku dochodowego, rozliczenia VAT ani amortyzacji.")
    table, pipeline = st.columns([1.75, 1], gap="medium")
    with table, st.container(border=True):
        section("Ostatnie zlecenia", "Szybki wgląd w to, co dzieje się w pracowni", f"{len(orders)} ŁĄCZNIE")
        recent = orders.sort_values("created_at", ascending=False).head(5)
        if recent.empty:
            empty_state("Czas na pierwsze zlecenie", "Przejdź do produkcji i dodaj swojego pierwszego klienta.", "+")
        else:
            cols = st.columns([2.1, 1.4, 1.4, 1.1])
            for col, label in zip(cols, ["KLIENT / PRODUKT", "DATA", "STATUS", "NETTO"]):
                col.markdown(f'<span class="table-label">{label}</span>', unsafe_allow_html=True)
            for _, row in recent.iterrows():
                cols = st.columns([2.1, 1.4, 1.4, 1.1])
                cols[0].markdown(f'<div class="order-client">{escape(row["client"])}</div><div class="order-meta">{escape(row["product"])} · {number(row["quantity"])} szt.</div>', unsafe_allow_html=True)
                cols[1].caption(row["created_at"].strftime("%d.%m.%Y"))
                cols[2].markdown(status_badge(row["status"]), unsafe_allow_html=True)
                cols[3].markdown(f'<div class="order-client">{money(row["net_amount"])}</div>', unsafe_allow_html=True)
        if st.button("Przejdź do produkcji  →", key="open_orders", width="stretch"):
            st.session_state["navigate_to"] = "➕  Nowe Zlecenie"
            st.rerun()

    with pipeline, st.container(border=True):
        section("Rytm produkcji", "Bieżący stan wszystkich zleceń")
        for status in ["Nowe", "W produkcji", "Gotowe", "Zrealizowane"]:
            count = int(orders["status"].eq(status).sum())
            left, right = st.columns([3, 1])
            left.markdown(status_badge(status), unsafe_allow_html=True)
            right.markdown(f'<div style="text-align:right;color:#CCD4E1;font-size:13px">{count}</div>', unsafe_allow_html=True)
            st.progress(count / max(len(orders), 1))
        st.caption("Od pierwszego briefu do gotowego haftu. Każdy etap w jednym miejscu.")
