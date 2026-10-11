"""Report remaining migration work; with --apply, retry previously locked moves."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from organize_project import ROOT, LOG, move_contents

APPLY = "--apply" in sys.argv
manifest = json.loads((LOG / "manifest.json").read_text(encoding="utf-8"))

print("== Manifest status ==")
unfinished = []
for record in manifest:
    status = record["status"]
    locked = [name for name, state in record.get("children", {}).items() if state != "verified"]
    line = f"{status}: {record['source']} -> {record['target']}"
    if locked:
        line += f" | locked children: {', '.join(locked)}"
    print(line)
    if status not in {"verified_with_compatibility_link", "verified_with_compatibility_shell"}:
        unfinished.append(record)

print("\n== Duplicate-looking folders on J:/ ==")
seen = {}
for entry in Path("J:/").iterdir():
    name = entry.name
    if name.startswith("โปรเจค"):
        hex_name = name.encode("utf-8").hex()
        seen[name] = hex_name
        try:
            children = sorted(p.name for p in entry.iterdir())
        except OSError as error:
            children = [f"unreadable: {error}"]
        print(f"{name!r}\n  utf8: {hex_name}\n  entries: {len(children)} -> {children[:10]}")
if len(seen) == 1:
    print("Only one project folder exists; no duplicate.")

print("\n== J:/ATOM_MOBILE leftover check ==")
mobile = Path("J:/ATOM_MOBILE")
if mobile.exists():
    for item in sorted(mobile.iterdir(), key=lambda p: p.name):
        kind = "junction" if item.is_junction() else ("dir" if item.is_dir() else "file")
        print(f"  {kind:8} {item.name}")
else:
    print("  J:/ATOM_MOBILE no longer exists")

if APPLY:
    print("\n== Apply: retry unfinished moves ==")
    for record in unfinished:
        source, target = Path(record["source"]), Path(record["target"])
        if not source.exists():
            print(f"skip (source gone, treat as done): {source}")
            record["status"] = "verified_with_compatibility_link"
            continue
        if record.get("children"):
            # Clear a compatibility junction that occupies the destination child
            # slot; junction removal never touches the data it points to.
            for name in list(record.get("children", {})):
                destination = target / name
                if destination.is_junction() and source.exists() and (source / name).is_dir():
                    import os
                    os.rmdir(destination)
                    print(f"removed junction occupying slot: {destination}")
            move_contents(source, target, record, lambda: None)
        else:
            print(f"needs manual review: {source}")
    (LOG / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("manifest updated")
else:
    print("\n(dry run; pass --apply to retry locked moves)")
