from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

EXCLUDED_PARTS = {
    "__pycache__", "backups", ".git", ".venv", "venv",
    "logs", "dist", "node_modules"
}
EXCLUDED_NAMES = {
    ".env", ".env.local", "api_key", "secrets.json"
}

def allowed(path):
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDED_PARTS for part in rel.parts):
        return False
    if path.name in EXCLUDED_NAMES:
        return False
    if ".backup" in path.name or ".bak" in path.name:
        return False
    if path.suffix in {".pyc", ".pyo", ".log"}:
        return False
    if path.is_symlink() or not path.is_file():
        return False

    parts = rel.parts
    if parts[0] == "core":
        return path.suffix == ".py"
    if parts[0] == "memory":
        return rel.as_posix() == "memory/store.py"
    if parts[0] == "web":
        return path.suffix.lower() in {".png", ".svg", ".ico", ".webmanifest", ".js", ".css"}
    if parts[0] == "tools":
        return rel.as_posix() == "tools/package_nova.py"
    return rel.as_posix() in {"README.md"}

def build():
    DIST.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in ROOT.rglob("*") if allowed(p))

    required = [
        "core/web_app.py",
        "core/ai/gateway.py",
        "core/ai/config.py",
        "core/ai/multimodel.py",
        "core/ai/team_engine.py",
        "memory/store.py",
        "web/icon-192.png",
        "web/icon-512.png",
    ]
    names = {p.relative_to(ROOT).as_posix() for p in files}
    missing = [name for name in required if name not in names]
    if missing:
        raise RuntimeError("Required files missing: " + ", ".join(missing))

    manifest = {
        "format": "NOVA_SOURCE_PACKAGE",
        "format_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files),
        "files": {}
    }

    for path in files:
        data = path.read_bytes()
        manifest["files"][path.relative_to(ROOT).as_posix()] = hashlib.sha256(data).hexdigest()

    target = DIST / ("NOVA-Portable-" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".zip")
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr(
            "PACKAGE-MANIFEST.json",
            json.dumps(manifest, ensure_ascii=False, indent=2)
        )

    # Verify archive contents and every checksum before reporting success.
    with zipfile.ZipFile(target, "r") as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError("ZIP integrity error: " + bad)
        stored = json.loads(archive.read("PACKAGE-MANIFEST.json"))
        for name, expected in stored["files"].items():
            actual = hashlib.sha256(archive.read(name)).hexdigest()
            if actual != expected:
                raise RuntimeError("Checksum mismatch: " + name)

    print("PACKAGE BUILD: PASS")
    print("FILE COUNT:", len(files))
    print("PACKAGE:", target.relative_to(ROOT))
    print("SIZE:", round(target.stat().st_size / 1024, 2), "KB")
    print("CHECKSUM VALIDATION: PASS")
    print("ZIP TEST: PASS")
    print("API KEYS / ENV FILES: EXCLUDED")
    print("MEMORY DATA / LOGS / BACKUPS: EXCLUDED")
    return target

if __name__ == "__main__":
    build()
