# Data access and local preparation

No raw dataset, restricted microdata, person-level prediction, participant cache, membership list, or fitted model weight is redistributed. Frozen aggregate results allow numerical inspection without these inputs. This package grants no dataset rights. Provider requirements apply to each reviewer independently.

## NHANES — public-use components; restricted components excluded

Use [CDC's datasets and documentation](https://wwwn.cdc.gov/nchs/nhanes/tutorials/datasets.aspx). Only public-use components are relevant here; the artifact does not request restricted CDC variables. The controlled panel's recorded cycles are 2001–2014 for source and 2015–2018 plus `2023` for target. The label `2023` is the **existing adapter's cycle value**. The recovered source lock lists `2023/DEMO_L.xpt`; CDC identifies this as the [August 2021–August 2023 release](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.htm). Keep `2023` as the local adapter directory name.

Expected prepared file: `data/public/nhanes_source_lock/nhanes_common_panel_tokens_v2.parquet`. Its required columns are `subject_id`, `source_cycle`, `source_variable_id`, `value_numeric`, and `observed`. Feature IDs are `NHANES:age`, `NHANES:total_cholesterol`, `NHANES:hba1c`, `NHANES:creatinine`, `NHANES:hemoglobin`, `NHANES:rbc`, `NHANES:wbc`, `NHANES:waist`. The original loader/filter/outcome-generation code is in `scripts/run_crta_v3_mcr_factorial_semisynth_v1.py`. No new sample or synthetic replacement of the underlying NHANES inputs is supplied.

**Recovered existing preparation:** `code/preprocessing/foundation/raw_adapter_source_locks_v2.py` and `code/preprocessing/nhanes_source_lock/` were recovered from the explicitly referenced external project. The original source manifest lists every public XPT filename and checksum. Obtain those components from CDC and place them under `data/public/nhanes_raw/<cycle>/<filename>.xpt`. Do not use the overlapping 2017–March 2020 mirror. The original 14-variable lock is built first; the controlled runner selects its documented eight features.

```sh
python3 reproducibility/prepare_public_nhanes.py
# After all public source hashes pass, explicitly prepare:
python3 reproducibility/prepare_public_nhanes.py --prepare
make reproduce-public
```

The wrapper invokes the existing preparation function, checks source hashes, refuses to overwrite an existing output directory, and checks the frozen Parquet output hash. It does not download or fit models. Its module requires numpy, pandas, pyarrow and pyreadstat; an exact historical lock for the latter two was not recovered. No source-data processing was performed during packaging. The recovered current builder's historical revision was not separately pinned; successful output-hash verification is required before claiming the same frozen input. See `code/preprocessing/EXTERNAL_SOURCE_RECOVERY.md`.

## KNHANES — provider-governed access; no redistribution

Obtain the required health examination and questionnaire source products through the [KDCA KNHANES portal](https://knhanes.kdca.go.kr/knhanes/main.do), following its current download/registration and use procedure. The manuscript calls KNHANES registration/license governed; this artifact conservatively redistributes no person-level KNHANES material regardless of portal access changes. The exact source release/year set underlying the frozen externally prepared L3 file remains **UNKNOWN**. A recovered source manifest identifies `L3_9815_pr90_with_mpls.parquet` with SHA-256 `34762e6e8d2cc20ae7bb2b2b8ea62d2d8c3508ee05a7ed20bc785d5576908ccd`. A related raw-file audit inventories 105 KNHANES files; its filename/cycle/module metadata is supplied in `provenance/knhanes_related_raw_file_inventory.csv`. That audit is not the missing raw-to-L3 selection/build record, so it does not establish which provider release produced the frozen L3 snapshot.

Expected existing layouts used by the sanitized runners include `data/nhanes_knhanes/datasets/knhanes/processed/L3/L3_9815_pr90_with_mpls.parquet` and `data/benchmark/relation_sources/common/`. Required questionnaire columns and the 13-endpoint panel are in Appendix A.4; executable column maps are in the runtime code and `iclr_latex_v3/method_contract/v1/compiler/`. The 1,315-candidate matcher reads the Parquet **schema** and the externally prepared metadata CSV. The original 46-row metadata CSV was recovered and is included, but it covers only 23 target candidates. robustness/correspondence/candidate_inventory_1315.csv supplies all 1,315 column names, exported from the existing prepared-file schema during finalization. Its sorted-name hash matches all 50 frozen full-pool hashes, and the source-file hash matches the frozen summary. No row values were read or exported; this is a new schema projection, not an original historical CSV.

## HRS — registration/licensed provider data; no redistribution

Acquire the authorized source product through [HRS public survey data](https://hrsdata.isr.umich.edu/data-products/public-survey-data) and, where applicable, [RAND HRS products](https://hrsdata.isr.umich.edu/data-products/rand). Public-use in the HRS catalog does not waive registration or data-use terms. A recovered related dataset lock identifies **RAND HRS Longitudinal File 1992–2022 V1**, filename `randhrs1992_2022v1.dta`, with recorded SHA-256 `9faf6db0092c2e66d1e199965c1595d183d24a9f26974e11b80bfdd94adff211`. However, the associated current transfer snapshot has a different hash from the exact frozen M3 snapshot required by the runner. The exact frozen snapshot-to-raw-product linkage, and the separate biomarker product/release, therefore remain **UNVERIFIED/UNKNOWN**; this related lock is evidence, not an asserted exact reconstruction. `provenance/data_source_release_audit.json` records both snapshot hashes and source-document hashes. Do not silently substitute either the current related snapshot or the latest RAND product.

The frozen sign-probe runner expects `data/private/crta_v3/m3_inputs_v1/nhkn_canonical_source_v1.parquet` and `data/private/crta_v3/m3_inputs_v1/hrs_v1_concept_transfer_snapshot.parquet`. Column requirements are in `scripts/crta_v3_m3_nhkn2hrs_runtime_v1.py` and `iclr_latex_v3/method_contract/v1/compiler/runtime_schema_maps_m3_nhkn_hrs_v1.json`. Existing privacy/authorization gates are retained. Original author authorization evidence is not distributed and would not authorize a reviewer; no gate is disabled in this package. Obtain your own provider permission and the original approved preparation chain before a full rerun. Aggregate endpoint effects remain included. The second HRS factorial pair was not executed.

## CAMELS-US — publicly obtainable, externally hosted; observe source terms

Use the hydrological [NCAR CAMELS catalog](https://gdex.ucar.edu/dataset/camels/) and the product identifiers in `iclr_latex_v3/CAMELS_EXTERNAL_DOMAIN_PROTOCOL_V1.md`. This is the catchment dataset, not the cosmological CAMELS project. The exact download availability and full redistribution license for each US product were not confirmed during packaging; no source files are mirrored. Dataset version details not recorded in the frozen manifest remain UNKNOWN.

`scripts/run_crta_v3_camels_native_screen_v1.py` contains the existing preparation/load logic. The sign experiments read prepared `experiments/crta_v3_camels_native_screen_v1/data/source.pkl`, `target.pkl`, and `split_manifest.json`. These are reviewer-created local inputs, not bundled files. The 120-basin extension uses its frozen basin construction; basin is the resampling unit.

## CAMELS-GB — public, Open Government Licence

Use the [2020 EIDC record, DOI 10.5285/8344e4f3-d2ea-44f5-8afa-86d2987543a9](https://catalogue.ceh.ac.uk/documents/8344e4f3-d2ea-44f5-8afa-86d2987543a9). The provider identifies 671 catchments and the Open Government Licence. Preserve attribution and source component notices. Do not substitute the separately released CAMELS-GB v2 for the original product without declaring a new reproduction. No raw basin series are bundled. Use the native-screen/extension preparation code and the same expected local layout as CAMELS-US.

## TabLLM original datasets / released assets — externally hosted, source-specific licenses

Use the [official TabLLM repository](https://github.com/clinicalml/TabLLM) for the nine released dataset serializations and setup, and its corresponding T-Few/checkpoint instructions. Dataset names: Bank, Blood, California Housing, Car, Credit-g, Diabetes, Heart, Income and Jungle. Source licenses remain dataset-specific; this artifact does not assert a blanket redistribution license for them.

Use local relative paths `external/TabLLM/`, `external/t-few/`, `external/t-few-checkpoint-source/`, `models/T0/`, and `models/ia3_pretrained.pt` as explicit runner arguments. `tabllm/asset_identifiers.json` lists recorded upstream commits, model snapshot and checkpoint hashes. Do not replace recorded versions with upstream HEAD. Weights, serialized rows and row-level predictions are omitted; all frozen aggregate comparisons, 24-reference mappings, per-reference metrics and accepted scientific summaries are included.

## Reproduction boundary

`make reproduce-public` and `make reproduce-full` run prerequisite checks only, return nonzero when inputs are missing, and print commands. Nothing downloads or trains automatically. Original preprocessing dependencies missing from the repository are listed in MISSING_ARTIFACTS.md. No synthetic data fixture is represented as a replacement for a scientific input.
