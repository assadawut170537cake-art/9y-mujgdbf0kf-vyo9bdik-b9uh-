"""
Train an Unsloth Decision Model for Mark-LV — the offline router + classifier.

WHAT THIS PRODUCES
    A LoRA-finetuned LLM with a decision head that, given an input and a spec
    of options, returns a calibrated probability for each option (see
    src/services/decision_model.py for the inference-side contract). After
    training, `model.save_pretrained_merged(...)` writes a directory you can
    point DECISION_MODEL_PATH at and serve locally, or hand to `unsloth
    studio` for the HTTP rung.

PLATFORM
    Unsloth requires Linux + CUDA. On this Windows machine, run inside WSL2:

        wsl
        cd /mnt/j/Mark-LV
        python src/helpers/train_decision_model.py --model unsloth/Qwen3.5-0.8B \
            --epochs 2 --lr 2e-4 --output-dir models/marklv-decision-router

RECOMMENDED SETTINGS (from the Unsloth docs, verified on typed-decisions)
    LoRA rank 16, learning rate 2e-4, head learning rate 1e-4 (DecisionTrainer
    default), 2 epochs, 4-bit quantised base, max_seq_length 2048. Qwen3.5-0.8B
    reaches ~78% holdout accuracy in ~42 min on a 4GB card; --max-steps 60 is
    a quick smoke test.

DATASET
    --dataset accepts a HuggingFace dataset id in the typed-decisions row
    format (default: LocalLLaMA/typed-decisions, subset "all"), or a local
    JSONL file of rows in the SAME schema produced by
    src/helpers/decision_data_export.py. Training on your own router rows
    (rather than the generic benchmark mix) is what turns this into a
    command→action specialist for Mark-LV.

INSTALL (inside WSL2, one-time)
    pip install unsloth          # pulls torch + transformers + trl + peft
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def _die(message: str, code: int = 1) -> None:
    """Print a message to stderr and exit.

    Args:
        message: str — the explanation to show the user.
        code:    int — process exit code (default 1).
    """
    print(f"[train-decision] {message}", file=sys.stderr)
    sys.exit(code)


def _check_env() -> None:
    """Verify unsloth and its CUDA backend import, or exit with guidance.

    Runs BEFORE any training code so a broken environment produces one clear
    sentence instead of a 40-line torch traceback.

    Returns:
        None — exits the process on failure.
    """
    try:
        import unsloth  # noqa: F401
    except ImportError as e:
        _die(
            "unsloth is not importable — this script must run under Linux +\n"
            "  CUDA (WSL2 works). In PowerShell:\n"
            "    wsl\n"
            "    pip install unsloth\n"
            f"  Original error: {e}"
        )
    try:
        import torch
        if not torch.cuda.is_available():
            _die(
                "CUDA is not available to torch. Inside WSL2, confirm the\n"
                "  NVIDIA driver is visible with `nvidia-smi`, and that the\n"
                "  torch build is the CUDA one (pip install torch --index-url\n"
                "  https://download.pytorch.org/whl/cu124)."
            )
        print(f"[train-decision] CUDA device: {torch.cuda.get_device_name(0)}")
    except ImportError:
        _die("torch is not importable — `pip install unsloth` should have "
             "pulled it; reinstall inside your WSL2 environment.")


def parse_args(argv=None) -> argparse.Namespace:
    """Parse CLI arguments for the training run.

    Args:
        argv: list[str] | None — argument list (defaults to sys.argv[1:]).

    Returns:
        argparse.Namespace — the parsed arguments.
    """
    p = argparse.ArgumentParser(
        description="Fine-tune an Unsloth Decision Model for Mark-LV.")
    p.add_argument("--model", default="unsloth/Qwen3.5-0.8B",
                   help="Base HF model id (default: unsloth/Qwen3.5-0.8B; "
                        "use unsloth/Qwen3.5-2B for +3% accuracy at 2x VRAM)")
    p.add_argument("--dataset", default="LocalLLaMA/typed-decisions",
                   help="HF dataset id or local JSONL path (typed-decisions "
                        "schema) — default: LocalLLaMA/typed-decisions")
    p.add_argument("--subset", default="all",
                   help="HF dataset config/subset name (default: all)")
    p.add_argument("--split", default="train",
                   help="Dataset split to train on (default: train)")
    p.add_argument("--epochs", type=float, default=2.0,
                   help="Training epochs (default: 2.0)")
    p.add_argument("--lr", type=float, default=2e-4,
                   help="LoRA learning rate (default: 2e-4)")
    p.add_argument("--head-lr", type=float, default=1e-4,
                   help="Decision-head learning rate (default: 1e-4)")
    p.add_argument("--lora-rank", type=int, default=16,
                   help="LoRA rank r (default: 16)")
    p.add_argument("--max-seq-length", type=int, default=2048,
                   help="max_seq_length (default: 2048)")
    p.add_argument("--batch-size", type=int, default=8,
                   help="Per-device batch size (default: 8; halve it and "
                        "double --grad-accum if you run out of VRAM)")
    p.add_argument("--grad-accum", type=int, default=4,
                   help="Gradient accumulation steps (default: 4)")
    p.add_argument("--max-steps", type=int, default=-1,
                   help="Cap total steps (-1 = full epochs; 60 = quick smoke)")
    p.add_argument("--seed", type=int, default=3407,
                   help="Random seed (default: 3407)")
    p.add_argument("--output-dir", default="models/marklv-decision-router",
                   help="Where to save LoRA adapter + merged model "
                        "(default: models/marklv-decision-router)")
    p.add_argument("--no-4bit", action="store_true",
                   help="Disable 4-bit quantisation (needs much more VRAM)")
    return p.parse_args(argv)


def build_model(args):
    """Load the base model and attach the LoRA adapter.

    Args:
        args: argparse.Namespace — parsed CLI arguments.

    Returns:
        tuple — (model, tokenizer) ready for dataset building.
    """
    from unsloth import FastDecisionModel
    print(f"[train-decision] loading {args.model} "
          f"(4bit={not args.no_4bit}, seq_len={args.max_seq_length})")
    model, tokenizer = FastDecisionModel.from_pretrained(
        model_name=args.model,
        max_seq_length=args.max_seq_length,
        load_in_4bit=not args.no_4bit,
    )
    model = FastDecisionModel.get_peft_model(
        model,
        r=args.lora_rank,
        lora_alpha=args.lora_rank,
        lora_dropout=0,
        use_gradient_checkpointing="unsloth",
        random_state=args.seed,
    )
    return model, tokenizer


def load_rows(dataset_arg: str, subset: str, split: str):
    """Load training rows from Hugging Face or a local JSONL file.

    Args:
        dataset_arg: str — HF dataset id, or a path to a .jsonl file in the
                    typed-decisions row schema (see decision_data_export.py).
        subset:      str — HF config/subset name (ignored for local files).
        split:       str — split name (ignored for local files).

    Returns:
        Dataset — a HuggingFace Dataset with the columns needed by
        FastDecisionModel.build_dataset.
    """
    from datasets import load_dataset
    path = Path(dataset_arg)
    if path.exists() and path.is_file():
        print(f"[train-decision] loading local rows from {path}")
        return load_dataset("json", data_files=str(path), split="train")
    print(f"[train-decision] loading HF dataset {dataset_arg} "
          f"(subset={subset}, split={split})")
    return load_dataset(dataset_arg, subset, split=split)


def _build_dataset(dataset, tokenizer, model):
    """Thin wrapper so the module imports without unsloth at import time.

    Args:
        dataset:   Dataset — raw rows.
        tokenizer: tokenizer — the model tokenizer.
        model:     model — the FastDecisionModel instance.

    Returns:
        tuple — (items, report) from FastDecisionModel.build_dataset.
    """
    from unsloth import FastDecisionModel
    return FastDecisionModel.build_dataset(dataset, tokenizer, model)


def _split_holdout(items, seed: int):
    """Holdout split wrapper (same lazy-import rationale as _build_dataset).

    Args:
        items: list — tokenised training items.
        seed:  int — random seed for the split.

    Returns:
        tuple — (train_items, eval_items).
    """
    from unsloth import FastDecisionModel
    return FastDecisionModel.split_holdout(items, seed=seed)


def _calibrate(model, tokenizer, eval_items):
    """Calibration wrapper (same lazy-import rationale as _build_dataset).

    Args:
        model:      model — the trained FastDecisionModel.
        tokenizer:  tokenizer — the model tokenizer.
        eval_items: list — holdout items.

    Returns:
        dict — held-out accuracy, calibration error (ECE), and loss.
    """
    from unsloth import FastDecisionModel
    return FastDecisionModel.calibrate(model, tokenizer, eval_items)


def run_training(args, model, tokenizer, dataset) -> None:
    """Build the dataset, train, calibrate, and save.

    Args:
        args:      argparse.Namespace — parsed CLI arguments.
        model:     model     — the FastDecisionModel with LoRA attached.
        tokenizer: tokenizer — the model's tokenizer.
        dataset:   Dataset   — the raw training rows.

    Returns:
        None — saves the LoRA adapter and merged model under args.output_dir.
        Exits with code 1 on any unrecoverable training error.
    """
    from unsloth import DecisionTrainer, is_bfloat16_supported
    from transformers import TrainingArguments

    print("[train-decision] building tokenised dataset …")
    items, report = _build_dataset(dataset, tokenizer, model)
    print(f"[train-decision] rows: {report['total']} total, "
          f"{report['skipped']} skipped (malformed)")

    train_items, eval_items = _split_holdout(items, args.seed)
    print(f"[train-decision] train/eval split: "
          f"{len(train_items)}/{len(eval_items)}")

    bf16 = is_bfloat16_supported()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    trainer = DecisionTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train_items,
        eval_dataset=eval_items,
        head_learning_rate=args.head_lr,
        args=TrainingArguments(
            per_device_train_batch_size=args.batch_size,
            gradient_accumulation_steps=args.grad_accum,
            num_train_epochs=args.epochs,
            max_steps=args.max_steps,
            learning_rate=args.lr,
            lr_scheduler_type="cosine",
            warmup_steps=10,
            weight_decay=0.01,
            bf16=bf16,
            fp16=not bf16,
            eval_strategy="epoch",
            logging_steps=10,
            output_dir=str(out / "checkpoints"),
            report_to="none",
            seed=args.seed,
        ),
    )

    print("[train-decision] training …")
    started = time.time()
    trainer.train()
    elapsed = time.time() - started
    print(f"[train-decision] finished in {elapsed / 60:.1f} min")

    # Calibration on the holdout: the whole point of a decision model is that
    # its probabilities are trustworthy, so we measure ECE before saving.
    try:
        metrics = _calibrate(model, tokenizer, eval_items)
        print(f"[train-decision] holdout metrics: {json.dumps(metrics)}")
        (out / "metrics.json").write_text(json.dumps(metrics, indent=2))
    except Exception as e:
        print(f"[train-decision] calibration failed ({e}) — continuing; "
              "the model is still usable, you just don't have ECE numbers.")

    # Two exports: the LoRA adapter (small, loadable by unsloth) and the
    # fully merged weights (loadable by plain transformers too).
    model.save_pretrained(str(out / "lora"))
    model.save_pretrained_merged(str(out / "merged"))
    print(f"[train-decision] saved → {out}/lora (adapter) and {out}/merged "
          "(merged; set DECISION_MODEL_PATH to the merged dir)")


def main(argv=None) -> None:
    """Entry point: parse args, check the environment, train, save.

    Args:
        argv: list[str] | None — CLI arguments (defaults to sys.argv[1:]).

    Returns:
        None — exits 0 on success, 1 on environment/training failure.
    """
    args = parse_args(argv)
    _check_env()
    dataset = load_rows(args.dataset, args.subset, args.split)
    model, tokenizer = build_model(args)
    try:
        run_training(args, model, tokenizer, dataset)
    except Exception as e:
        _die(f"training failed: {type(e).__name__}: {e}")
    print("[train-decision] done.")


if __name__ == "__main__":
    main()
