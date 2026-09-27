#!/usr/bin/env python3
"""Review-triggered CARTE extension on the frozen MCR realizations.

Seven arms expose correct, matched-wrong, and reference M/C/R content to the
official CARTE multitable regressor.  The parent MCR runner supplies every
realization, row draw, rendering, lesion, outcome, and split.  This runner only
changes the learner-facing table representation.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import sys
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PARENT_RUNNER = ROOT / "scripts/run_crta_v3_mcr_factorial_semisynth_v1.py"
PROTOCOL = ROOT / "iclr_latex_v3/MCR_CARTE_REVIEW_EXTENSION_V1.md"
DEFAULT_INPUT = Path("._data/nhanes_common_panel_tokens_v2.parquet")
DEFAULT_OUT = ROOT / "experiments/crta_v3_mcr_carte_v1"

EXPECTED_PARENT_SHA256 = "c753e142f3af884a9f9b0d635e67465e8d8e0e20cefbb13f09006be56753e4a0"
FAMILIES = ("additive", "pairwise", "sparse")
SUPPORTS = (32, 512)
N_REALIZATIONS = 20
ARMS = (
    "correct",
    "m_wrong",
    "m_raw",
    "c_wrong",
    "c_reference",
    "r_wrong",
    "r_free",
)

SEMANTIC_NAMES = (
    "standardized age",
    "standardized total cholesterol",
    "standardized glycated hemoglobin HbA1c",
    "standardized serum creatinine",
    "standardized blood hemoglobin",
    "standardized red blood cell count",
    "standardized white blood cell count",
    "standardized waist circumference",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def stable_frame_hash(frame: pd.DataFrame, y: np.ndarray | None = None) -> str:
    digest = hashlib.sha256()
    digest.update("\x1f".join(map(str, frame.columns)).encode("utf-8"))
    digest.update(pd.util.hash_pandas_object(frame, index=False).to_numpy().tobytes())
    if y is not None:
        digest.update(np.asarray(y, dtype=np.float64).tobytes())
    return digest.hexdigest()


def load_parent():
    observed = sha256_file(PARENT_RUNNER)
    if observed != EXPECTED_PARENT_SHA256:
        raise RuntimeError(
            f"parent MCR runner hash mismatch: {observed}; expected "
            f"{EXPECTED_PARENT_SHA256}"
        )
    spec = importlib.util.spec_from_file_location("mcr_carte_parent", PARENT_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {PARENT_RUNNER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class DomainState:
    columns: tuple[str, ...]
    medians: np.ndarray
    missing_columns: tuple[str, ...]


def fit_domain_state(frame: pd.DataFrame) -> DomainState:
    numeric = frame.apply(pd.to_numeric, errors="coerce")
    active = tuple(
        column
        for column in numeric.columns
        if numeric[column].notna().sum() >= 2
        and numeric[column].dropna().nunique() >= 2
    )
    if not active:
        raise RuntimeError("no active numeric feature")
    values = numeric.loc[:, active].to_numpy(np.float64)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        medians = np.nanmedian(values, axis=0)
    medians = np.where(np.isfinite(medians), medians, 0.0)
    missing = tuple(
        column
        for column in active
        if 0 < int(numeric[column].isna().sum()) < len(numeric)
    )
    return DomainState(active, medians, missing)


def apply_domain_state(frame: pd.DataFrame, state: DomainState) -> pd.DataFrame:
    values = frame.loc[:, state.columns].apply(
        pd.to_numeric, errors="coerce"
    ).to_numpy(np.float64)
    missing = ~np.isfinite(values)
    output = pd.DataFrame(
        np.where(missing, state.medians, values).astype(np.float32),
        columns=list(state.columns),
    )
    lookup = {column: index for index, column in enumerate(state.columns)}
    for column in state.missing_columns:
        output[f"missing indicator for {column}"] = missing[
            :, lookup[column]
        ].astype(np.float32)
    return output


def native_names(parent: Any, cell: Any, family: str, realization: int
                 ) -> tuple[tuple[str, ...], tuple[str, ...], Any]:
    ordinal = tuple(int(v) for v in cell.audit["ordinal_features"])
    source = parent.draw_side_rendering(
        ordinal, ("primary", family, realization, "source"), False
    )
    target = parent.draw_side_rendering(
        ordinal, ("primary", family, realization, "target"), False
    )
    return source.names, target.names, source


def neutralized_raw_source(cell: Any, source_rendering: Any) -> np.ndarray:
    result = np.asarray(cell.source_rendered, dtype=np.float64).copy()
    for index, sentinel in source_rendering.sentinel.items():
        result[result[:, index] == sentinel, index] = np.nan
    return result


def relation_label(
    base_names: tuple[str, ...], relation: tuple[Any, ...], index: int
) -> str:
    direction = "increases" if int(relation[-1]) > 0 else "decreases"
    if len(relation) == 2:
        feature, _ = relation
        return (
            f"higher {base_names[int(feature)]} "
            f"{direction} the prediction target"
        )
    left, right, operation, _ = relation
    op_text = "minus" if operation == "diff" else "log ratio to"
    return (
        f"{base_names[int(left)]} {op_text} "
        f"{base_names[int(right)]} {direction} the prediction target"
    )


def append_relations(
    parent: Any,
    frame: np.ndarray,
    base_names: tuple[str, ...],
    relations: Any | None,
) -> pd.DataFrame:
    columns: dict[str, np.ndarray] = {
        name: np.asarray(frame[:, index], dtype=np.float64)
        for index, name in enumerate(base_names)
    }
    if relations is not None:
        relation_index = 0
        for feature, sign in relations.feat_signs:
            relation = (int(feature), int(sign))
            columns[relation_label(base_names, relation, relation_index)] = np.asarray(
                frame[:, int(feature)], dtype=np.float64
            )
            relation_index += 1
        for left, right, operation, sign in relations.pair_terms:
            relation = (int(left), int(right), str(operation), int(sign))
            columns[relation_label(base_names, relation, relation_index)] = (
                parent.op_values(
                    str(operation), frame[:, int(left)], frame[:, int(right)]
                )
            )
            relation_index += 1
    return pd.DataFrame(columns)


def arm_frames(
    parent: Any,
    cell: Any,
    family: str,
    realization: int,
    support_k: int,
    arm: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    source_native, target_native, source_rendering = native_names(
        parent, cell, family, realization
    )
    source = parent.decode(cell.source_rendered, cell.source_tables["true"])
    target_support = np.asarray(cell.target_decoded_support[support_k], dtype=np.float64)
    target_query = np.asarray(cell.target_decoded_query, dtype=np.float64)
    source_names = tuple(SEMANTIC_NAMES)
    target_names = tuple(SEMANTIC_NAMES)
    relation_level = "true"

    if arm == "m_wrong":
        source = parent.decode(cell.source_rendered, cell.source_tables["wrong"])
    elif arm == "m_raw":
        source = neutralized_raw_source(cell, source_rendering)
    elif arm == "c_wrong":
        source = source[:, cell.c_perms["deranged"]]
    elif arm == "c_reference":
        source_names = tuple(source_native)
        target_names = tuple(target_native)
    elif arm == "r_wrong":
        relation_level = "random"
    elif arm == "r_free":
        relation_level = "free"
    elif arm != "correct":
        raise ValueError(f"unknown arm: {arm}")

    relations = cell.relations[relation_level]
    source_frame = append_relations(parent, source, source_names, relations)
    support_frame = append_relations(
        parent, target_support, target_names, relations
    )
    query_frame = append_relations(parent, target_query, target_names, relations)
    return source_frame, support_frame, query_frame


def transformer(fasttext_model: Any):
    from carte_ai import Table2GraphTransformer

    result = Table2GraphTransformer(fasttext_model_path=None, n_jobs=1)
    result.lm_model_ = fasttext_model
    return result


def set_domain(graphs: list[Any], domain: int) -> list[Any]:
    for graph in graphs:
        graph.domain = int(domain)
    return graphs


def patched_multitable_estimator():
    import torch
    from carte_ai import CARTEMultitableRegressor

    class PatchedMultitable(CARTEMultitableRegressor):
        def _run_epoch(self, model, optimizer, train_loader):
            scaler = torch.amp.GradScaler(
                "cuda", enabled=self.device_.type == "cuda"
            )
            model.train()
            for data in train_loader:
                self._run_step(model, data, optimizer, scaler)

        def _run_epoch_multitable(
            self, ds_source, ds_target, model, optimizer, idx_iterator
        ):
            scaler = torch.amp.GradScaler(
                "cuda", enabled=self.device_.type == "cuda"
            )
            model.train()
            idx_iterator.train_flag = True
            while idx_iterator.train_flag:
                idx_target, idx_source = idx_iterator.sample()
                batch = [ds_source[int(index)] for index in idx_source]
                batch += [ds_target[int(index)] for index in idx_target]
                data = self._set_data_eval(data=batch)
                self._run_step(model, data, optimizer, scaler)

    return PatchedMultitable


def fit_predict(
    source_graphs: list[Any],
    support_graphs: list[Any],
    support_y: np.ndarray,
    query_graphs: list[Any],
    seed: int,
    args: argparse.Namespace,
) -> np.ndarray:
    estimator_class = patched_multitable_estimator()
    estimator = estimator_class(
        source_data={"mcr_source": source_graphs},
        target_fraction=args.target_fraction,
        load_pretrain=True,
        freeze_pretrain=True,
        learning_rate=args.learning_rate,
        batch_size=args.batch_size,
        max_epoch=args.max_epoch,
        val_size=0.2,
        early_stopping_patience=args.early_stopping_patience,
        num_model=1,
        random_state=seed,
        n_jobs=1,
        device=args.device,
        disable_pbar=True,
        pretrained_model_path=str(args.pretrained_model),
    )
    estimator.fit(copy.copy(support_graphs), support_y)
    return np.asarray(
        estimator.predict(copy.copy(query_graphs)), dtype=np.float64
    ).reshape(-1)


def source_graph_bundle(
    source_frame: pd.DataFrame,
    source_y: np.ndarray,
    fasttext_model: Any,
) -> tuple[list[Any], dict[str, Any]]:
    source_state = fit_domain_state(source_frame)
    source_ready = apply_domain_state(source_frame, source_state)
    source_transformer = transformer(fasttext_model)
    source_graphs = set_domain(
        source_transformer.fit_transform(source_ready, y=source_y), 1
    )
    return source_graphs, {
        "source_rows": len(source_ready),
        "source_columns": list(source_ready.columns),
        "source_frame_sha256": stable_frame_hash(source_ready, source_y),
    }


def target_graph_bundle(
    support_frame: pd.DataFrame,
    support_y: np.ndarray,
    query_frame: pd.DataFrame,
    fasttext_model: Any,
) -> tuple[list[Any], list[Any], dict[str, Any]]:
    target_state = fit_domain_state(support_frame)
    support_ready = apply_domain_state(support_frame, target_state)
    query_ready = apply_domain_state(query_frame, target_state)
    target_transformer = transformer(fasttext_model)
    support_graphs = set_domain(
        target_transformer.fit_transform(support_ready, y=support_y), 0
    )
    query_graphs = set_domain(target_transformer.transform(query_ready), 0)
    return support_graphs, query_graphs, {
        "support_rows": len(support_ready),
        "query_rows": len(query_ready),
        "target_columns": list(support_ready.columns),
        "support_frame_sha256": stable_frame_hash(support_ready, support_y),
        "query_frame_sha256": stable_frame_hash(query_ready),
    }


def run_realization(
    parent: Any,
    panel: Any,
    fasttext_model: Any,
    family: str,
    realization: int,
    args: argparse.Namespace,
) -> dict[str, Any]:
    cell = parent.build_cell(
        panel, "primary", family, realization, tuple(args.supports)
    )
    y_query = np.asarray(cell.y[cell.query_rows], dtype=np.float64)
    source_y = np.asarray(cell.y[cell.source_rows], dtype=np.float64)
    query_var = float(np.var(y_query, ddof=0))
    if not np.isfinite(query_var) or query_var <= 0:
        raise RuntimeError("invalid query variance")

    results: dict[str, Any] = {}
    for support_k in args.supports:
        support_y = np.asarray(cell.y[cell.supports[support_k]], dtype=np.float64)
        results[str(support_k)] = {}
        source_cache: dict[str, tuple[list[Any], dict[str, Any]]] = {}
        target_cache: dict[
            tuple[str, str], tuple[list[Any], list[Any], dict[str, Any]]
        ] = {}
        for arm in ARMS:
            source_frame, support_frame, query_frame = arm_frames(
                parent, cell, family, realization, support_k, arm
            )
            source_key = stable_frame_hash(source_frame, source_y)
            target_key = (
                stable_frame_hash(support_frame, support_y),
                stable_frame_hash(query_frame),
            )
            graph_started = time.perf_counter()
            if source_key not in source_cache:
                source_cache[source_key] = source_graph_bundle(
                    source_frame, source_y, fasttext_model
                )
            if target_key not in target_cache:
                target_cache[target_key] = target_graph_bundle(
                    support_frame,
                    support_y,
                    query_frame,
                    fasttext_model,
                )
            source_graphs, source_audit = source_cache[source_key]
            support_graphs, query_graphs, target_audit = target_cache[target_key]
            audit = {**source_audit, **target_audit}
            graph_seconds = time.perf_counter() - graph_started
            fit_started = time.perf_counter()
            prediction = fit_predict(
                source_graphs,
                support_graphs,
                support_y,
                query_graphs,
                realization,
                args,
            )
            fit_seconds = time.perf_counter() - fit_started
            mse = float(np.mean((y_query - prediction) ** 2))
            results[str(support_k)][arm] = {
                "mse": mse,
                "nmse": mse / query_var,
                "nrmse": float(np.sqrt(mse / query_var)),
                "graph_seconds": round(graph_seconds, 3),
                "fit_predict_seconds": round(fit_seconds, 3),
                "audit": audit,
            }
            print(
                json.dumps(
                    {
                        "family": family,
                        "realization": realization,
                        "support": support_k,
                        "arm": arm,
                        "nmse": results[str(support_k)][arm]["nmse"],
                        "fit_seconds": round(fit_seconds, 1),
                    }
                ),
                flush=True,
            )
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
    parser.add_argument("--fasttext-model", type=Path, required=True)
    parser.add_argument("--pretrained-model", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--families", nargs="+", choices=FAMILIES, default=list(FAMILIES))
    parser.add_argument(
        "--realizations", nargs="+", type=int, default=list(range(N_REALIZATIONS))
    )
    parser.add_argument("--supports", nargs="+", type=int, default=list(SUPPORTS))
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--max-epoch", type=int, default=200)
    parser.add_argument("--early-stopping-patience", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--target-fraction", type=float, default=0.125)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    warnings.filterwarnings(
        "ignore", category=FutureWarning, module=r"carte_ai(?:\..*)?"
    )
    if any(r < 0 or r >= N_REALIZATIONS for r in args.realizations):
        raise ValueError("realizations must be in [0, 19]")
    if any(k not in SUPPORTS for k in args.supports):
        raise ValueError(f"supports must be drawn from {SUPPORTS}")
    for path in (args.input, args.fasttext_model, args.pretrained_model, PROTOCOL):
        if not path.is_file():
            raise FileNotFoundError(path)
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    parent = load_parent()

    import fasttext
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CARTE extension requires a visible CUDA device")
    provenance = {
        "input_sha256": sha256_file(args.input),
        "parent_runner_sha256": sha256_file(PARENT_RUNNER),
        "protocol_sha256": sha256_file(PROTOCOL),
        "runner_sha256": sha256_file(Path(__file__)),
        "pretrained_model_sha256": sha256_file(args.pretrained_model),
        "fasttext_model_sha256": sha256_file(args.fasttext_model),
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "torch": torch.__version__,
            "carte_ai": importlib.metadata.version("carte-ai"),
        },
        "learner": {
            "class": "carte_ai.CARTEMultitableRegressor",
            "num_model": 1,
            "load_pretrain": True,
            "freeze_pretrain": True,
            "max_epoch": args.max_epoch,
            "early_stopping_patience": args.early_stopping_patience,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "target_fraction": args.target_fraction,
            "device": args.device,
        },
    }
    print(json.dumps({"status": "loading_fasttext", **provenance}), flush=True)
    fasttext_model = fasttext.load_model(str(args.fasttext_model))
    panel = parent.load_panel(args.input)
    print(
        json.dumps(
            {
                "status": "ready",
                "source_rows_available": len(panel.source_index),
                "target_rows_available": len(panel.target_index),
            }
        ),
        flush=True,
    )

    for family in args.families:
        for realization in args.realizations:
            out_dir = args.out_root / family / f"r{realization:02d}"
            metrics_path = out_dir / "metrics.json"
            if metrics_path.is_file():
                existing = json.loads(metrics_path.read_text(encoding="utf-8"))
                keys = (
                    "input_sha256",
                    "parent_runner_sha256",
                    "protocol_sha256",
                    "runner_sha256",
                    "pretrained_model_sha256",
                    "fasttext_model_sha256",
                )
                if (
                    any(existing.get(key) != provenance[key] for key in keys)
                    or existing.get("family") != family
                    or existing.get("realization") != realization
                    or existing.get("supports") != list(args.supports)
                ):
                    raise RuntimeError(
                        f"cached cell conflicts with current provenance: {metrics_path}"
                    )
                print(
                    json.dumps(
                        {"family": family, "realization": realization, "status": "cached"}
                    ),
                    flush=True,
                )
                continue
            started = time.perf_counter()
            payload = run_realization(
                parent, panel, fasttext_model, family, realization, args
            )
            payload.update(provenance)
            payload["wall_seconds"] = round(time.perf_counter() - started, 3)
            payload["status"] = "complete"
            out_dir.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(
                json.dumps(parent.json_ready(payload), indent=1, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(
                json.dumps(
                    {
                        "family": family,
                        "realization": realization,
                        "status": "complete",
                        "wall_seconds": payload["wall_seconds"],
                    }
                ),
                flush=True,
            )
    print(json.dumps({"status": "complete"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
