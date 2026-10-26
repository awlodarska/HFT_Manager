"""Pure, defensive aggregations shared by the Streamlit dashboard."""

from __future__ import annotations

from datetime import date

import pandas as pd


def _column(frame: pd.DataFrame, name: str, default: object = None) -> pd.Series:
    return frame[name] if name in frame else pd.Series(default, index=frame.index)


def _numbers(frame: pd.DataFrame, name: str) -> pd.Series:
    return pd.to_numeric(_column(frame, name), errors="coerce").replace(
        [float("inf"), float("-inf")], 0
    ).fillna(0)


def _dates(frame: pd.DataFrame) -> pd.Series:
    # A common UTC representation also accepts a mixture of ISO timestamps
    # with and without offsets without failing the entire dashboard.
    return pd.to_datetime(
        _column(frame, "created_at"), errors="coerce", format="mixed", utc=True
    ).dt.tz_localize(None)


def _completed(orders: pd.DataFrame) -> pd.DataFrame:
    return orders.loc[_column(orders, "status").eq("Zrealizowane")].copy()


def period_start(label: str, today: date | None = None) -> pd.Timestamp | None:
    """Return an inclusive start for a supported dashboard period."""
    day = today or date.today()
    if label == "Cały okres":
        return None
    if label == "Ten miesiąc":
        return pd.Timestamp(day.replace(day=1))
    if label == "Ten kwartał":
        return pd.Timestamp(day.replace(month=((day.month - 1) // 3) * 3 + 1, day=1))
    if label == "Ten rok":
        return pd.Timestamp(day.replace(month=1, day=1))
    raise ValueError(f"Nieznany okres: {label}")


def filter_period(frame: pd.DataFrame, start: pd.Timestamp | None) -> pd.DataFrame:
    """Return a copy and exclude undated records from date-based reporting."""
    dates = _dates(frame)
    valid = dates.notna()
    if start is not None:
        start = pd.Timestamp(start)
        if start.tzinfo is not None:
            start = start.tz_convert("UTC").tz_localize(None)
        valid &= dates.ge(start)
    return frame.loc[valid].copy()


def summarize(orders: pd.DataFrame, expenses: pd.DataFrame) -> dict[str, float | int]:
    """Revenue is recognized only for completed orders; no tax claim is made."""
    completed = _completed(orders)
    revenue = float(_numbers(completed, "net_amount").sum())
    costs = float(_numbers(expenses, "gross_amount").sum())
    return {
        "revenue": revenue,
        "expenses": costs,
        "profit": revenue - costs,
        "in_progress": int(_column(orders, "status").isin(
            ["Nowe", "W produkcji", "Gotowe"]
        ).sum()),
        "completed": len(completed),
    }


def sold_products(orders: pd.DataFrame) -> pd.DataFrame:
    """Count sold units, rather than orders, by product."""
    completed = _completed(orders)
    if completed.empty:
        return pd.DataFrame(columns=["product", "quantity"])
    data = pd.DataFrame({
        "product": _column(completed, "product").fillna("Nieokreślony").replace("", "Nieokreślony"),
        "quantity": _numbers(completed, "quantity").clip(lower=0),
    })
    result = data.groupby("product", as_index=False)["quantity"].sum()
    return result.loc[result["quantity"].gt(0)].sort_values(
        "quantity", ascending=False, kind="stable"
    ).reset_index(drop=True)


def daily_revenue(orders: pd.DataFrame) -> pd.DataFrame:
    """Group completed sales by day. Missing days are explicit zero sales."""
    completed = _completed(orders)
    if completed.empty:
        return pd.DataFrame(columns=["date", "revenue"])
    data = pd.DataFrame({
        "date": _dates(completed).dt.normalize(),
        "revenue": _numbers(completed, "net_amount"),
    }).dropna(subset=["date"])
    if data.empty:
        return pd.DataFrame(columns=["date", "revenue"])
    grouped = data.groupby("date")["revenue"].sum().sort_index()
    grouped = grouped.reindex(pd.date_range(grouped.index.min(), grouped.index.max()), fill_value=0)
    return grouped.rename_axis("date").reset_index()


def expense_categories(expenses: pd.DataFrame) -> pd.DataFrame:
    if expenses.empty:
        return pd.DataFrame(columns=["category", "amount"])
    data = pd.DataFrame({
        "category": _column(expenses, "category").fillna("Inne").replace("", "Inne"),
        "amount": _numbers(expenses, "gross_amount"),
    })
    return data.groupby("category", as_index=False)["amount"].sum().sort_values(
        "amount", ascending=False, kind="stable"
    ).reset_index(drop=True)
