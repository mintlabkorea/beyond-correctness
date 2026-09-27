#!/usr/bin/env python3
"""E1: direction-constraint support sweep (the regularization curve).

Thin wrapper over the frozen PAM v1 runner: arms restricted to
{free, sign_documented, pl_sign_flip}; pass
--support-rows 16 32 64 128 256 1024 and a fresh --out-root.
Design and predictions:
`iclr_latex_v3/OVERNIGHT_EXPANSION_PREREGISTRATION_20260820_V1.md` (E1).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    spec = importlib.util.spec_from_file_location(
        "pam_v1_for_sweep",
        ROOT / "scripts/run_crta_v3_pam_constraint_relations_v1.py")
    pam = importlib.util.module_from_spec(spec)
    sys.modules["pam_v1_for_sweep"] = pam
    spec.loader.exec_module(pam)
    pam.ARMS = ("free", "sign_documented", "pl_sign_flip")
    return pam.main()


if __name__ == "__main__":
    raise SystemExit(main())
