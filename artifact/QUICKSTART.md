# Quickstart

Extract the single top-level directory and run from it:

```sh
make verify
make scan
make validate
```

All three Level 1 commands return zero for this sealed release. make verify deterministically rewrites the same verification CSV/Markdown. make scan includes XLSX XML/properties and PDF author metadata (pdfinfo when installed). make validate verifies both release manifests and explicitly checks the disclosed Level 2/3 limitations; it does not claim every historical input/environment was recovered.

To write temporary reports without changing the sealed tree, supply an output directory **outside** the archive:

```sh
python3 reproducibility/verify_reported_results.py --output-dir ../verification_report
python3 reproducibility/validate_artifact.py --output-dir ../validation_report
```

The deliberately stricter completeness check fails while the declared reconstruction gaps remain:

```sh
python3 reproducibility/validate_artifact.py --require-full-completeness
```

Optional figures and tables (install outside the sealed tree to preserve its manifest):

```sh
python3 -m venv ../artifact_runtime
../artifact_runtime/bin/pip install -r reproducibility/environments/verification-requirements.txt
make figures PYTHON=../artifact_runtime/bin/python
make tables PYTHON=../artifact_runtime/bin/python
```

These commands regenerate outputs and may change generated-file bytes; run integrity checks on a fresh extraction first. They do not fit models. The conceptual diagram is frozen. make reproduce-public and make reproduce-full are prerequisite checks and return nonzero until external inputs are supplied; neither downloads data nor starts training.
