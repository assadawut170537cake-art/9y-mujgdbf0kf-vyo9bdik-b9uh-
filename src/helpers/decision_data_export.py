"""
Export Mark-LV command→action logs as typed-decisions training rows.

WHY
    The generic typed-decisions benchmark mix teaches a model to decide
    things like "which team handles this ticket". What Mark-LV actually needs
    is narrower: given a THAI/ENGLISH voice command, which of the app's
    actions should run? The best training data for that is the app's own
    history — every command the user gave and the action that was confirmed
    right.

ROW SCHEMA (mirrors LocalLLaMA/typed-decisions so FastDecisionModel.
build_dataset accepts it directly — verified against the dataset viewer):
    {
        "id":         "marklv_router_000001_row",
        "workflow":   "marklv_action_router",
        "split":      "train",
        "state":      "{\"task\": \"open chrome\"}",          # JSON string
        "questions":  "{\"action\": {\"type\": \"choice\",    # JSON string
                        \"instructions\": \"…\", \"criteria\": {…}}}",
        "action__label":         "open_app",
        "action__probabilities": "{\"open_app\": 1.0}",
    }

INPUT SOURCES
    1. A JSONL log of decisions, one per line:
           {"command": "…", "action": "open_app", "confidence": 0.9}
       This is the format a plugin should append to whenever route_action()
       answers — see record_decision() for the exact call.
    2. A CSV with columns command,action (confidence optional).

USAGE
    python -m src.helpers.decision_data_export \
        --input logs/routing.jsonl --output data/router_rows.jsonl \
        --actions-json config/action_descriptions.json

    --actions-json is optional: a {name: description} mapping used to build
    the `questions` criteria. Without it, the tool scans actions/*.py TOOL
    dicts at runtime (stdlib-only via core.action_loader).

    After export, train with:
    python src/helpers/train_decision_model.py --dataset data/router_rows.jsonl
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Iterable, Optional


def _log(message: str) -> None:
    """Print with a stable prefix.

    Args:
        message: str — the text to print.
    """
    print(f"[decision-export] {message}")


def load_action_descriptions(project_root: Optional[Path] = None,
                             actions_json: Optional[str] = None) -> dict:
    """Collect {action_name: description} from a JSON file or actions/*.py.

    Args:
        project_root: Path | None — repo root (defaults to two levels up
                     from this file).
        actions_json: str | None — path to a {name: description} JSON file.
                     When given, that file wins and no source scan happens.

    Returns:
        dict — {action_name: description}; {} on any failure (logged).
    """
    if actions_json:
        try:
            data = json.loads(Path(actions_json).read_text(encoding="utf-8"))
            if isinstance(data, dict) and data:
                return {str(k): str(v) for k, v in data.items()}
            _log(f"{actions_json} is not a non-empty object — ignoring")
        except Exception as e:
            _log(f"could not read {actions_json}: {e}")
    try:
        root = project_root or Path(__file__).resolve().parent.parent.parent
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        # action_loader is stdlib-only; each actions/*.py guards its own
        # optional deps, so a broken action fails validation and is skipped
        # exactly like at app startup.
        from core.action_loader import discover_actions
        registry = discover_actions(root / "actions", logger=lambda m: None)
        out: dict = {}
        for rec in getattr(registry, "_all_records", []):
            if getattr(rec, "valid", False):
                out[rec.name] = rec.description
        if out:
            return out
        _log("action scan found nothing — pass --actions-json instead")
    except Exception as e:
        _log(f"action scan failed: {e}")
    return {}


def build_questions(actions: dict,
                    instructions: str = "Which action should handle "
                                        "this command?") -> str:
    """Build the `questions` column value (JSON string) for training rows.

    Args:
        actions:     dict — {name: description}; needs 2+ entries.
        instructions: str — the routing question.

    Returns:
        str — JSON string: {"action": {"type": "choice", "instructions": …,
        "criteria": {name: description, …}}} with descriptions truncated to
        200 chars (the same budget build_action_spec uses at inference).
    """
    criteria = {name: (desc or "").strip().replace("\n", " ")[:200]
                for name, desc in actions.items() if name}
    spec = {"action": {
        "type": "choice",
        "instructions": instructions,
        "criteria": criteria,
    }}
    return json.dumps(spec, ensure_ascii=False)


def _one_hot(label: str, actions: dict) -> str:
    """Probabilities column value: 1.0 on the confirmed action, 0.0 elsewhere.

    Args:
        label:   str — the confirmed action name.
        actions: dict — {name: description} of all candidate actions.

    Returns:
        str — JSON string {name: 0.0/1.0}. One-hot keeps the training signal
        honest: the log records a decision that was MADE, not a probability
        distribution the logger guessed at.
    """
    probs = {name: (1.0 if name == label else 0.0) for name in actions}
    return json.dumps(probs)


_ID_RE = re.compile(r"[^a-z0-9]+")


def _make_id(command: str, seq: int) -> str:
    """Stable, filename-safe row id.

    Args:
        command: str — the source command (may be any script).
        seq:     int — row number.

    Returns:
        str — e.g. "marklv_router_000042_openchrome" (the suffix keeps Thai
        commands, which slug to nothing, from all colliding).
    """
    slug = _ID_RE.sub("", command.lower())[:8] or "row"
    return f"marklv_router_{seq:06d}_{slug}"


def _iter_jsonl(path: Path) -> Iterable[dict]:
    """Yield decoded objects from a JSONL file, skipping bad lines.

    Args:
        path: Path — the .jsonl file.

    Yields:
        dict — one per parseable line. Malformed lines are logged and skipped;
        a half-corrupted log should still yield every good row.
    """
    # utf-8-sig tolerates the BOM Windows tools like PowerShell's Set-Content
    # prepend — a BOM would otherwise make json.loads reject line 1.
    with path.open(encoding="utf-8-sig") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                _log(f"{path.name}:{lineno}: skipped ({e})")
                continue
            if isinstance(obj, dict):
                yield obj


def _iter_csv(path: Path) -> Iterable[dict]:
    """Yield rows from a CSV with command,action[,confidence] columns.

    Args:
        path: Path — the .csv file.

    Yields:
        dict — one per row; rows missing command/action are skipped.
    """
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("command") and row.get("action"):
                yield dict(row)


def convert(records: Iterable[dict], actions: dict,
            workflow: str = "marklv_action_router") -> list:
    """Convert decision log records into typed-decisions training rows.

    Args:
        records: Iterable[dict] — each with "command" and "action" keys
                 (optional "confidence").
        actions: dict — the {name: description} universe; a record whose
                 action is NOT in here is skipped (it cannot be a training
                 example for a choice the spec does not offer).
        workflow: str — the `workflow` column value.

    Returns:
        list[dict] — rows in the schema documented in the module header.
    """
    questions = build_questions(actions)
    rows: list = []
    for rec in records:
        command = str(rec.get("command", "")).strip()
        action = str(rec.get("action", "")).strip()
        if not command or not action:
            continue
        if action not in actions:
            _log(f"unknown action {action!r} — skipped")
            continue
        rows.append({
            "id": _make_id(command, len(rows) + 1),
            "workflow": workflow,
            "split": "train",
            "state": json.dumps({"task": command}, ensure_ascii=False),
            "questions": questions,
            "action__label": action,
            "action__probabilities": _one_hot(action, actions),
        })
    return rows


def record_decision(log_path: str, command: str, action: str,
                    confidence: float = 0.0) -> bool:
    """Append one routed command to the JSONL decision log.

    Call this from the app/plugin after route_action() returns a confident
    answer (or after the user confirms one) — the file it writes is exactly
    what convert() consumes later, closing the collect→train→serve loop.

    Args:
        log_path:   str — target .jsonl file (parent dirs are created).
        command:    str — the raw user command.
        action:     str — the action that handled it.
        confidence: float — the model's confidence, 0.0..1.0.

    Returns:
        bool — True when the line was written; False on failure (logged) —
        logging must never crash the assistant mid-command.
    """
    if not command or not action:
        return False
    try:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps({
            "command": command.strip(),
            "action": action.strip(),
            "confidence": float(confidence),
        }, ensure_ascii=False)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        return True
    except Exception as e:
        _log(f"could not record decision: {e}")
        return False


def _die(message: str, code: int = 1) -> None:
    """Print to stderr and exit.

    Args:
        message: str — the explanation.
        code:    int — exit code (default 1).
    """
    print(f"[decision-export] {message}", file=sys.stderr)
    sys.exit(code)


def main(argv=None) -> None:
    """CLI entry: read a log, write typed-decisions rows.

    Args:
        argv: list[str] | None — defaults to sys.argv[1:].

    Returns:
        None — exits 0 on success, 1 on missing/bad input.
    """
    p = argparse.ArgumentParser(
        description="Convert Mark-LV command→action logs to typed-decisions "
                    "JSONL for train_decision_model.py.")
    p.add_argument("--input", required=True,
                   help="Source log: .jsonl ({command, action}) or .csv")
    p.add_argument("--output", required=True,
                   help="Destination .jsonl (typed-decisions row schema)")
    p.add_argument("--actions-json", default=None,
                   help="Optional {name: description} JSON; otherwise scans "
                        "actions/*.py via core.action_loader")
    p.add_argument("--workflow", default="marklv_action_router",
                   help="Value for the `workflow` column")
    args = p.parse_args(argv)

    src = Path(args.input)
    if not src.exists():
        _die(f"input file not found: {src}")
    actions = load_action_descriptions(actions_json=args.actions_json)
    if len(actions) < 2:
        _die(f"need at least 2 action descriptions, got {len(actions)}")

    records = _iter_csv(src) if src.suffix.lower() == ".csv" \
        else _iter_jsonl(src)
    rows = convert(records, actions, workflow=args.workflow)
    if not rows:
        _die("no usable rows produced — check the log format")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    _log(f"wrote {len(rows)} rows → {out}")


if __name__ == "__main__":
    main()
