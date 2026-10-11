"""Rebuild ALL_PROJECTS_INDEX.json — ทะเบียนโค้ดไดรฟ์ J: เวอร์ชันใหม่
อนุมัติโดยลูกพี่ 2026-10-09 (ข้อ 1 ของตัวเลือก)
- สแกน J:\\ ทั้งหมด ยกเว้นโฟลเดอร์ขยะ/ระบบ (EXCLUDE_DIRS)
- นับทุกนามสกุลใน CODE_EXTENSIONS ไม่ใช่แค่ .py
- สำรองของเก่าเป็น ALL_PROJECTS_INDEX.<วัน>.backup.json ก่อนเขียนทับ
- เพิ่ม _meta (scanned_at / exclusions / skipped roots) + _loose_files
"""
import ast
import ctypes
import json
import os
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

FILE_ATTRIBUTE_REPARSE_POINT = 0x400


def is_reparse_point(path):
    """True ถ้าเป็น junction/symlink/reparse point (Windows) — กัน os.walk นับซ้ำ."""
    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        if attrs == -1:
            return False
        return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)
    except Exception:
        return False

ROOT = Path("J:/")
TARGET = ROOT / "ALL_PROJECTS_INDEX.json"
MAX_AST_BYTES = 512 * 1024

EXCLUDE_DIRS = {
    "venv", ".venv", "env", "node_modules", "__pycache__", ".git", "build",
    "dist", "out", ".gradle", ".idea", ".dart_tool", ".manus", "site-packages",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".next", ".nuxt", "target",
    "$recycle.bin", "system volume information", "ollama_models",
    "huggingface_cache", "gradle", "typesafe", ".claude", ".agents",
    ".antigravity", ".context", ".vscode", ".clinerules", "talonhub",
}

CODE_EXTENSIONS = {
    ".py", ".md", ".json", ".yaml", ".yml", ".dart", ".kt", ".kts", ".ts",
    ".tsx", ".js", ".jsx", ".cs", ".cpp", ".h", ".hpp", ".rs", ".sh", ".ps1",
    ".bat", ".cmd", ".sql", ".toml", ".cfg", ".ini", ".html", ".css", ".xml",
}


def should_skip_dir(name):
    n = name.lower()
    return n in EXCLUDE_DIRS or "backup" in n


def count_lines(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def scan_python(path):
    classes, functions = [], []
    try:
        if os.path.getsize(path) <= MAX_AST_BYTES:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(node.name)
    except (OSError, SyntaxError, ValueError, RecursionError):
        pass
    return classes, functions


def scan_project(project_dir):
    files, exts, total_bytes, total_lines = {}, Counter(), 0, 0
    for dirpath, dirnames, filenames in os.walk(project_dir):
        dirnames[:] = [
            d for d in dirnames
            if not should_skip_dir(d)
            and not is_reparse_point(os.path.join(dirpath, d))
        ]
        for name in filenames:
            ext = os.path.splitext(name)[1].lower()
            if ext not in CODE_EXTENSIONS:
                continue
            full = Path(dirpath) / name
            rel = full.relative_to(project_dir).as_posix()
            entry = {}
            if ext == ".py":
                entry["classes"], entry["functions"] = scan_python(full)
            entry["lines"] = count_lines(full)
            try:
                size = full.stat().st_size
                total_bytes += size
            except OSError:
                size = 0
            entry["bytes"] = size
            files[rel] = entry
            exts[ext] += 1
            total_lines += entry["lines"]
    return {
        "name": project_dir.name,
        "path": project_dir.as_posix(),
        "type": exts.most_common(1)[0][0].lstrip(".") if exts else "unknown",
        "files_count": len(files),
        "total_lines": total_lines,
        "size_bytes": total_bytes,
        "extensions": dict(exts.most_common()),
        "files": files,
    }


def main():
    scanned_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    index, skipped, loose = {}, [], {}

    for entry in sorted(ROOT.iterdir(), key=lambda p: p.name.lower()):
        try:
            if entry.is_dir():
                if should_skip_dir(entry.name) or entry.name.startswith("$"):
                    skipped.append(entry.name)
                    continue
                index[entry.name] = scan_project(entry)
            elif entry.is_file():
                ext = entry.suffix.lower()
                if ext in CODE_EXTENSIONS and entry.name != TARGET.name:
                    loose[entry.name] = {
                        "lines": count_lines(entry),
                        "bytes": entry.stat().st_size,
                    }
        except OSError as exc:
            skipped.append("{} (error: {})".format(entry.name, exc))

    index["_meta"] = {
        "scanned_at": scanned_at,
        "root": ROOT.as_posix(),
        "generator": "J:\\Mark-LV\\tools\\rebuild_project_index.py",
        "projects_indexed": len([k for k in index if not k.startswith("_")]),
        "code_extensions": sorted(CODE_EXTENSIONS),
        "excluded_dir_names": sorted(EXCLUDE_DIRS),
        "skipped_roots": sorted(set(skipped)),
        "note": "index เวอร์ชันใหม่ ทะเบียนเก่า 2026-10-06 สำรองเป็นไฟล์ .backup.json แล้ว",
    }
    index["_loose_files"] = loose

    if TARGET.exists():
        stamp = datetime.fromtimestamp(TARGET.stat().st_mtime).strftime("%Y-%m-%d")
        backup = ROOT / "ALL_PROJECTS_INDEX.{}.backup.json".format(stamp)
        shutil.copy2(TARGET, backup)
        print("backup -> {}".format(backup.name))

    with open(TARGET, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print("wrote {} ({:.1f} MB)".format(
        TARGET, TARGET.stat().st_size / (1024 * 1024)))
    for key, val in index.items():
        if key.startswith("_"):
            continue
        print("  {:<45} {:>5} files {:>9} lines".format(
            key, val["files_count"], val["total_lines"]))
    print("  skipped_roots = {}".format(len(index["_meta"]["skipped_roots"])))


if __name__ == "__main__":
    main()
