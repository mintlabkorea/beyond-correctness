#!/usr/bin/env python3
"""Run the review-triggered TransTab C-only extension on frozen MCR cells."""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import random
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SEMANTIC_RUNNER = ROOT / "scripts/run_crta_v3_mcr_carte_v1.py"
PROTOCOL = ROOT / "iclr_latex_v3/MCR_TRANSTAB_C_REVIEW_EXTENSION_V1.md"
DEFAULT_INPUT = Path("._data/nhanes_common_panel_tokens_v2.parquet")
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_transtab_c_v1"

EXPECTED_SEMANTIC_RUNNER_SHA256 = (
    "38d82262de030668eb5997d1327193d82bd71cc0f98f275be9fe135826031d86"
)
EXPECTED_TRANSTAB_COMMIT = "fdb34cf38abda73ee6a741b802fe226cc89ba7b5"
EXPECTED_TRANSTAB_TREE_SHA256 = (
    "6db3ddac43009ff15e0bc6b2f34f0cc900c39c632c323413840fc1c84b83f80e"
)
FAMILIES = ("additive", "pairwise", "sparse")
SUPPORTS = (32, 512)
N_REALIZATIONS = 20
ARMS = ("correct", "c_wrong", "c_reference")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def transtab_tree_hash(root: Path) -> str:
    tokenizer = root / "transtab" / "tokenizer"
    paths = sorted(
        list((root / "transtab").rglob("*.py"))
        + [
            tokenizer / "special_tokens_map.json",
            tokenizer / "tokenizer_config.json",
            tokenizer / "vocab.txt",
            root / "setup.py",
            root / "requirements.txt",
        ]
    )
    if any(not path.is_file() for path in paths):
        raise FileNotFoundError(f"incomplete TransTab source tree: {root}")
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def stable_frame_hash(frame: pd.DataFrame, y: np.ndarray | None = None) -> str:
    digest = hashlib.sha256()
    digest.update("\x1f".join(map(str, frame.columns)).encode("utf-8"))
    digest.update(pd.util.hash_pandas_object(frame, index=False).to_numpy().tobytes())
    if y is not None:
        digest.update(np.asarray(y, dtype=np.float64).tobytes())
    return digest.hexdigest()


