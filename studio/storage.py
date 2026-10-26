"""Local CSV persistence with validated schemas, locks and atomic writes.

Each mutation holds a process-shared lock across read, change and replace. A
malformed CSV is reported rather than replaced by an empty frame. Text and
optional empty values get safe display defaults; no existing rows are dropped.
"""

from contextlib import contextmanager
from datetime import datetime
from math import isfinite
import os
from pathlib import Path
import tempfile
from uuid import uuid4

import pandas as pd
from filelock import FileLock, Timeout


ORDER_STATUSES = ("Nowe", "W produkcji", "Gotowe", "Zrealizowane", "Anulowane")
PRODUCTS = ("T-shirt", "Bluza", "Polo", "Czapka", "Torba", "Polar", "Odzież robocza", "Inny produkt")
COST_CATEGORIES = ("Odzież i materiały", "Nici i akcesoria", "Serwis maszyn", "Media i lokal", "Marketing", "Transport", "Inne")
ORDER_COLUMNS = ("id", "created_at", "client", "product", "quantity", "stitches", "net_amount", "status", "document")
EXPENSE_COLUMNS = ("id", "created_at", "category", "supplier", "gross_amount")


class StorageError(Exception):
    """An actionable storage failure safe to present to a user."""


def _text(value: object, label: str, *, max_length: int = 200) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: wpisz niepustą wartość.")
    value = value.strip()
    if len(value) > max_length:
        raise ValueError(f"{label}: maksymalnie {max_length} znaków.")
    return value


def _numeric(value: object, label: str, *, minimum: float = 0, integer: bool = False) -> float | int:
    if isinstance(value, bool):
        raise ValueError(f"{label}: podaj liczbę.")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{label}: podaj poprawną liczbę.") from exc
    if not isfinite(result) or result < minimum or (integer and not result.is_integer()):
        raise ValueError(f"{label}: podaj {'całkowitą ' if integer else ''}liczbę nie mniejszą niż {minimum}.")
    return int(result) if integer else result


