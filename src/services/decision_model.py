"""
Offline Decision Model service — the Unsloth Decision Model integration.

WHY THIS EXISTS
    The assistant routes every one-line decision through Gemini (the FAST
    ladder in core/gemini.py). That costs quota — the pool that demonstrably
    runs dry on the free tier — and needs the network. Unsloth's Decision
    Models (Jev / Laya / Clef line) are LLMs fine-tuned with a classification
    head so they do not generate text; they SCORE the options you give them
    and return a choice plus a calibrated probability. A small one
    (Qwen3.5-0.8B, 4-bit) fits in ~4 GB VRAM — see
    docs/unsloth-decision-model.md.

    This module adds that as ONE MORE RUNG in front of Gemini, never as a
    replacement. The ladder, tried left to right:

        1. LOCAL     — an Unsloth decision model on this machine (needs
                       DECISION_MODEL_PATH + `unsloth` installed)
        2. STUDIO    — an `unsloth studio` HTTP server (UNSLOTH_DECISION_URL)
        3. GEMINI    — the existing core.gemini FAST ladder, same spec
        4. HEURISTIC — keyword overlap of input vs option criteria. No
                       network, no model, no quota. Always answers something
                       rather than raising: a router that crashes is worse
                       than a router that guesses.

    Every rung returns the SAME answer shape, so callers never care which
    machine actually decided:

        {
            "answers": {
                "<field>": {
                    "answer":        "<option label or yes/no>",
                    "probabilities": {"<option>": 0.0..1.0, ...},
                },
            },
            "source":         "local" | "studio" | "gemini" | "heuristic",
            "confidence":     0.0..1.0,   # weakest top-probability
            "needs_fallback": bool,       # True = confidence too low for an
                                          # unattended action; escalate
        }

THE SPEC (mirrors the typed-decisions format the models are trained on)
    {
        "team": {
            "type":         "choice",           # one of several options
            "instructions": "Which team should handle this?",
            "criteria": {                        # label -> what it means
                "billing":   "invoices, payments, refunds",
                "technical": "bugs, outages, errors",
            },
        },
        "refund": {
            "type":         "noul",             # yes/no style field
            "instructions": "Does the customer ask for a refund?",
        },
    }

CONFIG (master .env at the repo root — never a local .env)
    DECISION_MODEL_PATH      saved model dir (train_decision_model.py output)
    UNSLOTH_DECISION_URL     base URL of `unsloth studio`, e.g. localhost:8888
    DECISION_MIN_CONFIDENCE  below this, needs_fallback flips True (0.55)

    All three optional. With none set the service still works through the
    Gemini and heuristic rungs.

This module must import WITHOUT torch/unsloth installed; every heavy import
is lazy and guarded at the point of use, matching the plugin-extras contract
in requirements.txt.
"""
from __future__ import annotations

import os
import re
import sys
import threading
from pathlib import Path
from typing import Iterable, Optional

# Load environment variables from .env (master key file) — same pattern as
# memory/config_manager.py and main.py.
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path, override=False)
except ImportError:
    pass


