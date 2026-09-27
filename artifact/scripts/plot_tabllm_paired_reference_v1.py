#!/usr/bin/env python3
"""Companion to Figure 1: finite-library spread and simultaneous sign evidence."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'experiments/tabllm_paired_reference_decomposition_v2'


def main():
    summary = json.loads((OUT / 'SUMMARY_V1.json').read_text())
    intervals = pd.read_csv(OUT / 'utility_intervals.csv')
    order = ['calhousing', 'creditg', 'heart', 'jungle', 'bank', 'blood', 'car', 'diabetes', 'income']
    names = ['California', 'Credit-g', 'Heart', 'Jungle', 'Bank', 'Blood', 'Car', 'Diabetes', 'Income']
    plt.rcParams.update({'font.size': 9, 'pdf.fonttype': 42, 'ps.fonttype': 42})
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True,
                                    gridspec_kw={'width_ratios': [1, 1.5]})
    y = np.arange(9)
    records = [summary['datasets'][d] for d in order]
    left.scatter([r['observed_sd'] for r in records], y-.16, marker='o', facecolors='none',
                 edgecolors='#525252', label='Observed reference SD', s=35)
    left.scatter([r['corrected_reference_sd'] for r in records], y, marker='o',
                 color='#326E9C', label='Noise-corrected reference SD', s=25)
    left.scatter([r['within_se_rms'] for r in records], y+.16, marker='s',
                 color='#C27331', label='Within-reference evaluation SE', s=25)
    left.set_yticks(y, names)
    left.set_xlabel('AUROC units')
    left.set_xlim(left=0)
    left.set_title('(a) Spread versus evaluation uncertainty', loc='left', fontsize=10)
    left.legend(loc='lower left', bbox_to_anchor=(0, 1.03), frameon=False, fontsize=8)
    right.axvline(0, color='.35', linewidth=1)
    for pos, dataset in enumerate(order):
        rows = intervals[intervals.dataset == dataset]
        right.scatter(rows.utility, np.full(24, pos), color='#8A949D', s=9, alpha=.65)
        for j, idx in enumerate([rows.utility.idxmin(), rows.utility.idxmax()]):
            row = rows.loc[idx]
            yy = pos + (-.16 if j == 0 else .16)
            color = '#326E9C' if j else '#C27331'
            right.plot([row.simultaneous_216_lower, row.simultaneous_216_upper], [yy, yy],
                       color=color, linewidth=1.4)
            right.scatter([row.utility], [yy], s=25, color=color, marker='D')
    right.set_xlabel('Utility (intended AUROC minus reference AUROC)')
    right.set_title('(b) Extreme references: simultaneous 95% bands', loc='left', fontsize=10)
    right.text(0, 1.085, 'Orange: lowest estimate; blue: highest.\nBands simultaneously cover all 216 utilities.',
               transform=right.transAxes, fontsize=8, va='bottom')
    for ax in (left, right):
        ax.set_ylim(8.6, -.6)
        ax.grid(axis='x', alpha=.15)
        ax.spines[['top', 'right']].set_visible(False)
        ax.tick_params(axis='y', length=0)
    fig.text(.01, .012, '5,000 paired row bootstraps; shared rows retain identical positive weights across arms and overlapping splits. '
             'SD corrections are point estimates.', fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, .96), w_pad=3)
    for suffix in ('pdf', 'png'):
        fig.savefig(OUT / f'paired_reference_decomposition.{suffix}', dpi=220, bbox_inches='tight')
    plt.close(fig)
    paths = [OUT/'SUMMARY_V1.json', OUT/'utility_intervals.csv', Path(__file__)]
    provenance = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (OUT/'FIGURE_PROVENANCE_V1.json').write_text(json.dumps(provenance, indent=2)+'\n')


if __name__ == '__main__':
    main()