class CsvStore:
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir).expanduser().resolve()
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError("Nie można utworzyć katalogu danych. Sprawdź ścieżkę i uprawnienia.") from exc

    @contextmanager
    def _lock(self, *, write: bool = False):
        try:
            # Use an OS-backed lock on Windows as well as Unix. Reads are
            # exclusive too, so all sessions share one portable protocol.
            with FileLock(str(self.data_dir / ".storage.lock"), timeout=15):
                yield
        except Timeout as exc:
            raise StorageError("Pliki danych są zajęte przez inną operację. Spróbuj ponownie za chwilę.") from exc
        except OSError as exc:
            raise StorageError("Nie można odczytać lub zapisać CSV. Sprawdź uprawnienia i wolne miejsce.") from exc

    @staticmethod
    def _empty(columns: tuple[str, ...]) -> pd.DataFrame:
        frame = pd.DataFrame(columns=columns)
        frame["created_at"] = pd.Series(dtype="datetime64[ns]")
        for column in ("quantity", "stitches", "net_amount", "gross_amount"):
            if column in frame:
                frame[column] = pd.Series(dtype="int64" if column in ("quantity", "stitches") else "float64")
        return frame

    def _read(self, filename: str, columns: tuple[str, ...]) -> pd.DataFrame:
        path = self.data_dir / filename
        if not path.exists() or path.stat().st_size == 0:
            return self._empty(columns)
        try:
            # Preserve legitimate client names such as "NA"; only blank cells
            # are missing. Comma delimiters and UTF-8 are the file contract.
            frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        except pd.errors.EmptyDataError:
            return self._empty(columns)
        except (pd.errors.ParserError, UnicodeError, ValueError) as exc:
            raise StorageError(f"Plik {filename} jest uszkodzony. Przywróć poprawny plik z kopii; dane nie zostały nadpisane.") from exc
        if frame.empty:
            return self._empty(columns)
        # Pandas can infer an index from excess fields instead of reporting a
        # parser error. Reject that layout before a rewrite could drop a field.
        if not isinstance(frame.index, pd.RangeIndex):
            raise StorageError(f"Plik {filename} ma inną liczbę pól niż nagłówek. Popraw CSV przed zapisem.")
        if not {"id", "created_at"}.issubset(frame.columns):
            raise StorageError(f"Plik {filename} nie ma kolumn id i created_at. Popraw nagłówki; dane nie zostały nadpisane.")
        if any(column not in columns for column in frame.columns):
            raise StorageError(f"Plik {filename} zawiera nieobsługiwane kolumny. Zachowaj ich kopię i przywróć schemat aplikacji.")
        defaults = {"client": "Nieznany klient", "product": "Inny produkt", "quantity": "1", "stitches": "0", "net_amount": "0", "status": "Nowe", "document": "FV", "category": "Inne", "supplier": "Nieznany dostawca", "gross_amount": "0"}
        for column in columns:
            if column not in frame:
                frame[column] = defaults.get(column, "")
            frame[column] = frame[column].fillna("").astype(str).str.strip()
            if column in defaults:
                frame[column] = frame[column].replace("", defaults[column])
        if frame["id"].eq("").any() or frame["id"].duplicated().any():
            raise StorageError(f"Plik {filename} zawiera brakujące lub powtórzone ID. Popraw dane przed zapisem.")
        try:
            frame["created_at"] = pd.to_datetime(frame["created_at"], format="mixed", errors="raise", utc=True).dt.tz_localize(None)
            if frame["created_at"].isna().any():
                raise ValueError("missing date")
            for column in ("quantity", "stitches", "net_amount", "gross_amount"):
                if column in frame:
                    frame[column] = frame[column].map(lambda value, column=column: _numeric(value, column, minimum=1 if column == "quantity" else 0, integer=column in ("quantity", "stitches")))
        except (ValueError, TypeError, OverflowError) as exc:
            raise StorageError(f"Plik {filename} zawiera niepoprawną datę lub liczbę. Popraw dane; plik nie został nadpisany.") from exc
        if "status" in frame and not frame["status"].isin(ORDER_STATUSES).all():
            raise StorageError(f"Plik {filename} zawiera nieobsługiwany status zlecenia.")
        if "document" in frame and not frame["document"].isin(("FV", "Paragon")).all():
            raise StorageError(f"Plik {filename} zawiera nieobsługiwany rodzaj dokumentu.")
        return frame.loc[:, list(columns)]

    def _write(self, filename: str, frame: pd.DataFrame) -> None:
        temp_path = None
        try:
            fd, temp_path = tempfile.mkstemp(prefix=f".{filename}.", suffix=".tmp", dir=self.data_dir)
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as output:
                frame.to_csv(output, index=False)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temp_path, self.data_dir / filename)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    def orders(self) -> pd.DataFrame:
        with self._lock():
            return self._read("orders.csv", ORDER_COLUMNS)

    def expenses(self) -> pd.DataFrame:
        with self._lock():
            return self._read("expenses.csv", EXPENSE_COLUMNS)

    def add_order(self, *, client, product, quantity, stitches, net_amount, status, document) -> str:
        client = _text(client, "Nazwa klienta")
        if product not in PRODUCTS or status not in ORDER_STATUSES or document not in ("FV", "Paragon"):
            raise ValueError("Wybierz produkt, status i dokument z dostępnych opcji.")
        row = {"id": str(uuid4()), "created_at": datetime.now().isoformat(timespec="seconds"), "client": client, "product": product, "quantity": _numeric(quantity, "Liczba sztuk", minimum=1, integer=True), "stitches": _numeric(stitches, "Liczba wkłuć", integer=True), "net_amount": _numeric(net_amount, "Kwota netto"), "status": status, "document": document}
        with self._lock(write=True):
            frame = self._read("orders.csv", ORDER_COLUMNS)
            records = frame.to_dict("records")
            records.append(row)
            self._write("orders.csv", pd.DataFrame(records, columns=ORDER_COLUMNS))
        return row["id"]

    def add_expense(self, *, category, supplier, gross_amount) -> str:
        supplier = _text(supplier, "Dostawca")
        if category not in COST_CATEGORIES:
            raise ValueError("Wybierz kategorię z dostępnych opcji.")
        row = {"id": str(uuid4()), "created_at": datetime.now().isoformat(timespec="seconds"), "category": category, "supplier": supplier, "gross_amount": _numeric(gross_amount, "Kwota brutto")}
        with self._lock(write=True):
            frame = self._read("expenses.csv", EXPENSE_COLUMNS)
            records = frame.to_dict("records")
            records.append(row)
            self._write("expenses.csv", pd.DataFrame(records, columns=EXPENSE_COLUMNS))
        return row["id"]

    def update_order_status(self, order_id: str, status: str) -> bool:
        if status not in ORDER_STATUSES:
            raise ValueError("Wybierz status z dostępnych opcji.")
        with self._lock(write=True):
            frame = self._read("orders.csv", ORDER_COLUMNS)
            matched = frame["id"].eq(order_id)
            if not matched.any():
                return False
            frame.loc[matched, "status"] = status
            self._write("orders.csv", frame)
        return True

    def _delete(self, filename: str, columns: tuple[str, ...], record_id: str) -> bool:
        with self._lock(write=True):
            frame = self._read(filename, columns)
            keep = frame["id"].ne(record_id)
            if keep.all():
                return False
            self._write(filename, frame.loc[keep])
        return True

    def delete_order(self, order_id: str) -> bool:
        return self._delete("orders.csv", ORDER_COLUMNS, order_id)

    def delete_expense(self, expense_id: str) -> bool:
        return self._delete("expenses.csv", EXPENSE_COLUMNS, expense_id)
