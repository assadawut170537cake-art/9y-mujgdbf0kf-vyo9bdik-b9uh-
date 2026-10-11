"""
Unit tests for src/services/decision_model.py and decision_data_export.py.

Run with:
    python -m pytest tests/test_decision_model.py -v
    (or plain `python tests/test_decision_model.py` — no pytest required)

Covers everything that does NOT need unsloth/torch/GPU: spec validation,
the result envelope, the heuristic rung, the action-spec builder, and the
data exporter round-trip.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.services import decision_model as dm          # noqa: E402
from src.helpers import decision_data_export as exp    # noqa: E402


def _spec() -> dict:
    """A small valid two-field spec for the tests."""
    return {
        "team": {
            "type": "choice",
            "instructions": "Which team should handle this?",
            "criteria": {
                "billing":   "invoices, payments, refunds",
                "technical": "bugs, outages, errors",
                "sales":     "pricing, new plans",
            },
        },
        "refund": {
            "type": "noul",
            "instructions": "Does the customer ask for a refund?",
        },
    }


def _env(name: str, value) -> None:
    """Set (or clear) an environment variable for one test."""
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


# ── validate_spec ────────────────────────────────────────────────────────────

def test_validate_spec_accepts_good_spec():
    ok, reason = dm.validate_spec(_spec())
    assert ok and reason == ""


def test_validate_spec_rejects_non_dict():
    ok, reason = dm.validate_spec("not a dict")
    assert not ok and "non-empty dict" in reason


def test_validate_spec_rejects_bad_type():
    bad = _spec()
    bad["team"]["type"] = "regression"
    ok, reason = dm.validate_spec(bad)
    assert not ok and "type must be one of" in reason


def test_validate_spec_rejects_choice_with_one_option():
    bad = {"x": {"type": "choice", "instructions": "q",
                 "criteria": {"only": "one"}}}
    ok, reason = dm.validate_spec(bad)
    assert not ok and "at least 2 options" in reason


def test_validate_spec_rejects_missing_instructions():
    bad = {"x": {"type": "noul"}}
    ok, reason = dm.validate_spec(bad)
    assert not ok and "instructions" in reason


# ── envelope + confidence ────────────────────────────────────────────────────

def test_pack_needs_fallback_below_threshold():
    # Default threshold is 0.55: exactly 0.55 passes, 0.50 flags.
    answers = {"a": {"answer": "x", "probabilities": {"x": 0.55, "y": 0.45}}}
    out = dm._pack(answers, "heuristic")
    assert out["confidence"] == 0.55
    assert out["needs_fallback"] is False
    answers2 = {"a": {"answer": "x", "probabilities": {"x": 0.4, "y": 0.5}}}
    assert dm._pack(answers2, "heuristic")["needs_fallback"] is True


def test_pack_no_fallback_when_confident():
    answers = {"a": {"answer": "x", "probabilities": {"x": 0.9, "y": 0.1}}}
    out = dm._pack(answers, "local")
    assert out["confidence"] == 0.9
    assert out["needs_fallback"] is False


def test_confidence_is_min_across_fields():
    # Top prob per field: a=0.95, b=0.80 → overall confidence is min = 0.80.
    answers = {
        "a": {"answer": "x", "probabilities": {"x": 0.95, "y": 0.05}},
        "b": {"answer": "t", "probabilities": {"true": 0.2, "false": 0.8}},
    }
    assert dm._confidence_of(answers) == 0.8


def test_confidence_zero_when_no_probs():
    assert dm._confidence_of({"a": {"answer": "x", "probabilities": {}}}) == 0.0


def test_normalize_answers_drops_malformed_fields():
    raw = {
        "good": {"answer": "x", "probabilities": {"x": 1.0}},
        "bad":  "not a dict",
        "none": {"answer": None},
    }
    assert set(dm._normalize_answers(raw)) == {"good"}


def test_normalize_answers_argmax_when_no_answer():
    raw = {"f": {"probabilities": {"low": 0.1, "high": 0.9}}}
    assert dm._normalize_answers(raw)["f"]["answer"] == "high"


# ── heuristic rung ───────────────────────────────────────────────────────────

def test_heuristic_picks_best_keyword_match():
    out = dm._heuristic_predict("please refund my invoice", _spec())
    assert out["team"]["answer"] == "billing"
    assert out["refund"]["answer"] == "true"


def test_heuristic_respects_negation():
    out = dm._heuristic_predict("do not refund this", _spec())
    assert out["refund"]["answer"] == "false"


def test_heuristic_uniform_when_no_overlap():
    probs = dm._heuristic_predict("zzz qqq", _spec())["team"]["probabilities"]
    assert abs(max(probs.values()) - 1 / 3) < 0.01


# ── decide() ladder ──────────────────────────────────────────────────────────

def test_decide_empty_input_returns_safe_envelope():
    out = dm.decide("   ", _spec())
    assert out["answers"] == {}
    assert out["needs_fallback"] is True


def test_decide_invalid_spec_returns_safe_envelope():
    out = dm.decide("hello", {"bad": "spec"})
    assert out["answers"] == {}
    assert out["needs_fallback"] is True


def test_decide_heuristic_rung_only():
    out = dm.decide("refund my invoice please", _spec(), rungs=("heuristic",))
    assert out["source"] == "heuristic"
    assert out["answers"]["team"]["answer"] == "billing"


def test_decide_no_available_rungs_yields_none_source():
    # No model, no studio → source=none, never a crash. Gemini is excluded so
    # the test makes no network call.
    out = dm.decide("anything", _spec(), rungs=("local", "studio"))
    assert out["source"] == "none"
    assert out["needs_fallback"] is True


# ── build_action_spec / route_action ─────────────────────────────────────────

def test_build_action_spec_truncates_long_descriptions():
    spec = dm.build_action_spec([("a", "x" * 500), ("b", "short")])
    assert len(spec["action"]["criteria"]["a"]) <= 200


def test_build_action_spec_needs_two_actions():
    assert dm.build_action_spec([("only", "one")]) == {}


def test_route_action_action_mirrors_fallback():
    actions = [
        ("open_app",   "Launch a desktop application by name."),
        ("web_search", "Search the web for news or facts."),
        ("reminder",   "Set a time-based reminder."),
    ]
    out = dm.route_action("open chrome", actions, rungs=("heuristic",))
    assert out["answers"]["action"]["answer"] == "open_app"
    # The contract: "action" is set exactly when the decision is confident.
    assert (out["action"] is None) == out["needs_fallback"]


# ── exporter round-trip ──────────────────────────────────────────────────────

def test_exporter_convert_produces_rows():
    actions = {"open_app": "Launch an app.", "web_search": "Search the web."}
    records = [
        {"command": "open chrome", "action": "open_app"},
        {"command": "ค้นหาข่าว", "action": "web_search"},
        {"command": "x", "action": "not_real"},      # skipped
        {"command": "", "action": "open_app"},       # skipped
    ]
    rows = exp.convert(records, actions)
    assert len(rows) == 2
    assert rows[0]["action__label"] == "open_app"
    assert json.loads(rows[0]["state"])["task"] == "open chrome"
    assert json.loads(rows[1]["state"])["task"] == "ค้นหาข่าว"
    assert rows[0]["split"] == "train"
    questions = json.loads(rows[0]["questions"])
    assert questions["action"]["type"] == "choice"
    assert set(questions["action"]["criteria"]) == {"open_app", "web_search"}


def test_exporter_one_hot_probabilities():
    actions = {"a": "one", "b": "two"}
    rows = exp.convert([{"command": "x", "action": "b"}], actions)
    assert json.loads(rows[0]["action__probabilities"]) == {"a": 0.0, "b": 1.0}


def test_exporter_jsonl_round_trip_with_bad_line():
    actions = {"a": "one", "b": "two"}
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "log.jsonl"
        src.write_text(
            '{"command": "hi", "action": "a"}\n'
            '{broken json\n'
            '{"command": "yo", "action": "b"}\n',
            encoding="utf-8")
        rows = list(exp._iter_jsonl(src))
        assert len(rows) == 2                      # broken line skipped
        assert len(exp.convert(rows, actions)) == 2


def test_exporter_record_decision_writes_line():
    with tempfile.TemporaryDirectory() as td:
        log = Path(td) / "sub" / "decisions.jsonl"
        ok = exp.record_decision(str(log), "open chrome", "open_app", 0.9)
        assert ok is True
        lines = log.read_text(encoding="utf-8").splitlines()
        assert json.loads(lines[0])["action"] == "open_app"


def test_exporter_record_decision_rejects_blank():
    assert exp.record_decision("x.jsonl", "", "a") is False


def test_make_id_is_unique_and_safe():
    a = exp._make_id("open chrome", 1)
    b = exp._make_id("open chrome", 2)
    assert a != b and a.startswith("marklv_router_000001_")
    thai = exp._make_id("เปิด chrome", 3)
    assert thai.startswith("marklv_router_000003_")


# ── config getters ───────────────────────────────────────────────────────────

def test_min_confidence_parses_and_clamps():
    _env("DECISION_MIN_CONFIDENCE", "0.8")
    assert dm.get_min_confidence() == 0.8
    _env("DECISION_MIN_CONFIDENCE", "5")
    assert dm.get_min_confidence() == 1.0
    _env("DECISION_MIN_CONFIDENCE", "not-a-number")
    assert dm.get_min_confidence() == 0.55
    _env("DECISION_MIN_CONFIDENCE", None)


def test_studio_url_strips_trailing_slash():
    _env("UNSLOTH_DECISION_URL", "http://localhost:8888/")
    assert dm.get_studio_url() == "http://localhost:8888"
    _env("UNSLOTH_DECISION_URL", None)


if __name__ == "__main__":
    # Run every test_* function in this module without pytest.
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok   {name}")
            except AssertionError as e:
                failures += 1
                print(f"  FAIL {name}: {e}")
            except Exception as e:
                failures += 1
                print(f"  ERROR {name}: {type(e).__name__}: {e}")
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)
