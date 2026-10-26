"""Expense ledger, category analysis and CSV export."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from studio.analytics import expense_categories, filter_period, period_start
from studio.orders_view import csv_export, flash
from studio.storage import COST_CATEGORIES, CsvStore, StorageError
from studio.ui import PALETTE, chart_layout, empty_state, money, section, show_chart


def render_expenses(store: CsvStore, expenses: pd.DataFrame, demo: bool) -> None:
    entry, chart = st.columns([1, 1.6], gap="large")
    with entry:
        with st.form("new_expense", clear_on_submit=True):
            section("Dodaj wydatek", "Kwoty zapisujemy w wartości brutto")
            category = st.selectbox("Kategoria", COST_CATEGORIES, disabled=demo)
            supplier = st.text_input("Dostawca", placeholder="np. Hurtownia Tkanin", max_chars=200, disabled=demo)
            amount = st.number_input("Kwota brutto (zł)", min_value=0.0, max_value=100_000_000.0, value=0.0, step=10.0, format="%.2f", disabled=demo)
            if st.form_submit_button("Zapisz wydatek", type="primary", use_container_width=True, disabled=demo):
                try:
                    store.add_expense(category=category, supplier=supplier, gross_amount=amount)
                    flash("Wydatek został zapisany.")
                except (ValueError, StorageError) as exc:
                    st.error(str(exc))
    with chart, st.container(border=True):
        section("Struktura wydatków", "Zobacz, gdzie trafiają pieniądze pracowni", "BRUTTO / PLN")
        period = st.selectbox("Okres wydatków", ["Cały okres", "Ten miesiąc", "Ten kwartał", "Ten rok"], key="expense_period", label_visibility="collapsed")
        selected = filter_period(expenses, period_start(period))
        grouped = expense_categories(selected)
        if grouped.empty or grouped["amount"].sum() == 0:
            empty_state("Budżet czeka na pierwsze dane", "Dodaj wydatek, aby porównać koszty w kategoriach.", "↘")
        else:
            fig = go.Figure(go.Bar(
                x=grouped["amount"], y=grouped["category"], orientation="h",
                marker=dict(color=[PALETTE[i % len(PALETTE)] for i in range(len(grouped))], cornerradius=5),
                width=.48, hovertemplate="%{y}<br><b>%{x:,.2f} zł brutto</b><extra></extra>",
            ))
            chart_layout(fig, 290)
            fig.update_layout(margin=dict(l=0, r=15, t=10, b=0))
            fig.update_yaxes(autorange="reversed", showgrid=False)
            fig.update_xaxes(showgrid=True, gridcolor="#252D3A", ticksuffix=" zł", nticks=4)
            show_chart(fig, "expenses_chart")
        st.caption(f"Łącznie w wybranym okresie: {money(selected['gross_amount'].sum())}")

    st.write("")
    with st.container(border=True):
        section("Rejestr kosztów", "Wszystkie wydatki · od najnowszych", f"{len(expenses)} WPISÓW")
        if expenses.empty:
            empty_state("Wszystko zaczyna się od pierwszego wpisu", "Wprowadź koszt odzieży, nici, serwisu lub utrzymania pracowni.", "+")
        else:
            ordered = expenses.sort_values("created_at", ascending=False)
            ledger = ordered[["created_at", "category", "supplier", "gross_amount", "id"]].copy()
            ledger["created_at"] = ledger["created_at"].dt.strftime("%d.%m.%Y %H:%M")
            ledger.columns = ["Data", "Kategoria", "Dostawca", "Kwota brutto (zł)", "ID"]
            st.dataframe(ledger, hide_index=True, width="stretch", column_config={"Kwota brutto (zł)": st.column_config.NumberColumn(format="%.2f zł")})
            with st.expander("Usuń błędny wpis"):
                ids = ordered["id"].tolist()
                labels = {row["id"]: f'{row["created_at"]:%d.%m.%Y} · {row["supplier"]} · {money(row["gross_amount"])} · #{row["id"][:8]}' for _, row in ordered.iterrows()}
                selected_id = st.selectbox("Wybierz wydatek", ids, format_func=labels.get, disabled=demo)
                confirmed = st.checkbox("Potwierdzam usunięcie wydatku", key=f"confirm_expense_{selected_id}", disabled=demo)
                if st.button("Usuń wydatek", disabled=demo or not confirmed):
                    try:
                        if store.delete_expense(selected_id):
                            flash("Wydatek został usunięty.")
                        else:
                            st.warning("Wydatek już nie istnieje. Odśwież listę.")
                    except StorageError as exc:
                        st.error(str(exc))
        st.download_button("Eksportuj koszty CSV", csv_export(expenses), file_name="hft_koszty_demo.csv" if demo else "hft_koszty.csv", mime="text/csv", icon=":material/download:")
