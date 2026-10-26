"""Exercise real Streamlit interactions against isolated on-disk CSV stores."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

from studio.storage import CsvStore


ROOT = Path(__file__).resolve().parents[1]
PAGES = ["📊  Panel Główny", "➕  Nowe Zlecenie", "💸  Koszty & Wydatki", "⚙️  Kalkulator Wyceny"]


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data_dir = Path(self.temp.name)
        self.env_patch = patch.dict(os.environ, {"HFT_DATA_DIR": self.temp.name})
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def new_app(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
        self.assert_no_exception(app)
        return app

    def assert_no_exception(self, app):
        self.assertEqual(len(app.exception), 0, [item.value for item in app.exception])

    @staticmethod
    def widget(elements, label):
        return next(element for element in elements if element.label == label)

    def navigate(self, app, page):
        app.radio(key="navigation").set_value(page).run()
        self.assert_no_exception(app)

    def test_new_workspace_is_empty_and_ready_for_real_entries(self):
        app = self.new_app()
        self.assertEqual(len(app.toggle), 0)
        self.assertEqual(len(app.get("plotly_chart")), 0)
        self.assertFalse(any("Podgląd demo" in item.value for item in app.markdown))
        self.navigate(app, PAGES[1])
        self.assertFalse(self.widget(app.button, "Dodaj zlecenie").disabled)
        self.assertFalse(self.widget(app.text_input, "Nazwa klienta").disabled)
        self.assertEqual(len(app.expander), 0)
        self.navigate(app, PAGES[2])
        self.assertFalse(self.widget(app.button, "Zapisz wydatek").disabled)
        self.assertEqual(len(app.get("plotly_chart")), 0)
        self.assertEqual(list(self.data_dir.glob("*.csv")), [])

    def test_empty_dashboard_and_complete_order_lifecycle(self):
        app = self.new_app()
        self.assertEqual(len(app.error), 0)
        self.assertEqual(len(app.get("plotly_chart")), 0)
        self.navigate(app, PAGES[1])

        # Required field validation does not create partial CSV records.
        self.widget(app.button, "Dodaj zlecenie").click().run()
        self.assert_no_exception(app)
        self.assertTrue(any("niepustą" in error.value for error in app.error))
        self.assertFalse((self.data_dir / "orders.csv").exists())

        self.widget(app.text_input, "Nazwa klienta").set_value("Pracownia Testowa")
        self.widget(app.selectbox, "Typ produktu").select("Bluza")
        self.widget(app.number_input, "Ilość sztuk").set_value(6)
        self.widget(app.number_input, "Kwota netto całego zlecenia (zł)").set_value(360.0)
        self.widget(app.number_input, "Szacowane wkłucia na sztukę").set_value(8000)
        self.widget(app.toggle, "Faktura VAT (FV)").set_value(False)
        self.widget(app.button, "Dodaj zlecenie").click().run()
        self.assert_no_exception(app)
        order = pd.read_csv(self.data_dir / "orders.csv").iloc[0]
        self.assertEqual(order["client"], "Pracownia Testowa")
        self.assertEqual(order["quantity"], 6)
        self.assertEqual(order["net_amount"], 360)
        self.assertEqual(order["document"], "Paragon")
        self.assertTrue(pd.notna(pd.to_datetime(order["created_at"])))
        oid = order["id"]

        app.selectbox(key=f"status_{oid}").select("Zrealizowane")
        app.button(key=f"save_{oid}").click().run()
        self.assert_no_exception(app)
        self.assertEqual(pd.read_csv(self.data_dir / "orders.csv").iloc[0]["status"], "Zrealizowane")

        # A fresh session sees persisted data without a sample-data toggle.
        reloaded = self.new_app()
        self.assertEqual(len(reloaded.toggle), 0)
        self.assertEqual(len(reloaded.get("plotly_chart")), 2)
        self.navigate(reloaded, PAGES[1])
        self.assertTrue(reloaded.button(key=f"delete_{oid}").disabled)
        reloaded.checkbox(key=f"confirm_{oid}").check().run()
        self.assertFalse(reloaded.button(key=f"delete_{oid}").disabled)
        reloaded.button(key=f"delete_{oid}").click().run()
        self.assert_no_exception(reloaded)
        self.assertTrue(pd.read_csv(self.data_dir / "orders.csv").empty)

    def test_expense_write_reload_and_confirmed_delete(self):
        app = self.new_app()
        self.navigate(app, PAGES[2])
        self.widget(app.selectbox, "Kategoria").select("Nici i akcesoria")
        self.widget(app.text_input, "Dostawca").set_value("Dostawca Testowy")
        self.widget(app.number_input, "Kwota brutto (zł)").set_value(123.45)
        self.widget(app.button, "Zapisz wydatek").click().run()
        self.assert_no_exception(app)
        expenses = pd.read_csv(self.data_dir / "expenses.csv")
        self.assertEqual(len(expenses), 1)
        self.assertEqual(expenses.iloc[0]["supplier"], "Dostawca Testowy")
        self.assertAlmostEqual(expenses.iloc[0]["gross_amount"], 123.45)
        self.assertEqual(len(app.get("plotly_chart")), 1)

        reloaded = self.new_app()
        self.assertEqual(len(reloaded.toggle), 0)
        self.navigate(reloaded, PAGES[2])
        self.assertTrue(self.widget(reloaded.button, "Usuń wydatek").disabled)
        self.widget(reloaded.checkbox, "Potwierdzam usunięcie wydatku").check().run()
        self.widget(reloaded.button, "Usuń wydatek").click().run()
        self.assert_no_exception(reloaded)
        self.assertTrue(pd.read_csv(self.data_dir / "expenses.csv").empty)

    def test_pricing_inputs_update_the_displayed_quote(self):
        app = self.new_app()
        self.navigate(app, PAGES[3])
        app.number_input(key="pricing_stitches").set_value(6000)
        app.number_input(key="pricing_speed").set_value(600)
        app.number_input(key="pricing_changes").set_value(2)
        app.number_input(key="pricing_garment").set_value(20.0)
        app.slider(key="pricing_margin").set_value(50).run()
        self.assert_no_exception(app)
        # 10 min embroidery + 5 min setup + 1 min colour changes = 16 min;
        # cost = 24 labour + 20 garment + 1.50 material; 50% margin => 91 zł.
        card = next(item.value for item in app.markdown if 'class="price-card"' in item.value)
        self.assertIn("91,00", card)
        self.assertIn("16,0 min", card)
        self.assertIn("45,50 zł", card)
        app.slider(key="pricing_margin").set_value(0).run()
        self.assert_no_exception(app)
        updated = next(item.value for item in app.markdown if 'class="price-card"' in item.value)
        self.assertIn('class="price-number">45,50', updated)
        self.assertEqual(list(self.data_dir.glob("*.csv")), [])

    def test_expense_confirmation_does_not_transfer_to_another_entry(self):
        store = CsvStore(self.data_dir)
        first_id = store.add_expense(category="Nici i akcesoria", supplier="Dostawca A", gross_amount=50)
        second_id = store.add_expense(category="Transport", supplier="Dostawca B", gross_amount=80)
        original_csv = (self.data_dir / "expenses.csv").read_bytes()

        app = self.new_app()
        self.navigate(app, PAGES[2])
        self.widget(app.selectbox, "Wybierz wydatek").set_value(first_id).run()
        app.checkbox(key=f"confirm_expense_{first_id}").check().run()
        self.assertFalse(self.widget(app.button, "Usuń wydatek").disabled)

        self.widget(app.selectbox, "Wybierz wydatek").set_value(second_id).run()
        self.assert_no_exception(app)
        self.assertFalse(app.checkbox(key=f"confirm_expense_{second_id}").value)
        self.assertTrue(self.widget(app.button, "Usuń wydatek").disabled)
        self.assertEqual((self.data_dir / "expenses.csv").read_bytes(), original_csv)

    def test_malformed_csv_reports_error_without_overwriting(self):
        path = self.data_dir / "orders.csv"
        bad_content = "wrong,columns\nnot,a-valid-order\n"
        path.write_text(bad_content, encoding="utf-8")
        app = self.new_app()
        self.assertEqual(len(app.error), 1)
        self.assertIn("orders.csv", app.error[0].value)
        self.assertTrue(any("Pliki źródłowe pozostają bez zmian" in info.value for info in app.info))
        self.assertEqual(path.read_text(encoding="utf-8"), bad_content)


if __name__ == "__main__":
    unittest.main()
