"""Live, per-piece smart pricing workspace."""

from html import escape

import streamlit as st

from studio.pricing import estimate_price
from studio.ui import money, number, section


def render_pricing() -> None:
    inputs, quote = st.columns([1.25, 1], gap="large")
    with inputs:
        with st.container(border=True):
            section("Parametry haftu", "Wycena jednej sztuki. Zmieniaj parametry — wynik aktualizuje się na żywo.", "01 / KALKULACJA")
            a, b = st.columns(2)
            with a:
                stitches = st.number_input("Liczba wkłuć / szt.", min_value=0, max_value=10_000_000, value=12_000, step=1000, key="pricing_stitches")
                changes = st.number_input("Zmiany kolorów nici", min_value=0, max_value=100, value=3, step=1, key="pricing_changes", help="Liczba zmian koloru, nie liczba użytych kolorów.")
            with b:
                speed = st.number_input("Prędkość maszyny · wkłucia/min", min_value=1, max_value=1500, value=700, step=50, key="pricing_speed", help="Przyjmij realną średnią prędkość dla danego wzoru.")
                garment = st.number_input("Koszt odzieży netto · zł / szt.", min_value=0.0, max_value=100_000.0, value=25.0, step=1.0, format="%.2f", key="pricing_garment")
            margin = st.slider("Oczekiwana marża", min_value=0, max_value=90, value=35, step=1, format="%d%%", key="pricing_margin", help="Marża to udział zysku w cenie sprzedaży, a nie narzut na koszt.")
            with st.expander("Parametry pracowni"):
                a, b = st.columns(2)
                with a:
                    hourly = st.number_input("Stawka pracy maszyny · zł/h", min_value=0.0, max_value=10_000.0, value=90.0, step=5.0, format="%.2f", key="pricing_hourly", help="Uwzględnij pracę operatora, amortyzację i koszty stałe.")
                    change_seconds = st.number_input("Zmiana koloru · sekundy", min_value=0.0, max_value=3600.0, value=30.0, step=5.0, key="pricing_change_seconds")
                with b:
                    setup = st.number_input("Przygotowanie · min / szt.", min_value=0.0, max_value=600.0, value=5.0, step=0.5, key="pricing_setup", help="Np. założenie tamborka, pozycjonowanie i zdjęcie odzieży.")
                    materials = st.number_input("Nici i materiały · zł / szt.", min_value=0.0, max_value=100_000.0, value=1.5, step=0.5, format="%.2f", key="pricing_materials")
            st.caption("Dla serii rozdziel jednorazowe przygotowanie między sztuki. Kalkulacja nie uwzględnia rabatów, dostawy ani przygotowania programu hafciarskiego.")

    try:
        result = estimate_price(stitches, speed, changes, garment, margin, hourly_rate=hourly, setup_minutes=setup, color_change_seconds=change_seconds, material_cost=materials)
    except ValueError as exc:
        with quote:
            st.error(str(exc))
        return

    with quote:
        minutes = f"{result.production_minutes:.1f}".replace(".", ",")
        st.markdown(
            '<div class="price-card">'
            '<div class="price-label">Sugerowana cena netto</div>'
            f'<div class="price-number">{escape(money(result.suggested_price, False))} <small>zł / szt.</small></div>'
            '<div class="price-note">Cena orientacyjna dla klienta · bez podatku VAT</div>'
            f'<div class="price-row"><span>Szacowany czas produkcji</span><strong>{minutes} min</strong></div>'
            f'<div class="price-row"><span>Koszt własny</span><strong>{escape(money(result.total_cost))}</strong></div>'
            f'<div class="price-row"><span>Zysk na sztuce</span><strong>{escape(money(result.profit))}</strong></div>'
            f'<div class="price-row"><span>Marża w cenie sprzedaży</span><strong>{margin}%</strong></div>'
            '</div>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            section("Skąd ta cena?", "Przejrzysty koszt jednej sztuki")
            for label, value in (("Zakup odzieży", result.garment_cost), ("Praca maszyny i operatora", result.labor_cost), ("Nici i materiały pomocnicze", result.material_cost)):
                st.markdown(f'<div class="price-row"><span>{escape(label)}</span><strong>{escape(money(value))}</strong></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="info-box">'
            '<strong>Marża ≠ narzut.</strong> Cena = koszt własny ÷ (1 − marża / 100). '
            'Przy marży 35% każde 100 zł sprzedaży zawiera 35 zł zysku przed podatkami.</div>',
            unsafe_allow_html=True,
        )

    section("Założenia obliczeń", "Czas uwzględnia haft, przygotowanie i zmiany kolorów.")
    st.caption(
        f"Czas = {number(stitches)} wkłuć ÷ {number(speed)} wkłuć/min + {setup:g} min przygotowania "
        f"+ {changes} × {change_seconds:g} s ÷ 60 = {minutes} min. "
        f"Koszt pracy = czas ÷ 60 × {money(hourly)}/h. "
        "Koszt własny = praca + odzież + materiały. Wynik nie obejmuje VAT ani podatku dochodowego."
    )
