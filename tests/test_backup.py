from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile

from studio.backup import create_backup


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.backups = self.root / "backups"
        self.data.mkdir()

    def test_backup_preserves_csv_and_records_checksums(self):
        orders = b"id,client\n1,Firma Zolc\n"
        expenses = b"id,supplier\n1,Nici S.A.\n"
        (self.data / "orders.csv").write_bytes(orders)
        (self.data / "expenses.csv").write_bytes(expenses)

        archive_path = create_backup(self.data, self.backups)

        self.assertIsNotNone(archive_path)
        self.assertTrue(archive_path.is_file())
        with zipfile.ZipFile(archive_path) as archive:
            self.assertEqual(archive.read("orders.csv"), orders)
            self.assertEqual(archive.read("expenses.csv"), expenses)
            manifest = json.loads(archive.read("manifest.json"))
        self.assertEqual(manifest["files"]["orders.csv"]["sha256"], sha256(orders).hexdigest())
        self.assertEqual((self.data / "orders.csv").read_bytes(), orders)

    def test_no_archive_is_written_before_any_data_exists(self):
        self.assertIsNone(create_backup(self.data, self.backups))
        self.assertFalse(self.backups.exists())


if __name__ == "__main__":
    unittest.main()
