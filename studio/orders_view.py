"""Production entry, searchable cards, status management and confirmations."""

from html import escape

import pandas as pd
import streamlit as st

from studio.storage import ORDER_STATUSES, PRODUCTS, CsvStore, StorageError
from studio.ui import empty_state, money, number, section, status_badge


def csv_export(frame: pd.DataFrame) -> bytes:
    """Neutralize spreadsheet formulas in downloads without altering stored data."""
    safe = frame.copy()
    for column in safe.select_dtypes(include=["object", "string"]).columns:
        safe[column] = safe[column].map(
            lambda value: "'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else value
        )
    return safe.to_csv(index=False).encode("utf-8-sig")


def flash(message: str) -> None:
    st.session_state["flash"] = message
    st.rerun()


def order_card(store: CsvStore, row: pd.Series) -> None:
    oid = row["id"]
    initials = "".join(word[0] for word in row["client"].split()[:2]).upper()
    with st.container(border=True):
        st.markdown(
            f'<div class="order-head"><div class="avatar">{escape(initials)}</div><div>'
            f'<div class="order-client">{escape(row["client"])}</div>'
            f'<div class="order-meta">#{escape(oid[:8].upper())} · {row["created_at"]:%d.%m.%Y}</div></div></div>'
            f'<div class="order-meta">{escape(row["product"])} · {number(row["quantity"])} szt. · {number(row["stitches"])} wkłuć / szt.</div>'
            f'<div class="order-summary"><div class="order-amount">{money(row["net_amount"], False)} <small>zł netto</small></div>{status_badge(row["status"])}</div>'
            f'<div class="order-meta">Dokument: {escape(row["document"])}</div>', unsafe_allow_html=True,
        )
        with st.expander("Zarządzaj zleceniem"):
            status = st.selectbox("Status zlecenia", ORDER_STATUSES, index=ORDER_STATUSES.index(row["status"]), key=f"status_{oid}")
            if st.button("Zapisz status", key=f"save_{oid}", width="stretch"):
                try:
                    if store.update_order_status(oid, status):
                        flash("Status zlecenia został zaktualizowany.")
                    else:
                        st.warning("To zlecenie zostało już usunięte. Odśwież listę.")
                except (StorageError, ValueError) as exc:
                    st.error(str(exc))
            confirmed = st.checkbox("Potwierdzam usunięcie", key=f"confirm_{oid}")
            if st.button("Usuń zlecenie", key=f"delete_{oid}", disabled=not confirmed, width="stretch"):
                try:
                    if store.delete_order(oid):
                        flash("Zlecenie zostało usunięte.")
                    else:
                        st.warning("Zlecenie nie istnieje. Odśwież listę.")
                except StorageError as exc:
                    st.error(str(exc))


def render_orders(store: CsvStore, orders: pd.DataFrame) -> None:
    form_col, info = st.columns([2.1, 1], gap="large")
    with form_col:
        with st.form("new_order", clear_on_submit=True):
            section("Nowe zlecenie", "Szczegóły produkcji w jednym miejscu", "PRODUKCJA")
            client = st.text_input("Nazwa klienta", placeholder="np. Studio Forma", max_chars=200)
            left, right = st.columns(2)
            with left:
                product = st.selectbox("Typ produktu", PRODUCTS)
                quantity = st.number_input("Ilość sztuk", min_value=1, max_value=1_000_000, value=10, step=1)
                amount = st.number_input("Kwota netto całego zlecenia (zł)", min_value=0.0, max_value=100_000_000.0, value=0.0, step=10.0, format="%.2f")
            with right:
                status = st.selectbox("Status zlecenia", ORDER_STATUSES)
                stitches = st.number_input("Szacowane wkłucia na sztukę", min_value=0, max_value=100_000_000, value=12000, step=1000)
                invoice = st.toggle("Faktura VAT (FV)", value=True, help="Wyłącz, aby wybrać paragon. To oznaczenie dokumentu, a nie wystawianie faktury.")
                st.caption("FV" if invoice else "Paragon")
            submitted = st.form_submit_button("Dodaj zlecenie", type="primary", width="stretch")
            if submitted:
                try:
                    oid = store.add_order(client=client, product=product, quantity=quantity, stitches=stitches, net_amount=amount, status=status, document="FV" if invoice else "Paragon")
                    flash(f"Zlecenie #{oid[:8].upper()} zostało zapisane.")
                except (ValueError, StorageError) as exc:
                    st.error(str(exc))
    with info, st.container(border=True):
        section("Małe detale. Duży porządek.", "Twój proces produkcji")
        st.markdown("**01 · Dodaj zlecenie**")
        st.caption("Zapisz klienta, produkt i łączną wartość netto. ID i data dodadzą się automatycznie.")
        st.markdown("**02 · Aktualizuj status**")
        st.caption("W kartach poniżej przeprowadzisz zlecenie przez kolejne etapy produkcji.")
        st.markdown("**03 · Zobacz wyniki**")
        st.caption("Status „Zrealizowane” uwzględnia zlecenie w przychodach i strukturze sprzedaży.")
        st.markdown('<div class="info-box">Nie masz jeszcze ceny? Skorzystaj z kalkulatora wyceny w menu po lewej.</div>', unsafe_allow_html=True)

    st.write("")
    section("Twoje zlecenia", "Wyszukuj klientów i zarządzaj kolejnymi etapami", f"{len(orders)} ZLECEŃ")
    search_col, status_col, limit_col = st.columns([2, 1.2, .7])
    search = search_col.text_input("Szukaj klienta lub ID", placeholder="Wyszukaj klienta lub numer zlecenia…", label_visibility="collapsed")
    status_filter = status_col.selectbox("Filtr statusu", ["Wszystkie statusy", *ORDER_STATUSES], label_visibility="collapsed")
    limit = limit_col.selectbox("Liczba kart", [9, 18, 36, 90], label_visibility="collapsed")
    filtered = orders
    if search.strip():
        filtered = filtered.loc[filtered["client"].str.contains(search.strip(), case=False, regex=False) | filtered["id"].str.contains(search.strip(), case=False, regex=False)]
    if status_filter != "Wszystkie statusy":
        filtered = filtered.loc[filtered["status"].eq(status_filter)]
    filtered = filtered.sort_values("created_at", ascending=False)
    if filtered.empty:
        with st.container(border=True):
            empty_state("Jeszcze jeden ścieg do porządku", "Dodaj pierwsze zlecenie lub zmień filtry wyszukiwania.", "+")
    else:
        rows = list(filtered.head(limit).iterrows())
        for offset in range(0, len(rows), 3):
            columns = st.columns(3, gap="medium")
            for column, (_, row) in zip(columns, rows[offset:offset + 3]):
                with column:
                    order_card(store, row)
        st.caption(f"Wyświetlono {min(limit, len(filtered))} z {len(filtered)} zleceń pasujących do filtrów.")
    st.download_button("Eksportuj zlecenia CSV", csv_export(filtered), file_name="hft_zlecenia.csv", mime="text/csv", icon=":material/download:")
