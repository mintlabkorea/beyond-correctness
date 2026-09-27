from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[4]
TASK_ROOT = ROOT / "tasks" / "standard_benchmark" / "current"
CONFIG_DIR = TASK_ROOT / "configs"
DEFAULT_DATASET_MANIFEST = (
    ROOT / "tasks" / "cross_cohort_noncorepred" / "current" / "manifests" / "manifest.yaml"
)
QUESTIONNAIRE_BUNDLE_RULES_CSV = (
    TASK_ROOT
    / "relation_sources"
    / "common"
    / "artifacts"
    / "questionnaire_seed_bundle_v1"
    / "executable_item_rules.csv"
)


@dataclass
class BenchmarkSpec:
    benchmark_id: str
    setting: str
    train_dataset: str
    test_dataset: str
    feature_set: str
    target_set: str
    fewshot_fracs: List[float]
    adaptation_policy: str
    mask_target_cohort_only: bool
    observed_slots: List[str]


def load_yaml(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_configs() -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    feature_cfg = load_yaml(CONFIG_DIR / "feature_sets.yaml")
    target_cfg = load_yaml(CONFIG_DIR / "target_sets.yaml")
    registry_cfg = load_yaml(CONFIG_DIR / "benchmark_registry.yaml")
    return feature_cfg, target_cfg, registry_cfg


def get_manifest_mapping_value(mapping: Dict[str, Any], dataset_name: str) -> Optional[str]:
    if not isinstance(mapping, dict):
        return None

    source_map = mapping.get("source")
    if isinstance(source_map, dict) and dataset_name in source_map:
        value = source_map[dataset_name]
    else:
        value = mapping.get(dataset_name)

    if value is None:
        return None

    value = str(value).strip()
    return value or None


def get_manifest_mapping_values(mapping: Dict[str, Any], dataset_name: str) -> List[str]:
    if not isinstance(mapping, dict):
        return []

    source_map = mapping.get("source")
    value: Any = None
    if isinstance(source_map, dict) and dataset_name in source_map:
        value = source_map[dataset_name]
    else:
        value = mapping.get(dataset_name)

    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    value_str = str(value).strip()
    return [value_str] if value_str else []


def get_benchmark_spec(registry_cfg: Dict[str, Any], benchmark_id: str) -> BenchmarkSpec:
    matches = [b for b in registry_cfg["benchmarks"] if b["benchmark_id"] == benchmark_id]
    if not matches:
        raise ValueError(f"Unknown benchmark_id: {benchmark_id}")
    b = matches[0]
    return BenchmarkSpec(
        benchmark_id=b["benchmark_id"],
        setting=b["setting"],
        train_dataset=b["train_dataset"],
        test_dataset=b["test_dataset"],
        feature_set=b["feature_set"],
        target_set=b["target_set"],
        fewshot_fracs=b["fewshot_fracs"],
        adaptation_policy=b.get("adaptation_policy", "none"),
        mask_target_cohort_only=b.get("mask_target_cohort_only", False),
        observed_slots=b.get("observed_slots", []),
    )


def get_feature_set(feature_cfg: Dict[str, Any], feature_set_name: str) -> Dict[str, Any]:
    feature_sets = feature_cfg["feature_sets"]
    if feature_set_name not in feature_sets:
        raise ValueError(f"Unknown feature_set: {feature_set_name}")
    return feature_sets[feature_set_name]


def get_target_set(target_cfg: Dict[str, Any], target_set_name: str) -> List[str]:
    target_sets = target_cfg["target_sets"]
    if target_set_name not in target_sets:
        raise ValueError(f"Unknown target_set: {target_set_name}")
    return list(target_sets[target_set_name]["targets"])


def infer_subject_id_column(df: pd.DataFrame, candidates: List[str]) -> str:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    raise KeyError(f"Could not infer subject_id column. candidates={candidates}")


def slot_column_name(slot_name: str) -> str:
    return f"slot__{slot_name}"


def target_column_name(target_name: str) -> str:
    return f"target__{target_name}"


def load_questionnaire_rule_index(path: Path = QUESTIONNAIRE_BUNDLE_RULES_CSV) -> Dict[Tuple[str, str], Dict[str, str]]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return {
        (str(row["cohort_name"]).strip().lower(), str(row["raw_item_name"]).strip()): row
        for row in rows
    }


def recode_questionnaire_series(series: pd.Series, rule_id: str) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    out = pd.Series(np.nan, index=series.index, dtype="float64")

    if rule_id == "identity_binary_1_male_2_female":
        out = values.astype("float64")
    elif rule_id == "map_nhanes_education_5level_v1":
        out = values.where(values.isin([1, 2, 3, 4, 5]), np.nan).astype("float64")
    elif rule_id == "map_knhanes_education_to_nhanes_5level_v1":
        mapping = {1: 1.0, 2: 1.0, 3: 2.0, 4: 3.0, 5: 4.0, 6: 5.0, 7: 5.0, 8: 5.0}
        out = values.map(mapping).astype("float64")
    elif rule_id == "map_nhanes_diq010_binary_v1":
        mapping = {1: 1.0, 2: 0.0}
        out = values.map(mapping).astype("float64")
    elif rule_id == "map_knhanes_de1_binary_v1":
        mapping = {1: 1.0, 0: 0.0}
        out = values.map(mapping).astype("float64")
    elif rule_id == "map_nhanes_bpq020_binary_v1":
        mapping = {1: 1.0, 2: 0.0}
        out = values.map(mapping).astype("float64")
    elif rule_id == "map_knhanes_di1_binary_v1":
        mapping = {1: 1.0, 0: 0.0}
        out = values.map(mapping).astype("float64")
    elif rule_id == "map_nhanes_smq020_binary_v1":
        mapping = {1: 1.0, 2: 0.0}
        out = values.map(mapping).astype("float64")
    elif rule_id == "map_knhanes_bs1_1_to_100cig_threshold_v1":
        mapping = {2: 1.0, 1: 0.0, 3: 0.0}
        out = values.map(mapping).astype("float64")
    elif rule_id == "map_nhanes_smq040_to_binary_current_smoker_v1":
        mapping = {1: 1.0, 2: 1.0, 3: 0.0}
        out = values.map(mapping).astype("float64")
    elif rule_id == "map_knhanes_bs3_1_to_binary_current_smoker_v1":
        mapping = {1: 1.0, 2: 1.0, 3: 0.0, 4: 0.0}
        out = values.map(mapping).astype("float64")
    else:
        return series

    return out


def recode_series_from_inline_harmonization(
    series: pd.Series,
    slot_mapping: Dict[str, Any],
    dataset_name: str,
) -> pd.Series:
    harmonization_map = slot_mapping.get("harmonization")
    if not isinstance(harmonization_map, dict):
        return series

    dataset_rule = harmonization_map.get(dataset_name)
    if not isinstance(dataset_rule, dict):
        return series

    rule_type = str(dataset_rule.get("type", "")).strip()
    if not rule_type:
        return series

    values = pd.to_numeric(series, errors="coerce")
    out = pd.Series(np.nan, index=series.index, dtype="float64")

    if rule_type == "binary_map":
        positive = {float(v) for v in dataset_rule.get("positive_values", [])}
        negative = {float(v) for v in dataset_rule.get("negative_values", [])}
        out.loc[values.isin(list(positive))] = 1.0
        out.loc[values.isin(list(negative))] = 0.0
        return out

    if rule_type == "ordinal_keep":
        valid = {float(v) for v in dataset_rule.get("valid_values", [])}
        out.loc[values.isin(list(valid))] = values.loc[values.isin(list(valid))]
        return out

    return series


def aggregate_slot_series(
    series_list: List[pd.Series],
    slot_mapping: Dict[str, Any],
    dataset_name: str,
) -> pd.Series:
    if not series_list:
        raise ValueError("aggregate_slot_series received an empty series list.")

    aggregation_map = slot_mapping.get("aggregation")
    if isinstance(aggregation_map, dict):
        aggregation = str(aggregation_map.get(dataset_name, "")).strip()
    else:
        aggregation = str(aggregation_map or "").strip()

    if not aggregation:
        return series_list[0]

    if aggregation == "first_non_null":
        out = series_list[0].copy()
        for series in series_list[1:]:
            out = out.combine_first(series)
        return out

    if aggregation == "any_positive_binary":
        frame = pd.concat(series_list, axis=1)
        has_positive = frame.eq(1.0).any(axis=1)
        all_negative = frame.notna().all(axis=1) & frame.eq(0.0).all(axis=1)
        any_observed = frame.notna().any(axis=1)
        out = pd.Series(np.nan, index=frame.index, dtype="float64")
        out.loc[has_positive] = 1.0
        out.loc[all_negative & any_observed] = 0.0
        return out

    raise ValueError(f"Unsupported slot aggregation '{aggregation}' for dataset={dataset_name}")


def build_slot_series(
    df: pd.DataFrame,
    dataset_name: str,
    slot_name: str,
    slot_mapping: Dict[str, Any],
    questionnaire_rule_index: Dict[Tuple[str, str], Dict[str, str]],
    parquet_path: str,
) -> pd.Series:
    source_cols = get_manifest_mapping_values(slot_mapping, dataset_name)
    if not source_cols:
        raise ValueError(f"No source columns defined for slot={slot_name} dataset={dataset_name}")

    series_list: List[pd.Series] = []
    for source_col in source_cols:
        if source_col not in df.columns:
            raise KeyError(
                f"Manifest slots.{slot_name} for dataset={dataset_name} "
                f"points to missing column '{source_col}' in {parquet_path}"
            )
        series = df[source_col]
        questionnaire_rule = questionnaire_rule_index.get((dataset_name.lower(), source_col))
        if questionnaire_rule is not None:
            series = recode_questionnaire_series(series, str(questionnaire_rule["harmonized_value_rule"]))
        else:
            series = recode_series_from_inline_harmonization(series, slot_mapping, dataset_name)
        series_list.append(series)

    return aggregate_slot_series(series_list, slot_mapping, dataset_name)


def build_canonical_dataset_table(dataset_name: str, manifest: Dict[str, Any]) -> pd.DataFrame:
    ds_cfg = manifest["datasets"].get(dataset_name)
    if ds_cfg is None:
        raise ValueError(f"Dataset {dataset_name} is not defined in {DEFAULT_DATASET_MANIFEST}")

    parquet_path = ds_cfg["parquet"]
    df = pd.read_parquet(parquet_path).copy()
    defaults = manifest.get("defaults", {})

    subject_id_col = infer_subject_id_column(
        df,
        list(defaults.get("subject_id_candidates", ["SEQN", "subject_id"])),
    )
    split_col = str(defaults.get("split_col", "split"))
    if split_col not in df.columns:
        raise KeyError(f"split column '{split_col}' not found in {parquet_path}")

    canonical_cols: Dict[str, Any] = {
        "subject_id": df[subject_id_col].astype(str),
        "split": df[split_col].astype(str),
        "cohort": pd.Series(dataset_name, index=df.index, dtype="object"),
    }
    questionnaire_rule_index = load_questionnaire_rule_index()

    for slot_name, mapping in manifest.get("slots", {}).items():
        source_cols = get_manifest_mapping_values(mapping, dataset_name)
        if not source_cols:
            continue
        canonical_cols[slot_column_name(slot_name)] = build_slot_series(
            df=df,
            dataset_name=dataset_name,
            slot_name=slot_name,
            slot_mapping=mapping,
            questionnaire_rule_index=questionnaire_rule_index,
            parquet_path=parquet_path,
        )

    for target_name, mapping in manifest.get("targets", {}).items():
        source_col = get_manifest_mapping_value(mapping, dataset_name)
        if source_col is None:
            continue
        if source_col not in df.columns:
            raise KeyError(
                f"Manifest targets.{target_name} for dataset={dataset_name} "
                f"points to missing column '{source_col}' in {parquet_path}"
            )
        canonical_cols[target_column_name(target_name)] = df[source_col]

    overlap_cols = [c for c in canonical_cols if c in df.columns]
    if overlap_cols:
        df = df.drop(columns=overlap_cols)

    return pd.concat([df, pd.DataFrame(canonical_cols, index=df.index)], axis=1)


def load_dataset_table(dataset_name: str, manifest: Dict[str, Any]) -> pd.DataFrame:
    return build_canonical_dataset_table(dataset_name, manifest)


def apply_full_numeric_feature_rule(df: pd.DataFrame, feature_rule: Dict[str, Any]) -> List[str]:
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    exclude_columns = set(feature_rule.get("exclude_columns", []))
    exclude_prefixes = feature_rule.get("exclude_prefixes", [])

    keep = []
    for c in numeric_cols:
        if c in exclude_columns:
            continue
        if any(c.startswith(prefix) for prefix in exclude_prefixes):
            continue
        keep.append(c)
    return keep


def apply_explicit_slot_rule(df: pd.DataFrame, feature_rule: Dict[str, Any]) -> List[str]:
    slots = feature_rule["slots"]
    feature_cols = [slot_column_name(slot_name) for slot_name in slots]
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing explicit slot columns: {missing}")
    return feature_cols


def resolve_feature_columns(df: pd.DataFrame, feature_rule: Dict[str, Any]) -> List[str]:
    mode = feature_rule["feature_mode"]
    if mode == "explicit_slots":
        return apply_explicit_slot_rule(df, feature_rule)
    if mode == "cohort_full_numeric":
        return apply_full_numeric_feature_rule(df, feature_rule)
    raise ValueError(f"Unsupported feature_mode: {mode}")


def drop_target_from_features(feature_cols: List[str], target_name: str) -> List[str]:
    target_col = target_column_name(target_name)
    return [c for c in feature_cols if c != target_col]


def drop_columns(feature_cols: List[str], columns_to_remove: List[str]) -> List[str]:
    remove_set = set(columns_to_remove)
    return [c for c in feature_cols if c not in remove_set]


def get_target_leakage_columns(
    manifest: Dict[str, Any],
    dataset_name: str,
    target_name: str,
) -> List[str]:
    leakage_cols = [target_column_name(target_name)]
    target_mapping = manifest.get("targets", {}).get(target_name, {})
    source_col = get_manifest_mapping_value(target_mapping, dataset_name)
    if source_col is not None:
        leakage_cols.append(source_col)
        for slot_name, slot_mapping in manifest.get("slots", {}).items():
            slot_source_cols = get_manifest_mapping_values(slot_mapping, dataset_name)
            if source_col in slot_source_cols:
                leakage_cols.append(slot_column_name(slot_name))
    return leakage_cols


def split_by_standard_policy(
    df: pd.DataFrame,
    train_splits: List[str],
    eval_splits: List[str],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if "split" not in df.columns:
        raise ValueError("Expected split column in dataset table.")
    train_df = df[df["split"].isin(train_splits)].copy()
    eval_df = df[df["split"].isin(eval_splits)].copy()
    return train_df, eval_df


def remove_eval_subjects_from_target_train(
    target_train_df: pd.DataFrame,
    target_eval_df: pd.DataFrame,
) -> pd.DataFrame:
    if "subject_id" not in target_train_df.columns or "subject_id" not in target_eval_df.columns:
        return target_train_df
    eval_subjects = set(target_eval_df["subject_id"].dropna().unique().tolist())
    return target_train_df[~target_train_df["subject_id"].isin(eval_subjects)].copy()


def sample_fewshot(
    df: pd.DataFrame,
    frac: float,
    seed: int,
) -> pd.DataFrame:
    if frac <= 0.0:
        return df.iloc[0:0].copy()
    if "subject_id" in df.columns:
        subject_ids = pd.Series(df["subject_id"].dropna().unique())
        n = max(1, int(round(len(subject_ids) * frac)))
        sampled_subjects = subject_ids.sample(n=n, random_state=seed, replace=False)
        return df[df["subject_id"].isin(sampled_subjects)].copy()
    n = max(1, int(round(len(df) * frac)))
    return df.sample(n=n, random_state=seed, replace=False).copy()


def maybe_mask_to_observed_slots(
    df: pd.DataFrame,
    feature_cols: List[str],
    observed_slots: List[str],
) -> pd.DataFrame:
    if not observed_slots:
        return df
    masked = df.copy()
    keep = {slot_column_name(slot_name) for slot_name in observed_slots}
    for c in feature_cols:
        if c not in keep:
            masked[c] = np.nan
    return masked


def build_single_target_table(
    benchmark_id: str,
    target_name: str,
    fewshot_frac: float,
    seed: int,
    manifest_path: Path = DEFAULT_DATASET_MANIFEST,
    target_set_override: str = "",
    feature_set_override: str = "",
    remove_slot_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    feature_cfg, target_cfg, registry_cfg = load_configs()
    dataset_manifest = load_yaml(manifest_path)
    spec = get_benchmark_spec(registry_cfg, benchmark_id)
    effective_feature_set = feature_set_override or spec.feature_set
    feature_rule = get_feature_set(feature_cfg, effective_feature_set)
    effective_target_set = target_set_override or spec.target_set
    valid_targets = get_target_set(target_cfg, effective_target_set)

    if target_name not in valid_targets:
        raise ValueError(
            f"Target {target_name} is not in target_set {effective_target_set}. "
            f"Valid targets: {valid_targets}"
        )

    defaults = registry_cfg["defaults"]
    source_train_splits = defaults["eval_split_policy"]["source_train_splits"]
    target_train_splits = defaults["eval_split_policy"]["target_train_splits"]
    target_eval_splits = defaults["eval_split_policy"]["target_eval_splits"]
    remove_eval_subjects = defaults["eval_split_policy"]["remove_eval_subjects_from_target_train"]
    drop_rows_with_missing_target = bool(defaults.get("drop_rows_with_missing_target", True))

    target_col = target_column_name(target_name)

    train_df_all = load_dataset_table(spec.train_dataset, dataset_manifest)
    test_df_all = load_dataset_table(spec.test_dataset, dataset_manifest)

    source_train_df, _ = split_by_standard_policy(train_df_all, source_train_splits, [])
    target_train_df, target_eval_df = split_by_standard_policy(test_df_all, target_train_splits, target_eval_splits)

    if remove_eval_subjects:
        target_train_df = remove_eval_subjects_from_target_train(target_train_df, target_eval_df)

    source_feature_cols = resolve_feature_columns(source_train_df, feature_rule)
    target_feature_cols = resolve_feature_columns(target_train_df if len(target_train_df) > 0 else target_eval_df, feature_rule)

    source_feature_cols = drop_target_from_features(source_feature_cols, target_name)
    target_feature_cols = drop_target_from_features(target_feature_cols, target_name)

    source_feature_cols = drop_columns(
        source_feature_cols,
        get_target_leakage_columns(dataset_manifest, spec.train_dataset, target_name),
    )
    target_feature_cols = drop_columns(
        target_feature_cols,
        get_target_leakage_columns(dataset_manifest, spec.test_dataset, target_name),
    )

    remove_slot_names = remove_slot_names or []
    remove_slot_cols = [slot_column_name(slot_name) for slot_name in remove_slot_names]
    source_feature_cols = drop_columns(source_feature_cols, remove_slot_cols)
    target_feature_cols = drop_columns(target_feature_cols, remove_slot_cols)

    common_feature_cols = [c for c in source_feature_cols if c in set(target_feature_cols)]
    if not common_feature_cols:
        raise ValueError("No common feature columns remained after resolution.")

    if target_col not in source_train_df.columns or target_col not in target_eval_df.columns:
        raise KeyError(f"Canonical target column '{target_col}' was not created from the manifest.")

    if drop_rows_with_missing_target:
        source_train_df = source_train_df.dropna(subset=[target_col]).copy()
        target_eval_df = target_eval_df.dropna(subset=[target_col]).copy()
        target_train_df = target_train_df.dropna(subset=[target_col]).copy()

    if spec.setting == "same_cohort":
        X_train = source_train_df[common_feature_cols].copy()
        y_train = source_train_df[target_col].copy()
        X_test = target_eval_df[common_feature_cols].copy()
        y_test = target_eval_df[target_col].copy()
        train_origin = pd.Series("source", index=X_train.index, dtype="object")
        n_source_train = int(len(X_train))
        n_target_fewshot = 0

    elif spec.setting == "cross_cohort_shared":
        X_train = source_train_df[common_feature_cols].copy()
        y_train = source_train_df[target_col].copy()
        X_test = target_eval_df[common_feature_cols].copy()
        y_test = target_eval_df[target_col].copy()
        train_origin = pd.Series("source", index=X_train.index, dtype="object")
        n_source_train = int(len(X_train))
        n_target_fewshot = 0

    elif spec.setting == "cross_cohort_anchor_only":
        fewshot_df = sample_fewshot(target_train_df, frac=fewshot_frac, seed=seed)

        source_block = source_train_df[common_feature_cols + [target_col]].copy()
        target_block = fewshot_df[common_feature_cols + [target_col]].copy()
        source_block["_train_origin"] = "source"
        target_block["_train_origin"] = "target_fewshot"

        if spec.mask_target_cohort_only:
            target_block = maybe_mask_to_observed_slots(target_block, common_feature_cols, spec.observed_slots)
            target_eval_df = maybe_mask_to_observed_slots(target_eval_df, common_feature_cols, spec.observed_slots)

        train_concat = pd.concat([source_block, target_block], axis=0, ignore_index=True)

        X_train = train_concat[common_feature_cols].copy()
        y_train = train_concat[target_col].copy()
        train_origin = train_concat["_train_origin"].copy()
        X_test = target_eval_df[common_feature_cols].copy()
        y_test = target_eval_df[target_col].copy()
        n_source_train = int(len(source_block))
        n_target_fewshot = int(len(target_block))

    else:
        raise ValueError(f"Unsupported setting: {spec.setting}")

    return {
        "benchmark_id": benchmark_id,
        "setting": spec.setting,
        "train_dataset": spec.train_dataset,
        "test_dataset": spec.test_dataset,
        "target_name": target_name,
        "target_set": effective_target_set,
        "feature_set": effective_feature_set,
        "target_col": target_col,
        "fewshot_frac": fewshot_frac,
        "seed": seed,
        "removed_slot_names": remove_slot_names,
        "removed_slot_cols": remove_slot_cols,
        "feature_cols": common_feature_cols,
        "X_train": X_train,
        "y_train": y_train,
        "train_origin": train_origin,
        "X_test": X_test,
        "y_test": y_test,
        "metadata": {
            "n_train": len(X_train),
            "n_test": len(X_test),
            "n_features": len(common_feature_cols),
            "n_source_train": n_source_train,
            "n_target_fewshot": n_target_fewshot,
        },
    }


def build_multi_target_table(
    benchmark_id: str,
    target_names: List[str],
    fewshot_frac: float,
    seed: int,
    manifest_path: Path = DEFAULT_DATASET_MANIFEST,
    target_set_override: str = "",
    feature_set_override: str = "",
) -> Dict[str, Any]:
    feature_cfg, target_cfg, registry_cfg = load_configs()
    dataset_manifest = load_yaml(manifest_path)
    spec = get_benchmark_spec(registry_cfg, benchmark_id)
    effective_feature_set = feature_set_override or spec.feature_set
    feature_rule = get_feature_set(feature_cfg, effective_feature_set)
    effective_target_set = target_set_override or spec.target_set
    valid_targets = get_target_set(target_cfg, effective_target_set)

    unknown_targets = [target for target in target_names if target not in valid_targets]
    if unknown_targets:
        raise ValueError(
            f"Targets {unknown_targets} are not in target_set {effective_target_set}. "
            f"Valid targets: {valid_targets}"
        )
    if not target_names:
        raise ValueError("At least one target is required for build_multi_target_table.")

    defaults = registry_cfg["defaults"]
    source_train_splits = defaults["eval_split_policy"]["source_train_splits"]
    target_train_splits = defaults["eval_split_policy"]["target_train_splits"]
    target_eval_splits = defaults["eval_split_policy"]["target_eval_splits"]
    remove_eval_subjects = defaults["eval_split_policy"]["remove_eval_subjects_from_target_train"]

    target_cols = [target_column_name(target_name) for target_name in target_names]

    train_df_all = load_dataset_table(spec.train_dataset, dataset_manifest)
    test_df_all = load_dataset_table(spec.test_dataset, dataset_manifest)

    source_train_df, _ = split_by_standard_policy(train_df_all, source_train_splits, [])
    target_train_df, target_eval_df = split_by_standard_policy(test_df_all, target_train_splits, target_eval_splits)

    if remove_eval_subjects:
        target_train_df = remove_eval_subjects_from_target_train(target_train_df, target_eval_df)

    source_feature_cols = resolve_feature_columns(source_train_df, feature_rule)
    target_feature_cols = resolve_feature_columns(target_train_df if len(target_train_df) > 0 else target_eval_df, feature_rule)

    leakage_cols_source: List[str] = []
    leakage_cols_target: List[str] = []
    for target_name in target_names:
        leakage_cols_source.extend(get_target_leakage_columns(dataset_manifest, spec.train_dataset, target_name))
        leakage_cols_target.extend(get_target_leakage_columns(dataset_manifest, spec.test_dataset, target_name))

    source_feature_cols = drop_columns(source_feature_cols, sorted(set(leakage_cols_source)))
    target_feature_cols = drop_columns(target_feature_cols, sorted(set(leakage_cols_target)))

    common_feature_cols = [c for c in source_feature_cols if c in set(target_feature_cols)]
    if not common_feature_cols:
        raise ValueError("No common feature columns remained after multi-target leakage removal.")

    missing_source_targets = [c for c in target_cols if c not in source_train_df.columns]
    missing_eval_targets = [c for c in target_cols if c not in target_eval_df.columns]
    if missing_source_targets or missing_eval_targets:
        raise KeyError(
            f"Missing canonical target columns source={missing_source_targets} eval={missing_eval_targets}"
        )

    if spec.setting == "same_cohort":
        X_train = source_train_df[common_feature_cols].copy()
        Y_train = source_train_df[target_cols].copy()
        X_test = target_eval_df[common_feature_cols].copy()
        Y_test = target_eval_df[target_cols].copy()
    elif spec.setting == "cross_cohort_shared":
        X_train = source_train_df[common_feature_cols].copy()
        Y_train = source_train_df[target_cols].copy()
        X_test = target_eval_df[common_feature_cols].copy()
        Y_test = target_eval_df[target_cols].copy()
    elif spec.setting == "cross_cohort_anchor_only":
        raise ValueError("build_multi_target_table currently supports same_cohort and cross_cohort_shared only.")
    else:
        raise ValueError(f"Unsupported setting: {spec.setting}")

    train_observed_mask = Y_train.notna()
    test_observed_mask = Y_test.notna()

    train_keep = train_observed_mask.any(axis=1)
    test_keep = test_observed_mask.any(axis=1)
    X_train = X_train.loc[train_keep].reset_index(drop=True)
    Y_train = Y_train.loc[train_keep].reset_index(drop=True)
    X_test = X_test.loc[test_keep].reset_index(drop=True)
    Y_test = Y_test.loc[test_keep].reset_index(drop=True)

    return {
        "benchmark_id": benchmark_id,
        "setting": spec.setting,
        "train_dataset": spec.train_dataset,
        "test_dataset": spec.test_dataset,
        "target_names": target_names,
        "target_set": effective_target_set,
        "feature_set": effective_feature_set,
        "target_cols": target_cols,
        "fewshot_frac": fewshot_frac,
        "seed": seed,
        "feature_cols": common_feature_cols,
        "X_train": X_train,
        "Y_train": Y_train,
        "X_test": X_test,
        "Y_test": Y_test,
        "metadata": {
            "n_train": len(X_train),
            "n_test": len(X_test),
            "n_features": len(common_feature_cols),
            "n_targets": len(target_cols),
            "train_target_coverage": train_observed_mask.mean().to_dict(),
            "test_target_coverage": test_observed_mask.mean().to_dict(),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark_id", type=str, required=True)
    parser.add_argument("--target", type=str, required=True)
    parser.add_argument("--fewshot_frac", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_DATASET_MANIFEST)
    parser.add_argument("--target_set_override", type=str, default="")
    parser.add_argument("--feature_set_override", type=str, default="")
    parser.add_argument("--save_preview_json", type=str, default="")
    args = parser.parse_args()

    bundle = build_single_target_table(
        benchmark_id=args.benchmark_id,
        target_name=args.target,
        fewshot_frac=args.fewshot_frac,
        seed=args.seed,
        manifest_path=args.manifest,
        target_set_override=args.target_set_override,
        feature_set_override=args.feature_set_override,
    )

    preview = {
        "benchmark_id": bundle["benchmark_id"],
        "setting": bundle["setting"],
        "train_dataset": bundle["train_dataset"],
        "test_dataset": bundle["test_dataset"],
        "target_name": bundle["target_name"],
        "fewshot_frac": bundle["fewshot_frac"],
        "seed": bundle["seed"],
        "target_set": bundle["target_set"],
        "feature_set": bundle["feature_set"],
        "metadata": bundle["metadata"],
        "feature_cols_head": bundle["feature_cols"][:20],
    }

    print(json.dumps(preview, indent=2, ensure_ascii=False))

    if args.save_preview_json:
        out_path = Path(args.save_preview_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(preview, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
