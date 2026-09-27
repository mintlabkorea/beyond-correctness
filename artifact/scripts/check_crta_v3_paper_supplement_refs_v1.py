"""Cross-check main.tex's hardcoded `Table~A<n>` / `Figure~A<n>` supplement
references against the numbers LaTeX actually assigns in the appendix build.

main.tex must compile standalone without the appendix, so those references
cannot use \\ref.  They therefore go stale silently whenever a float is
inserted into appendix.tex.  Run this after any appendix edit.

Usage: build submission_main_appendix.tex first, then run this script.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "iclr_latex_v3"
AUX = ROOT / "submission_main_appendix.aux"
MAIN = ROOT / "main.tex"


def main() -> int:
    if not AUX.is_file():
        print(f"missing {AUX}; build submission_main_appendix.tex first")
        return 2
    numbers = {m.group(1): m.group(2) for m in
               re.finditer(r"\\newlabel\{([^}]*)\}\{\{([^}]*)\}", AUX.read_text())}

    lines = MAIN.read_text().splitlines()
    # A "% Supplement source: lab1; lab2." comment declares what the nearest
    # preceding hardcoded reference(s) point at.
    problems = checked = 0
    for i, line in enumerate(lines):
        m = re.search(r"%\s*Supplement source:\s*(.+?)\s*$", line)
        if not m:
            continue
        labels = [x.strip().rstrip(".") for x in re.split(r"[;,]", m.group(1))
                  if x.strip().rstrip(".")]
        window = "\n".join(lines[max(0, i - 12):i + 12])
        cited = set(re.findall(r"(?:Table|Figure)~(A\d+)", window))
        expected = {numbers[lab] for lab in labels
                    if lab in numbers and re.fullmatch(r"A\d+", numbers[lab])}
        if not expected:
            continue
        checked += 1
        missing = expected - cited
        if missing:
            problems += 1
            print(f"main.tex:{i}: cites {sorted(cited) or '[]'} but "
                  f"{sorted(labels)} resolve to {sorted(expected)}")
    print(f"supplement-reference check: {checked - problems}/{checked} sites ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
