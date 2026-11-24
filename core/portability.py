import argparse
import json
import zipfile
import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
from core.platform import data_path, data_dir
BACKUPS = data_dir() / "backups"
ALLOWED = [
    "memory/memory.json",
    "memory/model_registry.json",
    "logs/task_ledger.json",
    "logs/errors.log",
    "memory/model_comparisons.json",
    "integrations/registry.json",
    "data/evidence_ledger.jsonl",
]

def export_data():
    BACKUPS.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = BACKUPS / f"NOVA_transfer_{stamp}.nova"

    manifest = {
        "format": "NOVA_PORTABLE",
        "version": 1,
        "created": datetime.now(timezone.utc).isoformat(),
        "files": {}
    }

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in ALLOWED:
            path = data_path(name, ROOT / name)
            if path.is_file():
                data = path.read_bytes()
                manifest["files"][name] = hashlib.sha256(data).hexdigest()
                archive.writestr(name, data)

        archive.writestr(
            "manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2)
        )

    print("NOVA EXPORT: SUCCESS")
    print("File:", target)
    print("Size:", round(target.stat().st_size / 1024, 2), "KB")
    print("Included files:", len(manifest["files"]))


def import_data(source):
    source = Path(source).expanduser().resolve()

    if not source.is_file():
        raise ValueError("Transfer file not found.")

    BACKUPS.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safety = BACKUPS / f"before_import_{stamp}"

    with zipfile.ZipFile(source, "r") as archive:
        names = archive.namelist()

        if "manifest.json" not in names:
            raise ValueError("Invalid NOVA transfer package.")

        manifest = json.loads(archive.read("manifest.json"))

        if manifest.get("format") != "NOVA_PORTABLE":
            raise ValueError("Unsupported package format.")

        files = manifest.get("files", {})
        if not isinstance(files, dict) or not files:
            raise ValueError("No transferable data found.")

        for name, expected_hash in files.items():
            if name not in ALLOWED:
                raise ValueError("Unapproved file in package: " + name)

            data = archive.read(name)

            if hashlib.sha256(data).hexdigest() != expected_hash:
                raise ValueError("File integrity check failed: " + name)

            if name.endswith(".json"):
                json.loads(data.decode("utf-8"))

        safety.mkdir(parents=True, exist_ok=True)

        for name in files:
            destination = data_path(name, ROOT / name)

            if destination.exists():
                backup_path = safety / name
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(destination, backup_path)

        for name in files:
            destination = data_path(name, ROOT / name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            temp = destination.with_name(destination.name + ".nova_tmp")
            temp.write_bytes(archive.read(name))
            temp.replace(destination)

    print("NOVA IMPORT: SUCCESS")
    print("Restored files:", len(files))
    print("Previous data backup:", safety)


def main():
    parser = argparse.ArgumentParser(description="NOVA Data Portability")
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser("export", help="Export NOVA data")

    imp = sub.add_parser("import", help="Restore NOVA data")
    imp.add_argument("file", help="Path to .nova transfer file")

    args = parser.parse_args()

    if args.action == "export":
        export_data()
    else:
        import_data(args.file)


if __name__ == "__main__":
    main()