def load_semantic_runner():
    observed = sha256_file(SEMANTIC_RUNNER)
    if observed != EXPECTED_SEMANTIC_RUNNER_SHA256:
        raise RuntimeError(
            f"semantic runner hash mismatch: {observed}; expected "
            f"{EXPECTED_SEMANTIC_RUNNER_SHA256}"
        )
    spec = importlib.util.spec_from_file_location("mcr_transtab_semantics", SEMANTIC_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {SEMANTIC_RUNNER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def import_transtab(source: Path):
    observed = transtab_tree_hash(source)
    if observed != EXPECTED_TRANSTAB_TREE_SHA256:
        raise RuntimeError(
            f"TransTab source hash mismatch: {observed}; expected "
            f"{EXPECTED_TRANSTAB_TREE_SHA256}"
        )
    sys.path.insert(0, str(source))
    import transtab
    import transtab.trainer as trainer_module
    from torch.utils.data import Dataset

    class FixedTrainDataset(Dataset):
        """Upstream-compatible dataset with the one-row indexing typo corrected."""

        def __init__(self, trainset):
            self.x, self.y = trainset

        def __len__(self):
            return len(self.x)

        def __getitem__(self, index):
            x = self.x.iloc[index : index + 1]
            y = self.y.iloc[index : index + 1] if self.y is not None else None
            return x, y

    trainer_module.TrainDataset = FixedTrainDataset
    return transtab


def set_seed(seed: int) -> None:
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def raw_regression_predict(model: Any, frame: pd.DataFrame, batch_size: int) -> np.ndarray:
    import torch

    model.eval()
    chunks: list[np.ndarray] = []
    for start in range(0, len(frame), batch_size):
        batch = frame.iloc[start : start + batch_size]
        with torch.no_grad():
            output, _ = model(batch)
        chunks.append(output.detach().cpu().numpy().reshape(-1))
    prediction = np.concatenate(chunks).astype(np.float64, copy=False)
    if len(prediction) != len(frame) or not np.isfinite(prediction).all():
        raise RuntimeError("invalid TransTab regression prediction")
    return prediction


def fit_predict(
    transtab: Any,
    source_x: pd.DataFrame,
    source_y: np.ndarray,
    support_x: pd.DataFrame,
    support_y: np.ndarray,
    query_x: pd.DataFrame,
    seed: int,
    args: argparse.Namespace,
) -> tuple[np.ndarray, dict[str, float]]:
    import torch

    set_seed(seed)
    label_mean = float(np.mean(source_y))
    label_scale = float(np.std(source_y, ddof=0))
    if not np.isfinite(label_scale) or label_scale <= 0:
        raise RuntimeError("invalid source label scale")
    source_scaled = (np.asarray(source_y, dtype=np.float64) - label_mean) / label_scale
    support_scaled = (np.asarray(support_y, dtype=np.float64) - label_mean) / label_scale
    numerical = sorted(set(source_x.columns) | set(support_x.columns))
    model = transtab.build_regressor(
        categorical_columns=[],
        numerical_columns=numerical,
        binary_columns=[],
        hidden_dim=128,
        num_layer=2,
        num_attention_head=8,
        hidden_dropout_prob=0,
        ffn_dim=256,
        activation="relu",
        device=args.device,
    )
    trainset = [
        (source_x.reset_index(drop=True), pd.Series(source_scaled.astype(np.float32))),
        (support_x.reset_index(drop=True), pd.Series(support_scaled.astype(np.float32))),
    ]
    with tempfile.TemporaryDirectory(prefix="mcr_transtab_c_") as checkpoint:
        transtab.train(
            model,
            trainset,
            valset=None,
            num_epoch=args.num_epoch,
            batch_size=args.batch_size,
            eval_batch_size=args.eval_batch_size,
            lr=args.learning_rate,
            weight_decay=0.0,
            output_dir=checkpoint,
            num_workers=0,
            load_best_at_last=False,
        )
    standardized = raw_regression_predict(model, query_x, args.eval_batch_size)
    prediction = standardized * label_scale + label_mean
    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return prediction, {"source_label_mean": label_mean, "source_label_scale": label_scale}


def prepare_frames(semantic: Any, source: pd.DataFrame, support: pd.DataFrame,
                   query: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    source_state = semantic.fit_domain_state(source)
    target_state = semantic.fit_domain_state(support)
    return (
        semantic.apply_domain_state(source, source_state),
        semantic.apply_domain_state(support, target_state),
        semantic.apply_domain_state(query, target_state),
    )


def run_realization(semantic: Any, parent: Any, panel: Any, transtab: Any,
                    family: str, realization: int,
                    args: argparse.Namespace) -> dict[str, Any]:
    cell = parent.build_cell(panel, "primary", family, realization, tuple(args.supports))
    source_y = np.asarray(cell.y[cell.source_rows], dtype=np.float64)
    query_y = np.asarray(cell.y[cell.query_rows], dtype=np.float64)
    query_var = float(np.var(query_y, ddof=0))
    if not np.isfinite(query_var) or query_var <= 0:
        raise RuntimeError("invalid query variance")
    results: dict[str, Any] = {}
    for support_k in args.supports:
        support_y = np.asarray(cell.y[cell.supports[support_k]], dtype=np.float64)
        results[str(support_k)] = {}
        for arm in ARMS:
            raw_source, raw_support, raw_query = semantic.arm_frames(
                parent, cell, family, realization, support_k, arm
            )
            source_x, support_x, query_x = prepare_frames(
                semantic, raw_source, raw_support, raw_query
            )
            started = time.perf_counter()
            prediction, label_audit = fit_predict(
                transtab, source_x, source_y, support_x, support_y, query_x,
                realization, args
            )
            fit_seconds = time.perf_counter() - started
            mse = float(np.mean((query_y - prediction) ** 2))
            results[str(support_k)][arm] = {
                "mse": mse,
                "nmse": mse / query_var,
                "nrmse": float(np.sqrt(mse / query_var)),
                "fit_predict_seconds": round(fit_seconds, 3),
                "audit": {
                    **label_audit,
                    "source_columns": list(source_x.columns),
                    "target_columns": list(support_x.columns),
                    "source_frame_sha256": stable_frame_hash(source_x, source_y),
                    "support_frame_sha256": stable_frame_hash(support_x, support_y),
                    "query_frame_sha256": stable_frame_hash(query_x),
                },
            }
            print(json.dumps({
                "family": family,
                "realization": realization,
                "support": support_k,
                "arm": arm,
                "nmse": results[str(support_k)][arm]["nmse"],
                "fit_seconds": round(fit_seconds, 1),
            }), flush=True)
    return {
        "family": family,
        "realization": realization,
        "supports": list(args.supports),
        "arms": list(ARMS),
        "n_source": len(cell.source_rows),
        "n_query": len(cell.query_rows),
        "query_variance": query_var,
        "cell_audit": cell.audit,
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--transtab-source", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--families", nargs="+", choices=FAMILIES, default=list(FAMILIES))
    parser.add_argument("--realizations", nargs="+", type=int, default=list(range(N_REALIZATIONS)))
    parser.add_argument("--supports", nargs="+", type=int, default=list(SUPPORTS))
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--num-epoch", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--eval-batch-size", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.input = args.input.resolve()
    args.transtab_source = args.transtab_source.resolve()
    args.out_root = args.out_root.resolve()
    if any(value < 0 or value >= N_REALIZATIONS for value in args.realizations):
        raise ValueError("realizations must be in [0, 19]")
    if any(value not in SUPPORTS for value in args.supports):
        raise ValueError(f"supports must be drawn from {SUPPORTS}")
    for path in (args.input, PROTOCOL, SEMANTIC_RUNNER):
        if not path.is_file():
            raise FileNotFoundError(path)
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    semantic = load_semantic_runner()
    parent = semantic.load_parent()
    transtab = import_transtab(args.transtab_source)
    import torch

    if not torch.cuda.is_available() or not args.device.startswith("cuda"):
        raise RuntimeError("TransTab extension requires a visible CUDA device")
    source_tree_hash = transtab_tree_hash(args.transtab_source)
    provenance = {
        "input_sha256": sha256_file(args.input),
        "parent_runner_sha256": sha256_file(semantic.PARENT_RUNNER),
        "semantic_runner_sha256": sha256_file(SEMANTIC_RUNNER),
        "protocol_sha256": sha256_file(PROTOCOL),
        "runner_sha256": sha256_file(Path(__file__)),
        "transtab_commit": EXPECTED_TRANSTAB_COMMIT,
        "transtab_tree_sha256": source_tree_hash,
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "torch": torch.__version__,
            "transformers": importlib.metadata.version("transformers"),
            "transtab_setup": "0.0.7",
        },
        "compatibility_corrections": [
            "TrainDataset index:index+1 instead of upstream index-1:index",
            "raw TransTabRegressor outputs instead of classifier sigmoid in predict()",
        ],
        "learner": {
            "class": "transtab.TransTabRegressor",
            "initialization": "scratch",
            "hidden_dim": 128,
            "num_layer": 2,
            "num_attention_head": 8,
            "ffn_dim": 256,
            "activation": "relu",
            "hidden_dropout_prob": 0,
            "num_epoch": args.num_epoch,
            "batch_size": args.batch_size,
            "eval_batch_size": args.eval_batch_size,
            "learning_rate": args.learning_rate,
            "weight_decay": 0.0,
            "device": args.device,
        },
    }
    print(json.dumps({"status": "provenance", **provenance}), flush=True)
    panel = parent.load_panel(args.input)
    for family in args.families:
        for realization in args.realizations:
            out_dir = args.out_root / family / f"r{realization:02d}"
            metrics_path = out_dir / "metrics.json"
            if metrics_path.is_file():
                existing = json.loads(metrics_path.read_text(encoding="utf-8"))
                identity = (
                    "input_sha256", "parent_runner_sha256", "semantic_runner_sha256",
                    "protocol_sha256", "runner_sha256", "transtab_tree_sha256",
                )
                if (
                    any(existing.get(key) != provenance[key] for key in identity)
                    or existing.get("family") != family
                    or existing.get("realization") != realization
                    or existing.get("supports") != list(args.supports)
                    or existing.get("learner") != provenance["learner"]
                ):
                    raise RuntimeError(f"cached cell conflicts with provenance: {metrics_path}")
                print(json.dumps({"family": family, "realization": realization,
                                  "status": "cached"}), flush=True)
                continue
            started = time.perf_counter()
            payload = run_realization(
                semantic, parent, panel, transtab, family, realization, args
            )
            payload.update(provenance)
            payload["wall_seconds"] = round(time.perf_counter() - started, 3)
            payload["status"] = "complete"
            out_dir.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(
                json.dumps(parent.json_ready(payload), indent=1, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(json.dumps({"family": family, "realization": realization,
                              "status": "complete",
                              "wall_seconds": payload["wall_seconds"]}), flush=True)
    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
