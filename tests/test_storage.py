from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import pandas as pd

from studio.storage import CsvStore, StorageError


def _process_order(args):
    path, index = args
    return CsvStore(path).add_order(client=f"Process {index}", product="Polo", quantity=1, stitches=1000, net_amount=20, status="Nowe", document="FV")


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.store = CsvStore(self.path)

    def order(self, **overrides):
        return self.store.add_order(**(dict(client="Firma Żółć", product="Bluza", quantity=12, stitches=16000, net_amount=690.5, status="Nowe", document="FV") | overrides))

    def test_missing_and_empty_files_have_typed_schemas(self):
        for filename, read in (("orders.csv", self.store.orders), ("expenses.csv", self.store.expenses)):
            with self.subTest(filename=filename):
                self.assertTrue(read().empty)
                self.assertTrue(pd.api.types.is_datetime64_any_dtype(read()["created_at"]))
                (self.path / filename).touch()
                self.assertTrue(read().empty)

    def test_order_round_trip_update_and_delete(self):
        first = self.order(client='Żółć, "Studio"\nOddział 1')
        second = self.order(document="Paragon")
        self.assertNotEqual(first, second)
        frame = self.store.orders()
        self.assertEqual(len(frame), 2)
        self.assertEqual(frame.iloc[0].client, 'Żółć, "Studio"\nOddział 1')
        self.assertEqual(frame.iloc[0].quantity, 12)
        self.assertEqual(frame.iloc[0].net_amount, 690.5)
        self.assertFalse(pd.isna(frame.iloc[0].created_at))
        self.assertTrue(self.store.update_order_status(first, "W produkcji"))
        self.assertEqual(self.store.orders().iloc[0].status, "W produkcji")
        self.assertFalse(self.store.update_order_status("missing", "Gotowe"))
        self.assertTrue(self.store.delete_order(first))
        self.assertFalse(self.store.delete_order(first))
        self.assertEqual(self.store.orders().id.tolist(), [second])
        self.assertTrue(self.store.delete_order(second))
        self.assertTrue(self.store.orders().empty)

    def test_expense_round_trip_and_delete(self):
        record_id = self.store.add_expense(category="Serwis maszyn", supplier="Serwis Łódź", gross_amount=1230)
        expense = self.store.expenses().iloc[0]
        self.assertEqual(expense.supplier, "Serwis Łódź")
        self.assertEqual(expense.gross_amount, 1230)
        self.assertEqual(expense.id, record_id)
        self.assertFalse(self.store.delete_expense("missing"))
        self.assertTrue(self.store.delete_expense(record_id))
        self.assertTrue(self.store.expenses().empty)

    def test_invalid_input_never_creates_records(self):
        for overrides in (dict(client="  "), dict(client=None), dict(product="unknown"), dict(quantity=0), dict(quantity=2.5), dict(net_amount=math.nan), dict(stitches=-1), dict(status="unknown"), dict(document="other")):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.order(**overrides)
        self.assertTrue(self.store.orders().empty)
        for amount in (-1, math.inf, math.nan):
            with self.assertRaises(ValueError):
                self.store.add_expense(category="Inne", supplier="Test", gross_amount=amount)
        self.assertTrue(self.store.expenses().empty)

    def test_corrupt_files_are_not_silently_overwritten(self):
        for content in ('id,created_at,quantity\nabc,invalid,1\n', 'id,created_at,quantity\nabc,2026-01-01,not-a-number\n', 'id,created_at\nabc,2026-01-01\nabc,2026-01-01\n', 'client,quantity\nTest,1\n', 'id,created_at\n"unterminated,2026-01-01\n', 'id,created_at\nextra,abc,2026-01-01\n'):
            with self.subTest(content=content):
                csv_path = self.path / "orders.csv"
                csv_path.write_text(content, encoding="utf-8")
                with self.assertRaises(StorageError):
                    self.store.orders()
                with self.assertRaises(StorageError):
                    self.order()
                self.assertEqual(csv_path.read_text(encoding="utf-8"), content)

    def test_optional_blank_cells_get_defaults_without_dropping_rows(self):
        (self.path / "orders.csv").write_text("id,created_at,client,quantity,net_amount,status\nabc,2026-01-01,,,,\n", encoding="utf-8")
        row = self.store.orders().iloc[0]
        self.assertEqual(row.client, "Nieznany klient")
        self.assertEqual(row.quantity, 1)
        self.assertEqual(row.net_amount, 0)
        self.assertEqual(row.status, "Nowe")
        self.assertEqual(row["product"], "Inny produkt")
        self.assertFalse(self.store.orders().isna().any().any())

    def test_names_that_look_like_missing_markers_are_preserved(self):
        self.order(client="NA")
        self.assertEqual(self.store.orders().iloc[0].client, "NA")

    def test_failed_atomic_replace_keeps_original_file(self):
        self.order()
        before = (self.path / "orders.csv").read_bytes()
        with patch("studio.storage.os.replace", side_effect=OSError("disk error")):
            with self.assertRaises(StorageError):
                self.order(client="Another client")
        self.assertEqual((self.path / "orders.csv").read_bytes(), before)
        self.assertEqual(list(self.path.glob("*.tmp")), [])

    def test_concurrent_writers_do_not_lose_orders(self):
        # Separate store instances simulate simultaneous browser sessions.
        def add(index):
            return CsvStore(self.path).add_order(client=f"Client {index}", product="Polo", quantity=1, stitches=1000, net_amount=20, status="Nowe", document="FV")
        with ThreadPoolExecutor(max_workers=6) as pool:
            ids = list(pool.map(add, range(18)))
        self.assertEqual(len(set(ids)), 18)
        self.assertEqual(set(self.store.orders().id), set(ids))

    def test_spawned_processes_do_not_lose_orders(self):
        # Spawn is also used on Windows; these writers do not share Python locks.
        with ProcessPoolExecutor(max_workers=3, mp_context=multiprocessing.get_context("spawn")) as pool:
            ids = list(pool.map(_process_order, [(str(self.path), index) for index in range(12)]))
        frame = self.store.orders()
        self.assertEqual(len(frame), 12)
        self.assertEqual(set(frame.id), set(ids))


if __name__ == "__main__":
    unittest.main()
