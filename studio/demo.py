"""Deterministic, disposable examples. This module never writes business data."""

from __future__ import annotations

from datetime import date
from random import Random

import pandas as pd


def demo_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return six months of realistic sample work and recent active orders."""
    rng = Random(42)
    today = pd.Timestamp(date.today())
    products = ["T-shirt", "Bluza", "Polo", "Czapka", "Torba", "Odzież robocza"]
    unit_prices = [42, 105, 68, 34, 29, 92]
    clients = [
        "Kawiarnia Splot", "Studio Forma", "Hotel Brzoza", "Pracownia Maki",
        "Fundacja Dobre Rzeczy", "Bistro Sezon", "Klub Biegowy Północ",
        "Architekci Nowak", "Piekarnia Okruch", "Restauracja Zielnik",
    ]
    orders: list[dict] = []
    for month_index in range(6):
        month = today.replace(day=1) - pd.DateOffset(months=5 - month_index)
        for index in range(6):
            product_index = (month_index + index) % len(products)
            day_limit = today.day if month_index == 5 else month.days_in_month
            day = min(3 + index * 5, day_limit)
            quantity = rng.randint(8, 26) + month_index * 3
            orders.append({
                "id": f"demo-order-{month_index:02}-{index:02}",
                "created_at": month.replace(day=day) + pd.Timedelta(hours=10 + index),
                "client": clients[(month_index * 2 + index) % len(clients)],
                "product": products[product_index],
                "quantity": quantity,
                "stitches": rng.choice([4500, 8000, 12000, 18000]),
                "net_amount": round(quantity * unit_prices[product_index], 2),
                "status": "Zrealizowane",
                "document": "Paragon" if index == 4 else "FV",
            })
    for index, status in enumerate(["Nowe", "W produkcji", "Gotowe", "W produkcji", "Nowe"]):
        product_index = index % len(products)
        quantity = [24, 60, 18, 40, 12][index]
        orders.append({
            "id": f"demo-active-{index:02}",
            "created_at": today - pd.Timedelta(days=index) + pd.Timedelta(hours=9),
            "client": clients[(index + 3) % len(clients)],
            "product": products[product_index],
            "quantity": quantity,
            "stitches": 8500 + index * 1200,
            "net_amount": float(quantity * unit_prices[product_index]),
            "status": status,
            "document": "FV",
        })

    category_rows = [
        ("Odzież i materiały", "Cotton Supply", 2350),
        ("Nici i akcesoria", "Madeira Polska", 410),
        ("Media i lokal", "Pracownia • czynsz i energia", 1250),
        ("Marketing", "Materiały promocyjne", 240),
        ("Transport", "Dostawy kurierskie", 180),
    ]
    expenses: list[dict] = []
    for month_index in range(6):
        month = today.replace(day=1) - pd.DateOffset(months=5 - month_index)
        for index, (category, supplier, base_amount) in enumerate(category_rows):
            day_limit = today.day if month_index == 5 else month.days_in_month
            expenses.append({
                "id": f"demo-expense-{month_index:02}-{index:02}",
                "created_at": month.replace(day=min(2 + index * 4, day_limit)) + pd.Timedelta(hours=8),
                "category": category,
                "supplier": supplier,
                "gross_amount": round(base_amount * (1 + rng.uniform(-0.12, 0.12)), 2),
            })
    return pd.DataFrame(orders), pd.DataFrame(expenses)
