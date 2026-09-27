"""Immutable raw-backed source locks for the next V2 cohort-local adapters.

These builders deliberately do not modify a legacy Stage-B lock.  They create
new, local-only input contracts from raw HRS VBS and KNHANES HN20--HN24 files.
No artifact emitted here authorizes shared-core training or a checkpoint export.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pyreadstat

RAW_COLUMNS = {
    "bun": "pbun",
    "creatinine": "pcr",
    "glucose": "pgluff",
    "hdl_vbs": "phdld",
    "hematocrit": "phct",
    "hemoglobin": "phgb",
    "rbc": "prbc",
    "total_cholesterol_vbs": "pchol",
    "wbc": "pwbc",
}
TARGETS = {
    "KNHANES:age": "age", "KNHANES:he_bun": "HE_BUN", "KNHANES:he_dbp1": "HE_dbp1",
    "KNHANES:he_dbp2": "HE_dbp2", "KNHANES:he_glu": "HE_glu", "KNHANES:he_hba1c": "HE_HbA1c",
    "KNHANES:he_hb": "HE_HB", "KNHANES:he_rbc": "HE_RBC", "KNHANES:he_crea": "HE_crea",
    "KNHANES:he_sbp1": "HE_sbp1", "KNHANES:he_sbp2": "HE_sbp2", "KNHANES:he_chol": "HE_chol",
    "KNHANES:he_tg": "HE_TG", "KNHANES:he_wc": "HE_wc", "KNHANES:he_wbc": "HE_WBC",
}


def _subject_id(raw: pd.DataFrame) -> pd.Series:
    return (raw["hhid"].astype(str).str.lstrip("0") + raw["pn"].astype(str)).astype("int64")


HRS_REASON_VOCAB = (
    "observed",
    "assay_null_within_vbs_panel",
    "not_selected_for_vbs_panel",
)
KN_REASON_VOCAB = (
    "observed",
    "structural_age_ineligible_by_guide",
    "outside_integrated_health_exam_weight_frame",
    "eligible_null_with_integrated_exam_weight_unresolved",
)
KN_MINIMUM_AGE = {
    "age": 0,
    "HE_sbp1": 6,
    "HE_sbp2": 6,
    "HE_dbp1": 6,
    "HE_dbp2": 6,
    "HE_wc": 6,
}
NHANES_CYCLES = ("2001-2002", "2003-2004", "2005-2006", "2007-2008", "2009-2010", "2011-2012", "2013-2014", "2015-2016", "2017-2018", "2023")
NHANES_PANEL = {
    "age": ("DEMO", "RIDAGEYR", "years", "demographics"),
    "waist": ("BMX", "BMXWAIST", "cm", "body_size_proxy"),
    "sbp1": ("BPX", "BPXSY1", "mmHg", "blood_pressure"), "sbp2": ("BPX", "BPXSY2", "mmHg", "blood_pressure"),
    "dbp1": ("BPX", "BPXDI1", "mmHg", "blood_pressure"), "dbp2": ("BPX", "BPXDI2", "mmHg", "blood_pressure"),
    "glucose": ("GLU", "LBXGLU", "mg/dL", "glucose_metabolic"), "hba1c": ("GHB", "LBXGH", "percent", "glucose_metabolic"),
    "hemoglobin": ("CBC", "LBXHGB", "g/dL", "blood_count"), "rbc": ("CBC", "LBXRBCSI", "million_cells_per_uL", "blood_count"),
    "wbc": ("CBC", "LBXWBCSI", "thousand_cells_per_uL", "blood_count"), "creatinine": ("BIOPRO", "LBXSCR", "mg/dL", "renal_function"),
    "total_cholesterol": ("TCHOL", "LBXTC", "mg/dL", "lipid_metabolic"), "triglycerides": ("TRIGLY", "LBXTR", "mg/dL", "lipid_metabolic"),
}
KLOSA_REASON_VOCAB = (
    "observed",
    "feature_wave_not_reviewed",
    "item_missing",
    "raw_sentinel_-9",
    "raw_sentinel_-8",
    "raw_negative_code_unreviewed",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pseudonym(cohort: str, source_key: str) -> str:
    """Return a deterministic local pseudonym without emitting the raw key."""

    digest = hashlib.sha256(f"foundation-v2-local-source-lock|{cohort}|{source_key}".encode("utf-8")).hexdigest()
    return f"{cohort.lower()}v2:{digest[:24]}"


def _atomic_directory(destination: Path) -> tuple[Path, Path]:
    if destination.exists():
        raise FileExistsError(f"immutable source lock already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    return temporary, destination


def _write_checksums(root: Path, names: list[str]) -> Path:
    path = root / "SHA256SUMS"
    path.write_text("".join(f"{_sha256(root / name)}  {name}\n" for name in names), encoding="utf-8")
    return path


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    frame.to_csv(path, index=False, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)


def _archive_frame(path: Path) -> tuple[pd.DataFrame, Any]:
    with tempfile.TemporaryDirectory(prefix="knhanes_adapter_lock_") as raw:
        with zipfile.ZipFile(path) as archive:
            member = next(name for name in archive.namelist() if name.lower().endswith(".sas7bdat"))
            archive.extract(member, raw)
        return pyreadstat.read_sas7bdat(str(Path(raw) / member), disable_datetime_conversion=True)


def _published_manifest(
    *, schema_version: str, created_at: str, source_hashes: dict[str, str], output_dir: Path, output_names: list[str], status: str
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "created_at": created_at,
        "source_sha256": source_hashes,
        "outputs": {name: _sha256(output_dir / name) for name in output_names},
        "status": status,
        "shared_core_training_authorized": False,
        "checkpoint_export_authorized": False,
    }


def build_hrs_vbs_missingness_source_lock(
    *,
    raw_vbs_path: Path,
    legacy_stage_b_tokens_path: Path,
    legacy_hrs_registry_path: Path,
    codebook_candidates_path: Path,
    output_dir: Path,
    created_at: str | None = None,
) -> dict[str, Path]:
    """Rebuild nine VBS tokens with separate assay-null and panel-absence states.

    The legacy token file is used only for its existing wave-16 cohort roster
    and a value-lineage audit. Raw VBS values are the sole values emitted in
    the new source lock.
    """

    raw = pd.read_stata(raw_vbs_path, columns=["hhid", "pn", *RAW_COLUMNS.values()], convert_categoricals=False)
    raw["source_subject_id"] = _subject_id(raw).astype("int64").astype(str)
    if raw["source_subject_id"].duplicated().any():
        raise ValueError("raw VBS source subjects are not unique")
    raw = raw.set_index("source_subject_id", verify_integrity=True)

    legacy = pq.read_table(
        legacy_stage_b_tokens_path,
        columns=["subject_id", "wave", "feature_id", "value_numeric", "observed", "missing_reason"],
    ).to_pandas()
    legacy = legacy.loc[legacy["wave"].eq(16)].copy()
    legacy["source_subject_id"] = legacy["subject_id"].astype(str).str.removeprefix("hrs:")
    roster = pd.DataFrame({"source_subject_id": sorted(legacy["source_subject_id"].unique())})
    if roster.empty:
        raise ValueError("legacy token source has no HRS wave-16 roster")

    registry = pd.read_csv(legacy_hrs_registry_path).fillna("")
    registry = registry.loc[registry["source_column"].astype(str).isin(RAW_COLUMNS)].copy()
    registry["local_variable"] = registry["source_column"].astype(str)
    registry = registry.set_index("local_variable", verify_integrity=True)
    absent = sorted(set(RAW_COLUMNS) - set(registry.index))
    if absent:
        raise ValueError(f"legacy HRS registry lacks VBS variables: {absent}")

    candidates = pd.read_csv(codebook_candidates_path).fillna("")
    candidates["local_variable"] = candidates["registry_id"].astype(str).str.removeprefix("HRS:")
    candidates = candidates.set_index("local_variable", verify_integrity=True)
    if set(candidates.index) != set(RAW_COLUMNS):
        raise ValueError("VBS candidate codebook does not exactly cover the raw VBS variables")

    features = pd.DataFrame(
        [
            {
                "feature_id": str(registry.loc[local, "feature_name"]),
                "source_variable_id": local,
                "official_raw_variable_id": str(candidates.loc[local, "official_raw_variable_id"]),
                "concept_id": str(registry.loc[local, "concept_id"]),
                "local_unit": str(candidates.loc[local, "official_unit"]),
                "observed_domain": f"{candidates.loc[local, 'official_min']}..{candidates.loc[local, 'official_max']}",
                "missingness_class": "vbs_assay_null_vs_panel_absence_separate",
                "time_representation": "local_wave_16_only",
                "training_gate_status": "local_source_lock_only_not_shared_core_eligible",
            }
            for local in RAW_COLUMNS
        ]
    )

    wide = raw.reset_index().melt(
        id_vars=["source_subject_id"],
        value_vars=list(RAW_COLUMNS.values()),
        var_name="raw_column",
        value_name="value_numeric",
    )
    reverse = {raw_name: local_name for local_name, raw_name in RAW_COLUMNS.items()}
    wide["source_variable_id"] = wide["raw_column"].map(reverse)
    payload = roster.merge(features, how="cross").merge(
        wide[["source_subject_id", "source_variable_id", "value_numeric"]],
        on=["source_subject_id", "source_variable_id"],
        how="left",
        indicator="raw_panel_membership",
        validate="one_to_one",
    )
    in_panel = payload["raw_panel_membership"].eq("both")
    payload["observed"] = in_panel & payload["value_numeric"].notna()
    payload["missing_reason"] = np.select(
        [payload["observed"], in_panel],
        ["observed", "assay_null_within_vbs_panel"],
        default="not_selected_for_vbs_panel",
    )
    payload["value_numeric"] = pd.to_numeric(payload["value_numeric"], errors="coerce").where(payload["observed"])
    payload["cohort"] = "HRS"
    payload["wave"] = np.int16(16)
    payload["time_value"] = np.float32(16.0)
    payload["subject_id"] = payload["source_subject_id"].map(lambda key: _pseudonym("HRS", key))
    payload_for_audit = payload.copy()
    payload = payload[
        [
            "cohort", "subject_id", "wave", "time_value", "feature_id", "source_variable_id",
            "official_raw_variable_id", "value_numeric", "observed", "missing_reason",
            "missingness_class", "local_unit", "concept_id", "time_representation",
        ]
    ].sort_values(["subject_id", "feature_id"], kind="stable")
    if payload.duplicated(["subject_id", "wave", "feature_id"]).any():
        raise ValueError("HRS source lock has duplicate subject-wave-feature tokens")
    if set(payload["missing_reason"].unique()) != set(HRS_REASON_VOCAB):
        raise ValueError("HRS source lock failed to materialize all required missingness reasons")

    legacy_vbs = legacy.loc[legacy["feature_id"].isin(features["feature_id"])].copy()
    local_by_feature = features.set_index("feature_id")["source_variable_id"].to_dict()
    legacy_vbs["source_variable_id"] = legacy_vbs["feature_id"].map(local_by_feature)
    comparison = payload_for_audit.merge(
        legacy_vbs[["source_subject_id", "source_variable_id", "value_numeric", "observed", "missing_reason"]],
        on=["source_subject_id", "source_variable_id"],
        how="inner",
        suffixes=("_raw_v2", "_legacy"),
        validate="one_to_one",
    )
    observed = comparison["observed_raw_v2"]
    values_match = np.isclose(
        comparison.loc[observed, "value_numeric_raw_v2"].astype(float),
        comparison.loc[observed, "value_numeric_legacy"].astype(float),
        rtol=0.0,
        atol=0.0,
    ).all()
    if not comparison["observed_raw_v2"].eq(comparison["observed_legacy"]).all() or not values_match:
        raise ValueError("raw VBS values do not reproduce legacy observed values")

    temporary, destination = _atomic_directory(output_dir)
    try:
        token_name = "hrs_vbs_adapter_tokens_v2.parquet"
        registry_name = "hrs_vbs_adapter_registry_v2.csv"
        audit_name = "hrs_vbs_adapter_audit_v2.json"
        readme_name = "README.md"
        pq.write_table(__import__("pyarrow").Table.from_pandas(payload, preserve_index=False), temporary / token_name, compression="zstd")
        _write_csv(temporary / registry_name, features)
        created = created_at or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        counts = payload.groupby(["source_variable_id", "missing_reason"], sort=True).size().unstack(fill_value=0)
        audit = {
            "schema_version": "hrs_vbs_adapter_source_lock_audit_v2",
            "created_at": created,
            "wave": 16,
            "roster_subject_count": int(roster.shape[0]),
            "raw_vbs_subject_count": int(raw.shape[0]),
            "raw_vbs_subjects_in_roster": int(raw.index.isin(roster["source_subject_id"]).sum()),
            "feature_count": int(features.shape[0]),
            "token_count": int(payload.shape[0]),
            "missing_reason_vocab": list(HRS_REASON_VOCAB),
            "per_feature_missing_reason_counts": {str(feature): {str(reason): int(value) for reason, value in row.items()} for feature, row in counts.iterrows()},
            "legacy_observed_mask_exact_match": True,
            "legacy_observed_value_exact_match": True,
            "status": "raw_backed_vbs_missingness_separated_local_source_lock_only",
            "shared_core_training_authorized": False,
        }
        (temporary / audit_name).write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (temporary / readme_name).write_text(
            "# HRS VBS local-adapter source lock v2\n\n"
            "Raw VBS values are materialized with three distinct local states: observed, "
            "assay null within the VBS panel, and not selected for the VBS panel. This is "
            "a source lock only; it does not alter the legacy Stage-B checkpoint or authorize "
            "shared-core training. Subject keys are deterministic local pseudonyms.\n",
            encoding="utf-8",
        )
        source_hashes = {
            "raw_vbs": _sha256(raw_vbs_path),
            "legacy_stage_b_tokens_roster_and_lineage_audit": _sha256(legacy_stage_b_tokens_path),
            "legacy_hrs_registry_concept_metadata": _sha256(legacy_hrs_registry_path),
            "vbs_codebook_candidates": _sha256(codebook_candidates_path),
        }
        manifest_name = "manifest_v2.json"
        manifest = _published_manifest(
            schema_version="hrs_vbs_adapter_source_lock_manifest_v2",
            created_at=created,
            source_hashes=source_hashes,
            output_dir=temporary,
            output_names=[token_name, registry_name, audit_name, readme_name],
            status=audit["status"],
        )
        (temporary / manifest_name).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _write_checksums(temporary, [readme_name, token_name, registry_name, audit_name, manifest_name])
        os.replace(temporary, destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {"root": destination, "tokens": destination / token_name, "registry": destination / registry_name, "audit": destination / audit_name}


def build_knhanes_raw_adapter_source_lock(
    *, raw_root: Path, codebook_path: Path, guide_paths: tuple[Path, ...], output_dir: Path, created_at: str | None = None
) -> dict[str, Path]:
    """Build HN20--HN24 local tokens with official age-eligibility separation."""

    codebook = pd.read_csv(codebook_path).fillna("")
    codebook["_key"] = codebook["변수명"].astype(str).str.casefold()
    code_lookup = codebook.drop_duplicates("_key", keep="first").set_index("_key").to_dict("index")
    if len(guide_paths) != 2 or any(not path.is_file() for path in guide_paths):
        raise ValueError("both KNHANES 2019--21 and 2022--24 official guide files are required")
    target_by_variable = {variable: registry_id for registry_id, variable in TARGETS.items()}
    rows: list[pd.DataFrame] = []
    registry_rows: list[dict[str, str]] = []
    hashes: dict[str, str] = {"codebook": _sha256(codebook_path)}
    for year in range(20, 25):
        archive = raw_root / f"HN{year}_ALL(SAS).zip"
        frame, metadata = _archive_frame(archive)
        if "ID" not in frame.columns or frame["ID"].isna().any() or frame["ID"].duplicated().any():
            raise ValueError(f"{archive.name}: ID must be present, non-null, and unique")
        absent = sorted(set(target_by_variable) - set(frame.columns))
        if absent:
            raise ValueError(f"{archive.name}: missing target variables {absent}")
        year_text = f"20{year}"
        hashes[archive.name] = _sha256(archive)
        source = frame[["ID", "wt_itvex", *target_by_variable]].copy()
        source["eligibility_age_years"] = pd.to_numeric(source["age"], errors="coerce")
        values = source.melt(
            id_vars=["ID", "wt_itvex", "eligibility_age_years"], var_name="raw_variable", value_name="value_numeric"
        )
        values["source_variable_id"] = values["raw_variable"].map(target_by_variable)
        values["cohort"] = "KNHANES"
        values["subject_id"] = values["ID"].astype(str).map(lambda key: _pseudonym("KNHANES", f"{year_text}|{key}"))
        values["source_cycle"] = year_text
        values["time_value"] = np.float32(0.0)
        values["time_representation"] = "cross_sectional_cycle_local_not_shared_temporal_signal"
        values["value_numeric"] = pd.to_numeric(values["value_numeric"], errors="coerce")
        values["observed"] = values["value_numeric"].notna()
        values["minimum_age_by_guide"] = values["raw_variable"].map(KN_MINIMUM_AGE).fillna(10).astype("int16")
        values["missing_reason"] = np.select(
            [
                values["observed"],
                values["eligibility_age_years"].lt(values["minimum_age_by_guide"]),
                values["wt_itvex"].isna(),
            ],
            [
                "observed",
                "structural_age_ineligible_by_guide",
                "outside_integrated_health_exam_weight_frame",
            ],
            default="eligible_null_with_integrated_exam_weight_unresolved",
        )
        rows.append(values[["cohort", "subject_id", "source_cycle", "time_value", "source_variable_id", "raw_variable", "value_numeric", "observed", "missing_reason", "time_representation"]])
        labels = dict(zip(metadata.column_names, metadata.column_labels))
        if year == 20:
            for raw_variable, registry_id in sorted(target_by_variable.items()):
                code = code_lookup.get(raw_variable.casefold(), {})
                registry_rows.append(
                    {
                        "source_variable_id": registry_id,
                        "raw_variable": raw_variable,
                        "official_label": str(code.get("변수설명", "")),
                        "official_unit_text": str(code.get("내용", "")),
                        "raw_column_label": str(labels.get(raw_variable, "")),
                        "missingness_class": "age_ineligible_and_exam_weight_frame_separate_remaining_eligible_null_unresolved",
                        "time_representation": "cross_sectional_cycle_local_not_shared_temporal_signal",
                        "training_gate_status": "closed_weighted_exam_frame_null_semantics_not_resolved",
                    }
                )
    tokens = pd.concat(rows, ignore_index=True)
    if tokens.duplicated(["subject_id", "source_variable_id"]).any():
        raise ValueError("KNHANES source lock has duplicate subject-feature tokens")
    if set(tokens["missing_reason"].unique()) != set(KN_REASON_VOCAB):
        raise ValueError("KNHANES source lock did not preserve SAS-null state")

    temporary, destination = _atomic_directory(output_dir)
    try:
        token_name = "knhanes_hn20_24_adapter_tokens_v2.parquet"
        registry_name = "knhanes_hn20_24_adapter_registry_v2.csv"
        audit_name = "knhanes_hn20_24_adapter_audit_v2.json"
        readme_name = "README.md"
        pq.write_table(__import__("pyarrow").Table.from_pandas(tokens, preserve_index=False), temporary / token_name, compression="zstd")
        _write_csv(temporary / registry_name, pd.DataFrame(registry_rows))
        created = created_at or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        audit = {
            "schema_version": "knhanes_hn20_24_adapter_source_lock_audit_v2",
            "created_at": created,
            "years": [f"20{year}" for year in range(20, 25)],
            "feature_count": len(target_by_variable),
            "token_count": int(tokens.shape[0]),
            "subject_count": int(tokens["subject_id"].nunique()),
            "missing_reason_vocab": list(KN_REASON_VOCAB),
            "observed_count": int(tokens["observed"].sum()),
            "structural_age_ineligible_count": int(tokens["missing_reason"].eq("structural_age_ineligible_by_guide").sum()),
            "outside_integrated_health_exam_weight_frame_count": int(tokens["missing_reason"].eq("outside_integrated_health_exam_weight_frame").sum()),
            "weighted_exam_frame_null_unresolved_count": int(tokens["missing_reason"].eq("eligible_null_with_integrated_exam_weight_unresolved").sum()),
            "official_guide_age_policy": {
                "age": "all ages", "waist_and_blood_pressure": "age >= 6", "blood_laboratories": "age >= 10"
            },
            "status": "raw_hn20_24_source_lock_age_structural_missingness_separated_remaining_semantics_closed",
            "shared_core_training_authorized": False,
        }
        (temporary / audit_name).write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (temporary / readme_name).write_text(
            "# KNHANES HN20--HN24 local-adapter source lock v2\n\n"
            "All 15 raw variables are materialized from five supplied SAS archives. Official guides "
            "separate nulls for people younger than the collection age (6 for waist/blood pressure, "
            "10 for blood laboratories) as structural absence. Age-eligible nulls with no `wt_itvex` "
            "are separately marked as outside the integrated health/exam weight frame, without claiming "
            "a specific nonparticipation cause. Only weighted-frame nulls remain unresolved and keep this "
            "source lock closed for training. Subject keys are deterministic local pseudonyms, and cycle "
            "is retained only as local metadata.\n",
            encoding="utf-8",
        )
        manifest_name = "manifest_v2.json"
        manifest = _published_manifest(
            schema_version="knhanes_hn20_24_adapter_source_lock_manifest_v2",
            created_at=created,
            source_hashes={**hashes, **{f"official_guide_{index + 1}": _sha256(path) for index, path in enumerate(guide_paths)}},
            output_dir=temporary,
            output_names=[token_name, registry_name, audit_name, readme_name],
            status=audit["status"],
        )
        (temporary / manifest_name).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _write_checksums(temporary, [readme_name, token_name, registry_name, audit_name, manifest_name])
        os.replace(temporary, destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {"root": destination, "tokens": destination / token_name, "registry": destination / registry_name, "audit": destination / audit_name}


def build_nhanes_common_panel_source_lock(*, raw_root: Path, output_dir: Path, created_at: str | None = None) -> dict[str, Path]:
    """Build a raw XPT lock for an explicitly cycle-local 14-feature NHANES panel."""
    records: list[pd.DataFrame] = []
    hashes: dict[str, str] = {}
    cycle_stats: dict[str, int] = {}
    for cycle in NHANES_CYCLES:
        root = raw_root / cycle
        demo = next(iter(sorted(root.glob("DEMO_*.xpt"))), None)
        if demo is None:
            raise ValueError(f"{cycle}: independent DEMO XPT absent")
        base = pd.read_sas(demo, format="xport", encoding="utf-8")[["SEQN"]].copy()
        base["source_cycle"] = cycle
        hashes[str(demo.relative_to(raw_root))] = _sha256(demo)
        cycle_stats[cycle] = len(base)
        for local, (module, column, unit, concept) in NHANES_PANEL.items():
            file = next(iter(sorted(root.glob(f"{module}_*.xpt"))), None)
            value = pd.Series(np.nan, index=base.index, dtype="float64")
            availability = "source_column_unavailable_in_cycle"
            if file is not None:
                part = pd.read_sas(file, format="xport", encoding="utf-8")
                hashes[str(file.relative_to(raw_root))] = _sha256(file)
                if column in part.columns and "SEQN" in part.columns:
                    lookup = part[["SEQN", column]].drop_duplicates("SEQN").set_index("SEQN")[column]
                    value = pd.to_numeric(base["SEQN"].map(lookup), errors="coerce")
                    availability = "source_column_available"
            out = base[["SEQN", "source_cycle"]].copy()
            out["source_variable_id"] = f"NHANES:{local}"
            out["raw_variable"] = column
            out["value_numeric"] = value
            out["observed"] = value.notna()
            out["missing_reason"] = np.where(out["observed"], "observed", "raw_null_unspecified" if availability == "source_column_available" else availability)
            out["local_unit"] = unit
            out["concept_id"] = concept
            records.append(out)
    tokens = pd.concat(records, ignore_index=True)
    tokens["cohort"] = "NHANES"
    tokens["subject_id"] = tokens.apply(lambda row: _pseudonym("NHANES", f"{row.source_cycle}|{int(row.SEQN)}"), axis=1)
    tokens["time_value"] = np.float32(0.0)
    tokens["time_representation"] = "cross_sectional_cycle_local_not_shared_temporal_signal"
    tokens = tokens[["cohort", "subject_id", "source_cycle", "time_value", "source_variable_id", "raw_variable", "value_numeric", "observed", "missing_reason", "local_unit", "concept_id", "time_representation"]]
    if tokens.duplicated(["subject_id", "source_variable_id"]).any(): raise ValueError("NHANES duplicate subject-feature token")
    temporary, destination = _atomic_directory(output_dir)
    try:
        names = ["README.md", "nhanes_common_panel_tokens_v2.parquet", "nhanes_common_panel_registry_v2.csv", "nhanes_common_panel_audit_v2.json", "manifest_v2.json"]
        pq.write_table(__import__("pyarrow").Table.from_pandas(tokens, preserve_index=False), temporary / names[1], compression="zstd")
        registry = pd.DataFrame([{"source_variable_id":f"NHANES:{k}","raw_variable":v[1],"local_unit":v[2],"concept_id":v[3],"missingness_class":"raw_null_or_cycle_column_unavailable_local","time_representation":"cross_sectional_cycle_local_not_shared_temporal_signal","training_gate_status":"local_source_lock_only_pending_pre_ssl_gate"} for k,v in NHANES_PANEL.items()])
        _write_csv(temporary / names[2], registry)
        created = created_at or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        audit = {"schema_version":"nhanes_common_panel_source_lock_audit_v2","created_at":created,"cycles":list(NHANES_CYCLES),"cycle_subject_counts":cycle_stats,"feature_count":len(NHANES_PANEL),"token_count":int(len(tokens)),"missing_reason_counts":{str(k):int(v) for k,v in tokens.missing_reason.value_counts().items()},"status":"raw_xpt_common_panel_local_source_lock_only","shared_core_training_authorized":False}
        (temporary / names[3]).write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        (temporary / names[0]).write_text("# NHANES common-panel local source lock v2\n\nOnly independent raw XPT cycles are used; the 2017--March 2020 mirror is excluded. A raw null and a source column unavailable in a given cycle remain distinct cohort-local states.\n",encoding="utf-8")
        manifest=_published_manifest(schema_version="nhanes_common_panel_source_lock_manifest_v2",created_at=created,source_hashes=hashes,output_dir=temporary,output_names=names[:-1],status=audit["status"])
        (temporary / names[4]).write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        _write_checksums(temporary,names)
        os.replace(temporary,destination)
    except Exception:
        shutil.rmtree(temporary,ignore_errors=True); raise
    return {"root":destination,"tokens":destination/names[1],"registry":destination/names[2],"audit":destination/names[3]}


def _klosa_wave_members(excel_zip: Path) -> dict[int, str]:
    """Return one independently named individual-data workbook per KLoSA wave."""

    with zipfile.ZipFile(excel_zip) as archive:
        matches: dict[int, list[str]] = {wave: [] for wave in range(1, 10)}
        for member in archive.namelist():
            name = Path(member).name
            if name.lower().endswith(".xlsx") and len(name) == 9 and name[:2].casefold() == "lt" and name[2:4].isdigit():
                wave = int(name[2:4])
                if wave in matches:
                    matches[wave].append(member)
    selected: dict[int, str] = {}
    for wave, candidates in matches.items():
        if len(candidates) != 1:
            raise ValueError(f"KLoSA wave {wave} must have exactly one LtNN.xlsx member, got {candidates}")
        selected[wave] = candidates[0]
    return selected


def _klosa_source_column(frame: pd.DataFrame, expected: str) -> str | None:
    """Resolve workbook case variance without accepting an ambiguous source column."""

    aliases = [column for column in frame.columns if str(column).casefold() == expected.casefold()]
    if len(aliases) > 1:
        raise ValueError(f"ambiguous KLoSA source column for {expected}: {aliases}")
    return aliases[0] if aliases else None


def _klosa_scope_contains(scope: str, wave: int) -> bool:
    start, end = (int(part) for part in scope.split("-"))
    return start <= wave <= end


def _klosa_raw_code(value: object) -> str | None:
    if pd.isna(value):
        return None
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.notna(numeric) and float(numeric).is_integer():
        return str(int(numeric))
    return str(value).strip()


def build_klosa_raw_source_lock(
    *,
    raw_excel_zip: Path,
    codebook_zip: Path,
    registry_path: Path,
    sentinel_audit_path: Path,
    code_direction_path: Path,
    output_dir: Path,
    created_at: str | None = None,
) -> dict[str, Path]:
    """Build a raw KLoSA 1--9-wave lock with raw codes and local missingness.

    The source Excel workbooks use unsupported worksheet extension metadata in
    the local ``openpyxl`` version.  They are therefore extracted verbatim and
    converted by LibreOffice to CSV before parsing.  This is an I/O workaround,
    not a semantic transformation: source ZIP and codebook hashes are bound in
    the manifest and raw categorical codes remain local ``value_code`` values.
    """

    registry = pd.read_csv(registry_path).fillna("")
    required = {"feature_name", "source_column", "value_type", "source_wave_scope", "local_unit", "concept_id"}
    absent = required - set(registry.columns)
    if absent:
        raise ValueError(f"KLoSA registry lacks columns: {sorted(absent)}")
    registry = registry.sort_values("registry_order", kind="stable").reset_index(drop=True)
    if registry["feature_name"].duplicated().any():
        raise ValueError("KLoSA registry feature names must be unique")
    sentinels = pd.read_csv(sentinel_audit_path).fillna("")
    directions = pd.read_csv(code_direction_path).fillna("")
    if not raw_excel_zip.is_file() or not codebook_zip.is_file():
        raise ValueError("KLoSA raw Excel ZIP and codebook ZIP are both required")

    token_frames: list[pd.DataFrame] = []
    per_wave_subjects: dict[str, int] = {}
    raw_columns_present: dict[str, list[str]] = {}
    with tempfile.TemporaryDirectory(prefix="klosa_raw_adapter_") as scratch:
        scratch_path = Path(scratch)
        extracted = scratch_path / "xlsx"
        converted = scratch_path / "csv"
        extracted.mkdir()
        converted.mkdir()
        members = _klosa_wave_members(raw_excel_zip)
        with zipfile.ZipFile(raw_excel_zip) as archive:
            for wave, member in members.items():
                out = extracted / f"Lt{wave:02d}.xlsx"
                with archive.open(member) as source, out.open("wb") as target:
                    shutil.copyfileobj(source, target)
        for wave in range(1, 10):
            workbook = extracted / f"Lt{wave:02d}.xlsx"
            subprocess.run(
                ["libreoffice", "--headless", "--convert-to", "csv", "--outdir", str(converted), str(workbook)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            csv_path = converted / f"Lt{wave:02d}.csv"
            if not csv_path.is_file():
                raise ValueError(f"LibreOffice did not create {csv_path.name}")
            frame = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
            pid = _klosa_source_column(frame, "pid")
            if pid is None or frame[pid].eq("").any() or frame[pid].duplicated().any():
                raise ValueError(f"KLoSA wave {wave}: pid must be present, nonblank, and unique")
            per_wave_subjects[str(wave)] = int(frame.shape[0])
            wave_records: list[pd.DataFrame] = []
            expected_columns: list[str] = []
            for spec in registry.itertuples(index=False):
                scope = str(spec.source_wave_scope)
                source_suffix = str(spec.source_column)
                scoped = _klosa_scope_contains(scope, wave)
                expected = "wave_index" if source_suffix == "wave_index" else f"w{wave:02d}{source_suffix}"
                if source_suffix != "wave_index":
                    expected_columns.append(expected)
                source_column = _klosa_source_column(frame, expected) if scoped and source_suffix != "wave_index" else None
                if scoped and source_suffix != "wave_index" and source_column is None:
                    raise ValueError(f"KLoSA wave {wave}: reviewed source column unavailable: {expected}")
                out = pd.DataFrame({"source_pid": frame[pid].astype(str)})
                out["cohort"] = "KLOSA"
                out["subject_id"] = out["source_pid"].map(lambda key: _pseudonym("KLOSA", key))
                out["wave"] = np.int16(wave)
                out["time_value"] = np.float32(float(wave))
                out["feature_id"] = str(spec.feature_name)
                out["feature_type"] = str(spec.value_type)
                out["source_variable_id"] = f"KLOSA:{source_suffix}"
                out["raw_variable"] = expected
                out["local_unit"] = str(spec.local_unit)
                out["concept_id"] = str(spec.concept_id)
                out["time_representation"] = "local_panel_wave_index_not_shared_clock"
                out["value_numeric"] = np.nan
                out["value_code"] = pd.NA
                if source_suffix == "wave_index":
                    out["value_numeric"] = float(wave)
                    out["observed"] = True
                    out["missing_reason"] = "observed"
                elif not scoped:
                    out["observed"] = False
                    out["missing_reason"] = "feature_wave_not_reviewed"
                else:
                    raw_value = frame[source_column]
                    parsed = pd.to_numeric(raw_value, errors="coerce")
                    negative = parsed.lt(0)
                    observed = raw_value.ne("") & parsed.notna() & ~negative
                    out["observed"] = observed
                    out["missing_reason"] = np.select(
                        [observed, raw_value.eq(""), parsed.eq(-9), parsed.eq(-8), negative],
                        ["observed", "item_missing", "raw_sentinel_-9", "raw_sentinel_-8", "raw_negative_code_unreviewed"],
                        default="item_missing",
                    )
                    if str(spec.value_type) == "continuous":
                        out.loc[observed, "value_numeric"] = parsed.loc[observed].astype(float)
                    else:
                        out.loc[observed, "value_code"] = raw_value.loc[observed].map(_klosa_raw_code).astype("string")
                wave_records.append(out)
            raw_columns_present[str(wave)] = sorted(expected_columns)
            wave_payload = pd.concat(wave_records, ignore_index=True)
            if wave_payload.duplicated(["subject_id", "wave", "feature_id"]).any():
                raise ValueError(f"KLoSA wave {wave}: duplicate subject-wave-feature tokens")
            token_frames.append(wave_payload)
    tokens = pd.concat(token_frames, ignore_index=True).drop(columns=["source_pid"])
    tokens = tokens.sort_values(["subject_id", "wave", "feature_id"], kind="stable").reset_index(drop=True)
    unexpected = set(tokens["missing_reason"].unique()) - set(KLOSA_REASON_VOCAB)
    if unexpected:
        raise ValueError(f"KLoSA unexpected missingness states: {sorted(unexpected)}")
    if tokens.duplicated(["subject_id", "wave", "feature_id"]).any():
        raise ValueError("KLoSA source lock has duplicate tokens")
    if tokens.loc[tokens["observed"] & tokens["feature_type"].eq("continuous"), "value_numeric"].isna().any():
        raise ValueError("KLoSA observed continuous token lacks numeric value")
    if tokens.loc[tokens["observed"] & ~tokens["feature_type"].isin(["continuous", "time"]), "value_code"].isna().any():
        raise ValueError("KLoSA observed discrete token lacks raw local code")

    temporary, destination = _atomic_directory(output_dir)
    try:
        names = ["README.md", "klosa_raw_adapter_tokens_v2.parquet", "klosa_raw_adapter_registry_v2.csv", "klosa_raw_adapter_audit_v2.json", "manifest_v2.json"]
        pq.write_table(__import__("pyarrow").Table.from_pandas(tokens, preserve_index=False), temporary / names[1], compression="zstd")
        registry_out = registry.assign(
            raw_workbook_pattern="Lt01.xlsx..Lt09.xlsx from EXCEL.zip",
            raw_code_representation="discrete values retained as local source codes",
            missingness_class="reviewed_wave_absence_item_missing_and_raw_negative_codes_separate",
            time_representation="local_panel_wave_index_not_shared_clock",
            training_gate_status="local_source_lock_only_pending_adapter_semantic_review",
        )
        _write_csv(temporary / names[2], registry_out)
        created = created_at or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        audit = {
            "schema_version": "klosa_raw_adapter_source_lock_audit_v2",
            "created_at": created,
            "waves": list(range(1, 10)),
            "wave_subject_counts": per_wave_subjects,
            "feature_count": int(registry.shape[0]),
            "token_count": int(tokens.shape[0]),
            "subject_count_across_waves": int(tokens["subject_id"].nunique()),
            "missing_reason_counts": {str(key): int(value) for key, value in tokens["missing_reason"].value_counts().sort_index().items()},
            "raw_columns_present_by_wave": raw_columns_present,
            "sentinel_audit_rows_bound": int(sentinels.shape[0]),
            "code_direction_rows_bound": int(directions.shape[0]),
            "status": "raw_excel_panel_source_lock_local_codes_and_missingness_preserved",
            "shared_core_training_authorized": False,
            "checkpoint_export_authorized": False,
        }
        (temporary / names[3]).write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (temporary / names[0]).write_text(
            "# KLoSA raw local-adapter source lock v2\n\n"
            "All nine raw individual wave workbooks are extracted verbatim from `EXCEL.zip` and converted to CSV by LibreOffice only because the local XLSX reader rejects workbook metadata. Discrete values retain their raw local codes; local wave availability, blank items, reviewed -9/-8 sentinels, and other negative raw codes remain distinct. This is a source lock only and does not authorize shared-core training or checkpoint export.\n",
            encoding="utf-8",
        )
        manifest = _published_manifest(
            schema_version="klosa_raw_adapter_source_lock_manifest_v2",
            created_at=created,
            source_hashes={
                "raw_excel_zip": _sha256(raw_excel_zip),
                "raw_codebook_zip": _sha256(codebook_zip),
                "feature_registry": _sha256(registry_path),
                "sentinel_audit": _sha256(sentinel_audit_path),
                "code_direction": _sha256(code_direction_path),
            },
            output_dir=temporary,
            output_names=names[:-1],
            status=audit["status"],
        )
        (temporary / names[4]).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _write_checksums(temporary, names)
        os.replace(temporary, destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {"root": destination, "tokens": destination / names[1], "registry": destination / names[2], "audit": destination / names[3]}
