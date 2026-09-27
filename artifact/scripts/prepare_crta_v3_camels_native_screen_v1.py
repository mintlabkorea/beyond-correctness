#!/usr/bin/env python3
"""Prepare a leakage-safe CAMELS-US to CAMELS-GB development screen.

The screen uses only native source/target files. Basin selection is a salted
hash of gauge ID and never reads outcome values. Daily meteorology is reduced
to a fixed weekly cadence after deterministic trailing summaries are built;
no lagged discharge or other outcome-derived feature is emitted.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "iclr_latex_v3" / "method_contract" / "v1"
DEFAULT_US = Path("external/Downloads/CAMELS_US")
DEFAULT_GB = Path("external/Downloads/CAMELS_GB")
DEFAULT_OUT = ROOT / "experiments/crta_v3_camels_native_screen_v1/data"
REGISTRY_ROOT = (
    CONTRACT
    / "camels_documents/v1/materialized/camels_us_to_gb_native_v1"
)
START = pd.Timestamp("1981-01-01")
END = pd.Timestamp("2008-09-30")
WARMUP = START - pd.Timedelta(days=30)
CADENCE_DAYS = 7
ROLLING_WINDOWS = (3, 7, 30)
SOURCE_DYNAMIC = ("dayl", "prcp", "srad", "swe", "tmax", "tmin", "vp")
TARGET_DYNAMIC = (
    "precipitation_cehgear",
    "precipitation_haduk",
    "pet_chess",
    "peti_chess",
    "pet_hydrope",
    "peti_hydrope",
    "temperature_chess",
    "temperature_haduk",
)
SPLIT_SALT = "crta-camels-native-development-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camels-us-root", type=Path, default=DEFAULT_US)
    parser.add_argument("--camels-gb-root", type=Path, default=DEFAULT_GB)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--source-basin-count", type=int, default=64)
    parser.add_argument("--target-query-count", type=int, default=12)
    parser.add_argument("--target-support-pool-count", type=int, default=12)
    parser.add_argument("--split-salt", default=SPLIT_SALT)
    parser.add_argument("--exclude-target-manifest", type=Path)
    parser.add_argument(
        "--evaluation-role",
        choices=["development_screen", "confirmatory"],
        default="development_screen",
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_order(ids: list[str], namespace: str, split_salt: str = SPLIT_SALT) -> list[str]:
    return sorted(
        ids,
        key=lambda gauge: hashlib.sha256(
            f"{split_salt}|{namespace}|{gauge}".encode("utf-8")
        ).hexdigest(),
    )


def registry_ids(side: str) -> tuple[list[str], dict[str, str]]:
    name = (
        "source_camels_us_native_registry.csv"
        if side == "source"
        else "target_camels_gb_v2_native_registry.csv"
    )
    frame = pd.read_csv(REGISTRY_ROOT / name, dtype=str).fillna("")
    return frame["column_id"].tolist(), dict(
        zip(frame["column_id"], frame["native_category"])
    )


def source_attributes(root: Path, selected_ids: list[str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for category in ("topo", "clim", "vege", "soil", "geol"):
        path = root / f"camels_{category}.txt"
        frame = pd.read_csv(path, sep=";", dtype={"gauge_id": str})
        frame["gauge_id"] = frame["gauge_id"].str.zfill(8)
        keep = ["gauge_id", *[column for column in selected_ids if column in frame]]
        frames.append(frame[keep])
    output = frames[0]
    for frame in frames[1:]:
        output = output.merge(frame, on="gauge_id", how="outer", validate="one_to_one")
    for column in selected_ids:
        if column in output:
            output[column] = pd.to_numeric(output[column], errors="coerce")
    return output


def target_attributes(root: Path, selected_ids: list[str], categories: dict[str, str]) -> pd.DataFrame:
    by_file: dict[Path, list[str]] = {}
    for column in selected_ids:
        category = categories[column]
        if category == "camels_gb_v2_daily":
            continue
        path = root / "attributes" / f"{category}.csv"
        by_file.setdefault(path, []).append(column)
    frames: list[pd.DataFrame] = []
    for path, columns in sorted(by_file.items()):
        header = pd.read_csv(path, nrows=0).columns.tolist()
        keep = ["gauge_id", *[column for column in columns if column in header]]
        frame = pd.read_csv(path, usecols=keep, dtype={"gauge_id": str})
        frame["gauge_id"] = frame["gauge_id"].astype(str)
        frames.append(frame)
    output = frames[0]
    for frame in frames[1:]:
        output = output.merge(frame, on="gauge_id", how="outer", validate="one_to_one")
    for column in selected_ids:
        if column in output:
            output[column] = pd.to_numeric(output[column], errors="coerce")
    return output


def rolling_and_sample(frame: pd.DataFrame, dynamic: tuple[str, ...]) -> pd.DataFrame:
    frame = frame.sort_values("date").reset_index(drop=True)
    for column in dynamic:
        values = pd.to_numeric(frame[column], errors="coerce")
        frame[column] = values
        for window in ROLLING_WINDOWS:
            frame[f"{column}__trailmean_{window}"] = values.rolling(
                window, min_periods=window
            ).mean()
    frame = frame[frame["date"].between(START, END)].copy()
    cadence = (frame["date"] - START).dt.days.mod(CADENCE_DAYS).eq(0)
    return frame[cadence].reset_index(drop=True)


def source_member_maps(names: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    forcing: dict[str, str] = {}
    flow: dict[str, str] = {}
    for name in names:
        match = re.search(
            r"basin_mean_forcing/daymet/\d{2}/(\d{8})_lump_cida_forcing_leap\.txt$",
            name,
        )
        if match:
            forcing[match.group(1)] = name
        match = re.search(r"usgs_streamflow/\d{2}/(\d{8})_streamflow_qc\.txt$", name)
        if match:
            flow[match.group(1)] = name
    return forcing, flow


def read_source_basin(
    archive: zipfile.ZipFile,
    forcing_member: str,
    flow_member: str,
    gauge_id: str,
    static_row: pd.Series,
) -> pd.DataFrame:
    raw = archive.read(forcing_member).decode("utf-8", errors="replace").splitlines()
    basin_area_m2 = float(raw[2].strip())
    forcing = pd.read_csv(io.StringIO("\n".join(raw[4:])), sep=r"\s+")
    forcing.columns = ["year", "month", "day", "hour", *SOURCE_DYNAMIC]
    forcing["date"] = pd.to_datetime(
        dict(year=forcing["year"], month=forcing["month"], day=forcing["day"]),
        errors="coerce",
    )
    forcing = forcing[forcing["date"].between(WARMUP, END)].copy()
    flow = pd.read_csv(
        io.BytesIO(archive.read(flow_member)),
        sep=r"\s+",
        header=None,
        names=["gauge", "year", "month", "day", "streamflow_cfs", "quality"],
    )
    flow["date"] = pd.to_datetime(
        dict(year=flow["year"], month=flow["month"], day=flow["day"]),
        errors="coerce",
    )
    flow["streamflow_cfs"] = pd.to_numeric(flow["streamflow_cfs"], errors="coerce")
    flow.loc[flow["streamflow_cfs"] < 0, "streamflow_cfs"] = np.nan
    frame = forcing.merge(flow[["date", "streamflow_cfs"]], on="date", how="left")
    frame["discharge_mm_day"] = (
        frame["streamflow_cfs"] * 0.028316846592 * 86400.0 * 1000.0 / basin_area_m2
    )
    frame = rolling_and_sample(frame, SOURCE_DYNAMIC)
    frame["gauge_id"] = gauge_id
    for column, value in static_row.items():
        if column != "gauge_id":
            frame[column] = value
    return frame


def read_target_basin(path: Path, gauge_id: str, static_row: pd.Series) -> pd.DataFrame:
    frame = pd.read_csv(path, parse_dates=["date"])
    frame = frame[frame["date"].between(WARMUP, END)].copy()
    frame = rolling_and_sample(frame, TARGET_DYNAMIC)
    frame["gauge_id"] = gauge_id
    frame["discharge_mm_day"] = pd.to_numeric(frame["discharge_spec"], errors="coerce")
    for column, value in static_row.items():
        if column != "gauge_id":
            frame[column] = value
    return frame


def main() -> int:
    args = parse_args()
    output_files = [
        args.out_dir / "source.pkl",
        args.out_dir / "target.pkl",
        args.out_dir / "split_manifest.json",
    ]
    if not args.force and all(path.exists() for path in output_files):
        print(json.dumps({"status": "exists", "out_dir": str(args.out_dir)}))
        return 0
    source_ids, _ = registry_ids("source")
    target_ids, target_categories = registry_ids("target")
    source_static_ids = [column for column in source_ids if column not in SOURCE_DYNAMIC]
    target_static_ids = [column for column in target_ids if column not in TARGET_DYNAMIC]
    source_static = source_attributes(args.camels_us_root, source_static_ids)
    target_static = target_attributes(args.camels_gb_root, target_static_ids, target_categories)

    archive_path = args.camels_us_root / "basin_timeseries_v1p2_metForcing_obsFlow.zip"
    with zipfile.ZipFile(archive_path) as archive:
        forcing, flow = source_member_maps(archive.namelist())
        available_source = sorted(set(forcing) & set(flow) & set(source_static["gauge_id"]))
        selected_source = hash_order(available_source, "source", args.split_salt)[
            : args.source_basin_count
        ]
        source_rows = source_static.set_index("gauge_id")
        source_parts = [
            read_source_basin(
                archive, forcing[gauge], flow[gauge], gauge, source_rows.loc[gauge]
            )
            for gauge in selected_source
        ]

    target_paths: dict[str, Path] = {}
    daily_root = args.camels_gb_root / "timeseries/meteorological/CAMELS_GB_v2_daily"
    for path in sorted(daily_root.glob("camels_gb_v2_hydromet_daily_timeseries_*.csv")):
        match = re.search(r"timeseries_(.+?)_\d{8}-\d{8}\.csv$", path.name)
        if match:
            target_paths[match.group(1)] = path
    available_target = sorted(set(target_paths) & set(target_static["gauge_id"]))
    excluded_target_ids: set[str] = set()
    if args.exclude_target_manifest:
        exclusion = json.loads(args.exclude_target_manifest.read_text(encoding="utf-8"))
        excluded_target_ids.update(map(str, exclusion["target_query_basin_ids"]))
        excluded_target_ids.update(map(str, exclusion["target_support_pool_basin_ids"]))
        available_target = [
            gauge for gauge in available_target if gauge not in excluded_target_ids
        ]
    selected_target = hash_order(available_target, "target", args.split_salt)[:
        args.target_query_count + args.target_support_pool_count
    ]
    query_ids = selected_target[: args.target_query_count]
    support_pool_ids = selected_target[args.target_query_count :]
    target_rows = target_static.set_index("gauge_id")
    target_parts = [
        read_target_basin(target_paths[gauge], gauge, target_rows.loc[gauge])
        for gauge in selected_target
    ]

    source = pd.concat(source_parts, ignore_index=True)
    target = pd.concat(target_parts, ignore_index=True)
    source = source[np.isfinite(source["discharge_mm_day"]) & (source["discharge_mm_day"] >= 0)]
    target = target[np.isfinite(target["discharge_mm_day"]) & (target["discharge_mm_day"] >= 0)]
    retained_source = sorted(source["gauge_id"].unique().tolist())
    retained_target = sorted(target["gauge_id"].unique().tolist())
    if retained_source != sorted(selected_source) or retained_target != sorted(selected_target):
        raise ValueError("At least one hash-selected basin has no valid outcome rows in the fixed period")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    source.to_pickle(args.out_dir / "source.pkl")
    target.to_pickle(args.out_dir / "target.pkl")
    manifest: dict[str, Any] = {
        "experiment": "crta_v3_camels_native_screen_v1",
        "evaluation_role": args.evaluation_role,
        "split_unit": "gauge_id",
        "selection_rule": "ascending_sha256(split_salt|namespace|gauge_id)",
        "split_salt": args.split_salt,
        "date_start": START.date().isoformat(),
        "date_end": END.date().isoformat(),
        "warmup_start": WARMUP.date().isoformat(),
        "cadence_days": CADENCE_DAYS,
        "trailing_mean_windows_days": list(ROLLING_WINDOWS),
        "lagged_outcome_features": False,
        "source_basin_ids": selected_source,
        "target_query_basin_ids": query_ids,
        "target_support_pool_basin_ids": support_pool_ids,
        "excluded_target_basin_ids": sorted(excluded_target_ids),
        "excluded_target_manifest": (
            str(args.exclude_target_manifest) if args.exclude_target_manifest else None
        ),
        "source_rows": len(source),
        "target_rows": len(target),
        "source_dynamic_columns": list(SOURCE_DYNAMIC),
        "target_dynamic_columns": list(TARGET_DYNAMIC),
        "source_registry_columns": source_ids,
        "target_registry_columns": target_ids,
        "inputs": {
            "camels_us_archive": str(archive_path),
            "camels_us_archive_sha256": sha256(archive_path),
            "camels_gb_daily_root": str(daily_root),
        },
        "outputs": {
            "source": str(args.out_dir / "source.pkl"),
            "source_sha256": sha256(args.out_dir / "source.pkl"),
            "target": str(args.out_dir / "target.pkl"),
            "target_sha256": sha256(args.out_dir / "target.pkl"),
        },
    }
    (args.out_dir / "split_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "source_basins": len(selected_source),
                "target_query_basins": len(query_ids),
                "target_support_pool_basins": len(support_pool_ids),
                "source_rows": len(source),
                "target_rows": len(target),
                "out_dir": str(args.out_dir),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
