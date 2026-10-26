"""HFT Studio OS — a local-first workspace for a small embroidery studio."""

import os
from datetime import date
from pathlib import Path

import streamlit as st

from studio.dashboard import render_dashboard
from studio.expenses_view import render_expenses
from studio.orders_view import render_orders
from studio.pricing_view import render_pricing
from studio.storage import CsvStore, StorageError
from studio.ui import inject_styles

ROOT = Path(__file__).resolve().parent
PAGES = ["📊  Panel Główny", "➕  Nowe Zlecenie", "💸  Koszty & Wydatki", "⚙️  Kalkulator Wyceny"]
TITLES = {
    PAGES[0]: ("TWOJA PRACOWNIA W LICZBACH", "Wszystko pod kontrolą.", "Przychody, produkcja i koszty. Dobry dzień zaczyna się od jasnego obrazu."),
    PAGES[1]: ("CENTRUM PRODUKCJI", "Od pomysłu do ostatniego ściegu.", "Dodawaj zlecenia, śledź postęp i utrzymuj rytm swojej pracowni."),
    PAGES[2]: ("FINANSE PRACOWNI", "Każdy koszt ma swoje miejsce.", "Zapisuj wydatki i sprawdzaj, na co pracuje Twój budżet."),
    PAGES[3]: ("SMART PRICING", "Wyceniaj z pewnością.", "Zamień czas maszyny i koszty materiałów w cenę, która ma sens."),
}


def main() -> None:
    st.set_page_config(page_title="HFT Studio OS", page_icon="🧵", layout="wide", initial_sidebar_state="auto")
    inject_styles()
    try:
        store = CsvStore(os.getenv("HFT_DATA_DIR", str(ROOT / "data")))
        orders, expenses = store.orders(), store.expenses()
    except StorageError as exc:
        st.error(str(exc))
        st.info("Pliki źródłowe pozostają bez zmian. Przywróć poprawną kopię orders.csv lub expenses.csv, a następnie odśwież aplikację.")
        st.stop()

    if "navigate_to" in st.session_state:
        st.session_state["navigation"] = st.session_state.pop("navigate_to")

    with st.sidebar:
        st.markdown(
            '<div class="brand"><div class="brand-mark">hft.</div><div>'
            '<div class="brand-name">HFT Studio OS</div><div class="brand-sub">Embroidery workspace</div></div></div>'
            '<div class="nav-label">PRZESTRZEŃ ROBOCZA</div>', unsafe_allow_html=True,
        )
        page = st.radio("Nawigacja", PAGES, key="navigation", label_visibility="collapsed")
        st.markdown(
            '<div class="workspace-card"><strong><span class="status-dot"></span>Twoja pracownia</strong>'
            '<p>Zlecenia, koszty i wyceny.<br>Jedna przestrzeń. Pełen obraz.</p></div>'
            '<div class="sidebar-foot">HFT STUDIO OS &nbsp; / &nbsp; v1.0</div>', unsafe_allow_html=True,
        )

    header, meta = st.columns([4, 1])
    eyebrow, title, subtitle = TITLES[page]
    with header:
        st.markdown(f'<div class="eyebrow">{eyebrow}</div><h1 class="page-title">{title}</h1><p class="page-subtitle">{subtitle}</p>', unsafe_allow_html=True)
    with meta:
        st.markdown(f'<div class="top-meta">{date.today():%d.%m.%Y}<span>Przestrzeń właściciela</span></div>', unsafe_allow_html=True)

    if message := st.session_state.pop("flash", None):
        st.success(message)

    if page == PAGES[0]:
        render_dashboard(orders, expenses)
    elif page == PAGES[1]:
        render_orders(store, orders)
    elif page == PAGES[2]:
        render_expenses(store, expenses)
    else:
        render_pricing()

    st.markdown('<div class="footer-note"><span>HFT Studio OS · Zadbaj o detale. Resztę uporządkuj tutaj.</span><span>PLN / lokalny zapis CSV</span></div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
