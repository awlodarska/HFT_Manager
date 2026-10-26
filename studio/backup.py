"""Create a consistent, dated archive of HFT Studio CSV data."""

from __future__ import annotations

import argparse
from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import zipfile

from filelock import FileLock, Timeout


ROOT = Path(__file__).resolve().parents[1]
DATA_FILENAMES = ("orders.csv", "expenses.csv")


class BackupError(RuntimeError):
    """A safe-to-display backup failure."""


def create_backup(source: Path = ROOT / "data", destination: Path = ROOT / "backups") -> Path | None:
    """Write an atomic ZIP archive, or None when no business data exists yet."""
    source = Path(source).expanduser().resolve()
    destination = Path(destination).expanduser().resolve()
    files = [source / name for name in DATA_FILENAMES if (source / name).is_file()]
    if not files:
        return None
    try:
        destination.mkdir(parents=True, exist_ok=True)
        with FileLock(str(source / ".storage.lock"), timeout=15):
            payloads = {file.name: file.read_bytes() for file in files}
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
        final_path = destination / f"HFT_Studio_kopia_{stamp}.zip"
        descriptor, temporary_name = tempfile.mkstemp(prefix=".backup-", suffix=".zip", dir=destination)
        try:
            os.close(descriptor)
            with zipfile.ZipFile(temporary_name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                manifest = {
                    "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                    "files": {name: {"sha256": sha256(content).hexdigest(), "bytes": len(content)} for name, content in payloads.items()},
                }
                archive.writestr("README.txt", "Kopia danych HFT Studio OS. Pliki CSV znajdują się w tym archiwum.\n")
                archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
                for name, content in payloads.items():
                    archive.writestr(name, content)
            os.replace(temporary_name, final_path)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)
        return final_path
    except Timeout as exc:
        raise BackupError("Dane są teraz zapisywane. Kopia nie została utworzona — spróbuj ponownie za chwilę.") from exc
    except OSError as exc:
        raise BackupError("Nie można utworzyć kopii. Sprawdź miejsce na dysku i uprawnienia do folderu backups.") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an HFT Studio OS backup.")
    parser.add_argument("--source", type=Path, default=ROOT / "data")
    parser.add_argument("--destination", type=Path, default=ROOT / "backups")
    args = parser.parse_args()
    try:
        result = create_backup(args.source, args.destination)
    except BackupError as exc:
        print(f"BŁĄD: {exc}")
        return 1
    if result is None:
        print("Brak danych do skopiowania — nie utworzono archiwum.")
    else:
        print(f"Kopia zapisana: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
