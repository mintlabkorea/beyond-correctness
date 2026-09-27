# Numerical environments

The manuscript requirements files are extracted declarations, **not recovered execution locks**. Compare them with `version_audit.csv`, recorded per-cell versions and model manifests. The local packaging interpreter is not evidence of the historical numerical environment. CUDA 12.8 and the PyTorch build are recorded in TabLLM manifests. The nightly PyTorch wheel may require the original wheel repository.

No complete trustworthy pip/conda lock was identified for every run. Do not merge the principal, extraction, and 4.30 extension environments into one installation. Historical TransTab 5.12 results are retained beside the 4.30 conformance replication.

Finalization follow-up (2026-09-24): repository requirements.txt is unpinned; earlier release requirements explicitly describe unpinned installation dependencies; prior environment.yml specifies Python 3.10 and a requirements include. A requirements-full.txt pins selected packages but is not a complete historical execution lock tied to all reported runs. These declarations were not promoted to recovered full locks. No current-environment freeze was generated. L02 remains PARTIAL.
