"""Transparent per-piece embroidery pricing with a true sales margin."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class PricingResult:
    production_minutes: float
    labor_cost: float
    material_cost: float
    garment_cost: float
    total_cost: float
    suggested_price: float
    profit: float


def _number(value: float, label: str, *, minimum: float = 0) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label}: podaj liczbę.")
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"{label}: podaj poprawną liczbę.") from exc
    if not isfinite(result) or result < minimum:
        raise ValueError(f"{label}: wartość musi być skończona i nie mniejsza niż {minimum}.")
    return result


def estimate_price(
    stitches: int,
    speed: int,
    color_changes: int,
    garment_cost: float,
    margin_percent: float,
    hourly_rate: float = 90,
    setup_minutes: float = 5,
    color_change_seconds: float = 30,
    material_cost: float = 1.5,
) -> PricingResult:
    """Estimate one piece, including setup and thread changes.

    Margin is profit / sales price, not markup on cost. Figures stay unrounded
    until presentation so the UI can explain the complete calculation.
    """
    stitches = _number(stitches, "Liczba wkłuć")
    speed = _number(speed, "Prędkość maszyny", minimum=1)
    color_changes = _number(color_changes, "Liczba zmian kolorów")
    if any(not value.is_integer() for value in (stitches, speed, color_changes)):
        raise ValueError("Wkłucia, prędkość i zmiany kolorów muszą być liczbami całkowitymi.")
    garment_cost = _number(garment_cost, "Koszt odzieży")
    hourly_rate = _number(hourly_rate, "Stawka godzinowa")
    setup_minutes = _number(setup_minutes, "Czas przygotowania")
    color_change_seconds = _number(color_change_seconds, "Czas zmiany koloru")
    material_cost = _number(material_cost, "Koszt materiałów")
    margin = _number(margin_percent, "Marża")
    if margin >= 100:
        raise ValueError("Marża musi być mniejsza niż 100%.")

    minutes = stitches / speed + setup_minutes + color_changes * color_change_seconds / 60
    labor = minutes / 60 * hourly_rate
    total = labor + garment_cost + material_cost
    price = total / (1 - margin / 100)
    if not all(isfinite(value) for value in (minutes, labor, total, price)):
        raise ValueError("Wartości są zbyt duże, aby obliczyć wycenę.")
    return PricingResult(minutes, labor, material_cost, garment_cost, total, price, price - total)
