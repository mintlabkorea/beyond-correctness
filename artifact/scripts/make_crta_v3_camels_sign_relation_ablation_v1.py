#!/usr/bin/env python3
"""Generate the GC-REL per-relation ablation runner from the frozen v2 runner.

The ablation must not silently re-implement v2's loaders, split, estimator or
metrics -- the whole point is that only the arm set differs.  This generator
performs four asserted substitutions on the v2 source and writes the result,
so the diff between the two files is exactly the arm set plus provenance.
Re-running it must reproduce the runner byte-for-byte.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/run_crta_v3_camels_sign_probe_v2.py"
TARGET = ROOT / "scripts/run_crta_v3_camels_sign_relation_ablation_v1.py"

NEW_DOC = '''"""GC-REL: per-relation ablation of the CAMELS sign prior (addendum GC-REL).

Derived from `run_crta_v3_camels_sign_probe_v2.py` by a single scripted
substitution (`scripts/make_crta_v3_camels_sign_relation_ablation_v1.py`);
loaders, split, robust channels, estimator, seeds, support levels and
metrics are byte-identical to v2.  Only the arm set changes: v2 flips
BOTH declared relations at once, so its +0.184 identification effect is
an undecomposed sum over precipitation -> discharge (+) and
PET -> discharge (-).  This runner flips one relation at a time.

Design and predictions:
`iclr_latex_v3/SCHEMA_PAIR_GENERALIZATION_PREREGISTRATION_V1.md` (section 9,
addendum GC-REL).
"""'''

OLD_ARMS = 'ARMS = ("free", "sign_documented", "sign_flipped", "sign_random")'
NEW_ARMS = ('ARMS = ("sign_documented", "flip_precip_only", "flip_pet_only",\n'
            '        "sign_flipped")')

OLD_BLOCK = '''            rng = derived_rng(f"camels_sign_v1|{n_support}|{seed}")
            signs_random_raw = [0] * len(base_features)
            for k in rng.choice(len(base_features), size=n_constrained,
                                replace=False):
                signs_random_raw[int(k)] = int(rng.choice([-1, 1]))
            arm_constraints = {
                "free": None,
                "sign_documented": expand(signs_doc_raw),
                "sign_flipped": expand([-s for s in signs_doc_raw]),
                "sign_random": expand(signs_random_raw),
            }'''

NEW_BLOCK = '''            def flip_family(signs: list[int], family: int) -> list[int]:
                """Negate only the entries whose documented sign is `family`.

                +1 selects the precipitation relation, -1 the PET relation;
                every other feature keeps its documented (0) constraint.
                """
                return [-s if s == family else s for s in signs]

            arm_constraints = {
                "sign_documented": expand(signs_doc_raw),
                "flip_precip_only": expand(flip_family(signs_doc_raw, 1)),
                "flip_pet_only": expand(flip_family(signs_doc_raw, -1)),
                "sign_flipped": expand([-s for s in signs_doc_raw]),
            }'''

OLD_REC = '"task": "N1_camels_us2gb", "support_basins": n_support,'
NEW_REC = ('"task": "N1_camels_us2gb", "addendum": "GC-REL",\n'
           '                "support_basins": n_support,\n'
           '                "relation_families": {\n'
           '                    "precipitation": [f for f, s in zip(\n'
           '                        base_features, signs_doc_raw) if s == 1],\n'
           '                    "pet": [f for f, s in zip(\n'
           '                        base_features, signs_doc_raw) if s == -1],\n'
           '                },')


def main() -> int:
    src = SOURCE.read_text(encoding="utf-8")
    head = src.index('"""')
    old_doc = src[head:src.index('"""', head + 3) + 3]
    for old, new in ((old_doc, NEW_DOC), (OLD_ARMS, NEW_ARMS),
                     (OLD_BLOCK, NEW_BLOCK), (OLD_REC, NEW_REC)):
        if old not in src:
            raise SystemExit(f"v2 source drifted; anchor not found:\n{old[:80]}")
        src = src.replace(old, new, 1)
    TARGET.write_text(src, encoding="utf-8")
    TARGET.chmod(0o755)
    print(f"wrote {TARGET} ({len(src.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
