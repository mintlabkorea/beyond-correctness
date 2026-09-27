# Beyond Correctness: Evaluating Semantic Knowledge in Cross-Table Transfer

Code and reproducibility artifacts for the paper by **Seokyong Sheem, Hochang Lee, Suyeong Lee, and Daekyum Kim**.

Semantic-content sensitivity and predictive utility answer different questions. This repository provides experiment and analysis code, frozen aggregate results, semantic records, the 24-reference library, and the human audit of 25 comparisons across nine studies.

## Quick start

Python 3 and Make are sufficient for the frozen-result checks. No data download, GPU, API key, or model training is needed.

```sh
git clone https://github.com/mintlabkorea/beyond-correctness.git
cd beyond-correctness
make verify
make scan
make validate
```

The preserved artifact has **1,175 passing numerical and source-record checks**, including final content-sensitivity adjudications for all four explicit claims. See the [validation summary](artifact/FINAL_ARTIFACT_REPORT.md), [quick start](artifact/QUICKSTART.md), and [artifact README](artifact/README.md).

## Repository guide

| Path | Contents |
|---|---|
| [paper/main.tex](paper/main.tex) | Author-supplied arXiv manuscript dated September 27, 2026, with the code-availability link added to the abstract |
| [paper/appendix.inc](paper/appendix.inc) | Appendix included by main.tex |
| [artifact/scripts/](artifact/scripts/) | Experiment, preprocessing, and analysis scripts |
| [artifact/code/](artifact/code/) | Indexes of executable roles |
| [artifact/experiments/](artifact/experiments/) | Frozen aggregate results and configurations |
| [artifact/published_audit/](artifact/published_audit/) | Human coding, source evidence, and final adjudication records |
| [artifact/reproducibility/](artifact/reproducibility/) | Verification, regeneration, and reproduction entry points |
| [artifact/DATA_ACCESS.md](artifact/DATA_ACCESS.md) | Data access, provenance, and redistribution boundaries |

The `artifact/` directory preserves the September 24 reproducibility release byte for byte, including its anonymous author labels, archived manuscript, and checksum files. Its verification commands check that frozen manuscript and evidence. The current public manuscript is in `paper/`; it incorporates the author's subsequent writing and figure revisions. This separation preserves the original verification record without presenting the earlier manuscript as the current preprint.

## Reproduction and manuscript build

```sh
make tables             # regenerate tables from frozen inputs
make figures            # regenerate figures from frozen inputs
make reproduce-public   # check public-input requirements and show runner commands
make reproduce-full     # check requirements for authorized restricted-data reruns
make paper              # compile paper/main.tex into .build/paper/main.pdf
```

Table and figure generation require the dependencies documented in [artifact/reproducibility/environments/README.md](artifact/reproducibility/environments/README.md). The manuscript build uses `latexmk`, pdfLaTeX and BibTeX. `make reproduce-public` and `make reproduce-full` report prerequisites; they do not automatically launch training.

Frozen-result verification passes. **Full historical reconstruction remains PARTIAL** because the exact restricted clinical preparation chain, complete historical environment locks, and historical NHANES builder revision are not all recoverable. See [MISSING_ARTIFACTS.md](artifact/MISSING_ARTIFACTS.md) and [ARTIFACT_STATUS.md](artifact/ARTIFACT_STATUS.md). Restricted participant data, person-level predictions, and model weights are not distributed.

## Citation and terms

Please cite the paper by its title and authors above. An arXiv identifier will be added once available. Code is publicly accessible under the existing [license notice](LICENSE); third-party code and data remain subject to their original terms. This repository does not grant access or redistribution rights to cohort datasets.