def get_base_dir() -> Path:
    """Project root, whether running from source or a frozen exe.

    Returns:
        Path — the directory containing main.py / the executable.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent


BASE_DIR = get_base_dir()

# Spec field types the trained models understand.
_CHOICE = "choice"
_NOUL = "noul"
_FIELD_TYPES = (_CHOICE, _NOUL)

# Negation words the heuristic rung checks before answering "true".
_NEGATIONS = ("not", "no ", "never", "don't", "dont", "doesn't", "doesnt",
              "isn't", "isnt", "wasn't", "wasnt", "cannot", "can't", "cant",
              "shouldn't", "shouldnt", "without")


def _log(message: str) -> None:
    """Print with a stable prefix so decision traffic is greppable in the log.

    Args:
        message: str — the text to print.
    """
    print(f"[Decision] {message}")


# ── Config ───────────────────────────────────────────────────────────────────

def get_model_path() -> str:
    """Path of the locally saved decision model, or "" when unset.

    Returns:
        str — DECISION_MODEL_PATH from the master .env, stripped; "" if absent.
    """
    return os.getenv("DECISION_MODEL_PATH", "").strip()


def get_studio_url() -> str:
    """Base URL of an `unsloth studio` server, or "" when unset.

    Returns:
        str — UNSLOTH_DECISION_URL from the master .env (no trailing slash);
              "" if absent.
    """
    return os.getenv("UNSLOTH_DECISION_URL", "").strip().rstrip("/")


def get_min_confidence() -> float:
    """Probability below which a decision is flagged for fallback.

    Returns:
        float — DECISION_MIN_CONFIDENCE (default 0.55), clamped to [0.0, 1.0].
    """
    raw = os.getenv("DECISION_MIN_CONFIDENCE", "0.55").strip()
    try:
        value = float(raw)
    except (TypeError, ValueError):
        _log(f"DECISION_MIN_CONFIDENCE={raw!r} is not a number — using 0.55")
        return 0.55
    return min(1.0, max(0.0, value))


# ── Spec validation ──────────────────────────────────────────────────────────

def validate_spec(spec) -> tuple[bool, str]:
    """Check a decision spec is well-formed before any rung sees it.

    A malformed spec would otherwise crash four different backends in four
    different ways; failing once, here, with one message is cheaper.

    Args:
        spec: Any — expected dict[field -> {"type", "instructions", ...}].

    Returns:
        tuple[bool, str] — (is_valid, reason). reason is "" when valid.
    """
    if not isinstance(spec, dict) or not spec:
        return False, "spec must be a non-empty dict"
    for field_name, cfg in spec.items():
        if not isinstance(field_name, str) or not field_name.strip():
            return False, f"field name {field_name!r} is not a non-empty string"
        if not isinstance(cfg, dict):
            return False, f"field {field_name!r}: config must be a dict"
        ftype = cfg.get("type")
        if ftype not in _FIELD_TYPES:
            return False, (f"field {field_name!r}: type must be one of "
                           f"{_FIELD_TYPES}, got {ftype!r}")
        instructions = cfg.get("instructions")
        if not isinstance(instructions, str) or not instructions.strip():
            return False, f"field {field_name!r}: instructions missing/empty"
        if ftype == _CHOICE:
            criteria = cfg.get("criteria")
            if not isinstance(criteria, dict) or len(criteria) < 2:
                return False, (f"field {field_name!r}: choice needs a criteria "
                               "dict with at least 2 options")
            for label, meaning in criteria.items():
                if not isinstance(label, str) or not label.strip():
                    return False, f"field {field_name!r}: blank option label"
                if not isinstance(meaning, str) or not meaning.strip():
                    return False, (f"field {field_name!r}: option {label!r} "
                                   "has an empty description")
    return True, ""


# ── Result shaping ───────────────────────────────────────────────────────────

def _normalize_answers(raw) -> dict:
    """Coerce any rung's raw output into {field: {answer, probabilities}}.

    Accepts the shapes seen in the wild: FastDecisionModel.predict output,
    studio JSON bodies, and gemini's JSON. Malformed fields are dropped rather
    than raised on — a partially useful decision beats an exception.

    Args:
        raw: Any — the rung's raw answer mapping (or None).

    Returns:
        dict — {field: {"answer": str, "probabilities": dict}}; {} if raw is
        not a dict.
    """
    if not isinstance(raw, dict):
        return {}
    out: dict = {}
    for field_name, value in raw.items():
        if not isinstance(value, dict):
            continue
        answer = value.get("answer", value.get("label"))
        probs = value.get("probabilities")
        if answer is None and isinstance(probs, dict) and probs:
            # No explicit answer — take the argmax of the probabilities.
            try:
                answer = max(probs.items(), key=lambda kv: float(kv[1]))[0]
            except (TypeError, ValueError):
                answer = None
        if answer is None:
            continue
        clean_probs: dict = {}
        if isinstance(probs, dict):
            for opt, p in probs.items():
                try:
                    clean_probs[str(opt)] = float(p)
                except (TypeError, ValueError):
                    continue
        out[str(field_name)] = {"answer": str(answer),
                                "probabilities": clean_probs}
    return out


def _confidence_of(answers: dict) -> float:
    """The weakest link: the MINIMUM top-probability across all fields.

    A two-field decision is only as sure as its least sure field, so the
    overall confidence is the minimum, not the mean — a 0.95 on one field
    must not launder a 0.20 on another.

    Args:
        answers: dict — normalized answers from _normalize_answers().

    Returns:
        float — 0.0..1.0; 0.0 when any field carries no probabilities (the
        source did not calibrate, so nothing is claimed).
    """
    if not answers:
        return 0.0
    worst = 1.0
    for value in answers.values():
        probs = value.get("probabilities") or {}
        if not probs:
            return 0.0
        try:
            top = max(float(p) for p in probs.values())
        except (TypeError, ValueError):
            return 0.0
        worst = min(worst, top)
    return worst


def _pack(answers: dict, source: str) -> dict:
    """Assemble the public result envelope.

    Args:
        answers: dict — normalized answers.
        source:  str — which rung answered ("local"/"studio"/"gemini"/"heuristic").

    Returns:
        dict — the full result documented in the module docstring.
    """
    confidence = _confidence_of(answers)
    return {
        "answers": answers,
        "source": source,
        "confidence": round(confidence, 4),
        "needs_fallback": confidence < get_min_confidence(),
    }


# ── Rung 1: local Unsloth model ──────────────────────────────────────────────

class _LocalModel:
    """Lazily-loaded local Unsloth decision model (one per process).

    Loading costs seconds and VRAM, so the model is loaded on first use and
    reused. Every attribute access is wrapped: a broken install, a missing
    CUDA device, or a half-copied model directory must degrade to "rung
    unavailable", never to a crash in the caller's thread.
    """

    def __init__(self) -> None:
        self._model = None
        self._tokenizer = None
        self._lock = threading.Lock()
        self._failed = False          # sticky: a failed load is not retried

    def available(self) -> bool:
        """Whether a loadable local model exists (path set, unsloth installed).

        Returns:
            bool — True only when DECISION_MODEL_PATH points somewhere real and
            `unsloth` imports.
        """
        if self._failed:
            return False
        path = get_model_path()
        if not path or not Path(path).exists():
            return False
        try:
            import unsloth  # noqa: F401
            return True
        except Exception:
            return False

    def predict(self, input_text: str, spec: dict) -> Optional[dict]:
        """Run the local model on one input.

        Args:
            input_text: str — the text to classify (a command, a ticket…).
            spec:       dict — the decision spec (see module docstring).

        Returns:
            dict | None — raw model output, or None when the model is
            unavailable or the call failed (logged, never raised).
        """
        if not self.available():
            return None
        with self._lock:
            try:
                if self._model is None:
                    from unsloth import FastDecisionModel
                    path = get_model_path()
                    _log(f"loading local decision model from {path} …")
                    self._model, self._tokenizer = \
                        FastDecisionModel.from_pretrained(
                            path, load_in_4bit=True)
                    FastDecisionModel.for_inference(self._model)
                    _log("local decision model ready")
                return FastDecisionModel.predict(
                    self._model, self._tokenizer, input_text, spec)
            except Exception as e:
                self._failed = True          # do not retry a broken load
                _log(f"local model failed ({type(e).__name__}: {e}) — "
                     "disabling this rung for the session")
                return None


_local = _LocalModel()


# ── Rung 2: unsloth studio HTTP ──────────────────────────────────────────────

def _studio_predict(input_text: str, spec: dict,
                    timeout: float = 10.0) -> Optional[dict]:
    """Ask an `unsloth studio` server for a decision.

    Args:
        input_text: str  — the text to classify.
        spec:       dict — the decision spec.
        timeout:    float — seconds before giving up (default 10.0).

    Returns:
        dict | None — raw answer mapping, or None on any connection/shape
        failure (logged, never raised).
    """
    url = get_studio_url()
    if not url:
        return None
    try:
        import requests
        resp = requests.post(
            f"{url}/predict",
            json={"input": input_text, "spec": spec},
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        _log(f"studio at {url} failed ({type(e).__name__}: {e}) — "
             "skipping this rung for this call")
        return None


# ── Rung 3: Gemini, same spec ────────────────────────────────────────────────

def _spec_to_prompt(spec: dict) -> str:
    """Render a spec as instructions for a general LLM (Gemini fallback).

    Args:
        spec: dict — the decision spec.

    Returns:
        str — a prompt asking for STRICT JSON in the normalized answer shape.
    """
    lines = [
        "Classify the input below. Reply with ONLY a JSON object, no prose,",
        "in this exact shape:",
        '{"<field>": {"answer": "<option>", "probabilities": '
        '{"<option>": 0-1}}, ...}',
        "",
    ]
    for field_name, cfg in spec.items():
        lines.append(f"Field '{field_name}': {cfg['instructions']}")
        if cfg["type"] == _CHOICE:
            lines.append("Options (label — meaning):")
            for label, meaning in cfg["criteria"].items():
                lines.append(f"  - {label}: {meaning}")
            lines.append("Probabilities must sum to ~1.0 across the options.")
        else:
            lines.append('Type is yes/no. Answer "true" or "false" with '
                         'probabilities {"true": x, "false": 1-x}.')
        lines.append("")
    return "\n".join(lines)


def _gemini_predict(input_text: str, spec: dict,
                    timeout_ms: int = 15000) -> Optional[dict]:
    """Classify with Gemini through the existing core.gemini FAST ladder.

    Import is deferred and guarded: this service must import cleanly in a
    bare venv (tests, training boxes) where neither google-genai nor the app
    package layout is present.

    Args:
        input_text: str  — the text to classify.
        spec:       dict — the decision spec.
        timeout_ms: int  — per-call deadline (default 15000).

    Returns:
        dict | None — raw JSON answer, or None when Gemini did not answer.
    """
    try:
        if str(BASE_DIR) not in sys.path:
            sys.path.insert(0, str(BASE_DIR))
        from core import gemini as _gemini
        prompt = _spec_to_prompt(spec) + "\nInput:\n" + input_text[:8000]
        return _gemini.as_json(
            [prompt], tier=_gemini.FAST, timeout_ms=timeout_ms)
    except Exception as e:
        _log(f"gemini fallback failed ({type(e).__name__}: {e})")
        return None


# ── Rung 4: keyword heuristic ────────────────────────────────────────────────

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set:
    """Lowercase alphanumeric word set for keyword overlap.

    Args:
        text: str — any input text.

    Returns:
        set — words of length >= 3 (drops "the", "a"). Thai text arrives as
        long spaceless runs, which is good enough for a last-resort rung.
    """
    return {w for w in _WORD_RE.findall(text.lower()) if len(w) >= 3}


def _heuristic_predict(input_text: str, spec: dict) -> dict:
    """Keyword-overlap classifier. No model, no network — always answers.

    For choice fields: scores each option by how many of its criteria words
    appear in the input and normalizes to a distribution. For noul fields:
    answers "true" unless a negation word is present. Deliberately crude; it
    exists so the router still functions with no GPU, no model and no quota.

    Args:
        input_text: str — the text to classify.
        spec:       dict — the decision spec.

    Returns:
        dict — {field: {"answer": str, "probabilities": dict}}.
    """
    words = _tokens(input_text)
    # Prefix (first 4+ chars) as well as exact tokens, so "invoice" matches
    # "invoices" and "refund" matches "refunded" — criteria text is written
    # in plural/generic forms while commands are singular and specific.
    prefixes = {w[:4] for w in words if len(w) >= 4}

    def _hits(keys: set) -> int:
        """Count how many criteria keys appear in the input (exact or prefix).

        Args:
            keys: set — tokenized criteria words (length >= 3).

        Returns:
            int — number of keys found in the input.
        """
        n = 0
        for k in keys:
            if k in words or (len(k) >= 4 and k[:4] in prefixes):
                n += 1
        return n

    out: dict = {}
    for field_name, cfg in spec.items():
        if cfg["type"] == _CHOICE:
            scores: dict = {}
            for label, meaning in cfg["criteria"].items():
                keys = _tokens(label + " " + meaning)
                scores[label] = float(_hits(keys))
            total = sum(scores.values())
            if total <= 0:
                # Nothing matched: uniform, so confidence lands low and
                # needs_fallback flips — the honest answer is "I don't know".
                n = max(1, len(scores))
                probs = {label: round(1.0 / n, 4) for label in scores}
            else:
                probs = {label: round(s / total, 4)
                         for label, s in scores.items()}
            answer = max(probs.items(), key=lambda kv: kv[1])[0]
            out[field_name] = {"answer": answer, "probabilities": probs}
        else:  # noul
            low = " " + input_text.lower() + " "
            negated = any(n in low for n in _NEGATIONS)
            p_true = 0.2 if negated else 0.8
            out[field_name] = {
                "answer": "false" if negated else "true",
                "probabilities": {"true": p_true,
                                  "false": round(1 - p_true, 4)},
            }
    return out


# ── Public API ───────────────────────────────────────────────────────────────

def decide(input_text: str, spec: dict,
           rungs: Optional[Iterable[str]] = None) -> dict:
    """Classify `input_text` against `spec`, walking the fallback ladder.

    Args:
        input_text: str            — the text to classify. Must be non-empty.
        spec:       dict           — decision spec; validated first, and an
                                     invalid spec returns an empty result with
                                     "answers": {} rather than raising.
        rungs:      Iterable[str] | None — restrict the ladder for testing;
                                     subset of {"local","studio","gemini",
                                     "heuristic"}. None = all four.

    Returns:
        dict — {"answers", "source", "confidence", "needs_fallback"} as
        documented in the module header. "source" is "none" if every rung
        failed (only possible when `rungs` excludes "heuristic").
    """
    if not isinstance(input_text, str) or not input_text.strip():
        _log("decide() called with empty input — returning empty result")
        return {"answers": {}, "source": "none", "confidence": 0.0,
                "needs_fallback": True}

    ok, reason = validate_spec(spec)
    if not ok:
        _log(f"invalid spec: {reason}")
        return {"answers": {}, "source": "none", "confidence": 0.0,
                "needs_fallback": True}

    wanted = set(rungs) if rungs else {"local", "studio", "gemini", "heuristic"}
    text = input_text.strip()

    if "local" in wanted and _local.available():
        answers = _normalize_answers(_local.predict(text, spec))
        if answers:
            return _pack(answers, "local")

    if "studio" in wanted and get_studio_url():
        answers = _normalize_answers(_studio_predict(text, spec))
        if answers:
            return _pack(answers, "studio")

    if "gemini" in wanted:
        answers = _normalize_answers(_gemini_predict(text, spec))
        if answers:
            return _pack(answers, "gemini")

    if "heuristic" in wanted:
        answers = _normalize_answers(_heuristic_predict(text, spec))
        if answers:
            return _pack(answers, "heuristic")

    _log("every rung failed — returning empty result")
    return {"answers": {}, "source": "none", "confidence": 0.0,
            "needs_fallback": True}


def build_action_spec(
    actions: Iterable[tuple],
    field_name: str = "action",
    instructions: str = "Which action should handle this command?",
    max_description_chars: int = 200,
) -> dict:
    """Build a choice spec that routes a command to one of Mark-LV's actions.

    Args:
        actions:  Iterable[tuple[str, str]] — (name, description) pairs, e.g.
                  from ActionRegistry records.
        field_name: str — the spec field to create ("action" by default).
        instructions: str — the routing question the model answers.
        max_description_chars: int — descriptions are hard-truncated to this
                  (typed-decisions criteria stay short; a 1500-char
                  description would blow the sequence budget before the
                  question even starts).

    Returns:
        dict — a valid choice spec; {} when fewer than 2 usable actions.
    """
    criteria: dict = {}
    for name, description in actions:
        if not isinstance(name, str) or not name.strip():
            continue
        clean = (description or "").strip().replace("\n", " ")
        criteria[name.strip()] = clean[:max_description_chars] or name.strip()
    if len(criteria) < 2:
        _log(f"build_action_spec: only {len(criteria)} usable action(s) — "
             "need at least 2; returning {}")
        return {}
    return {field_name: {
        "type": _CHOICE,
        "instructions": instructions,
        "criteria": criteria,
    }}


def route_action(command: str, actions: Iterable[tuple],
                 rungs: Optional[Iterable[str]] = None) -> dict:
    """Route one user command to one of the app's actions, offline-first.

    Args:
        command: str                      — what the user said/typed.
        actions: Iterable[tuple[str,str]] — (name, description) pairs of the
                                            discoverable actions.
        rungs:   Iterable[str] | None     — forwarded to decide(); restrict
                                            the ladder (mainly for tests).

    Returns:
        dict — decide()'s result envelope plus a convenience key "action"
        (str | None): the routed action name when confident, else None so
        the caller can escalate to Gemini Live.
    """
    spec = build_action_spec(actions)
    if not spec:
        return {"answers": {}, "source": "none", "confidence": 0.0,
                "needs_fallback": True, "action": None}
    result = decide(command, spec, rungs=rungs)
    field = next(iter(spec))
    entry = result["answers"].get(field)
    result["action"] = (entry["answer"]
                        if (entry and not result["needs_fallback"])
                        else None)
    return result


def is_ready() -> bool:
    """Whether the LOCAL rung (model file + unsloth) is present.

    Returns:
        bool — True when a local decision model can answer without network.
    """
    return _local.available()


def status() -> str:
    """One-line human-readable status of the four rungs (for HUD/debug).

    Returns:
        str — e.g. "local=off studio=off gemini=maybe heuristic=on".
    """
    return (
        f"local={'on' if _local.available() else 'off'} "
        f"studio={'on' if get_studio_url() else 'off'} "
        "gemini=maybe "
        f"heuristic=on "
        f"min_confidence={get_min_confidence():.2f}"
    )
