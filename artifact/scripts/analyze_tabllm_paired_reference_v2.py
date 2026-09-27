#!/usr/bin/env python3
"""Exact paired positive-weight row bootstrap for Figure 1; CPU only, fixed reference library."""
from __future__ import annotations

import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ.setdefault('NUMBA_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')

import argparse
import csv
import gzip
import hashlib
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from numba import njit
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ('bank', 'blood', 'calhousing', 'car', 'creditg', 'diabetes', 'heart', 'income', 'jungle')
SEEDS = (42, 1024, 0, 1, 32)
PROTOCOL = ROOT / 'iclr_latex_v3/TABLLM_PAIRED_REFERENCE_DECOMPOSITION_V2.md'
DEFAULT_OUT = ROOT / 'experiments/tabllm_paired_reference_decomposition_v2'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + '\n')


def write_csv(path, rows):
    with Path(path).open('w') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def prepare_scores(labels, probs, positions):
    """Sort once per arm/split/OVR class; preserve exact score ties."""
    n_arms, _, n_classes = probs.shape
    classes = [1] if n_classes == 2 else list(range(n_classes))
    indices, positive, starts, lengths, arms = [], [], [], [], []
    for arm in range(n_arms):
        for pos in positions:
            for cls in classes:
                order = np.argsort(probs[arm, pos, cls], kind='stable')
                idx = pos[order]
                scores = probs[arm, idx, cls]
                indices.extend(idx.tolist())
                positive.extend((labels[idx] == cls).tolist())
                starts.extend(np.r_[True, scores[1:] != scores[:-1]].tolist())
                lengths.append(len(idx))
                arms.append(arm)
    offsets = np.r_[0, np.cumsum(lengths)].astype(np.int64)
    return (np.asarray(indices, dtype=np.int64), np.asarray(positive, dtype=np.bool_),
            np.asarray(starts, dtype=np.bool_), offsets, np.asarray(arms, dtype=np.int64),
            n_arms, len(positions) * len(classes))


@njit(cache=True)
def weighted_aucs(weights, indices, positive, starts, offsets, arms, n_arms, divisor):
    out = np.zeros((len(weights), n_arms))
    for b in range(len(weights)):
        for cell in range(len(arms)):
            total_pos = 0.0
            total_neg = 0.0
            group_pos = 0.0
            group_neg = 0.0
            numerator = 0.0
            for j in range(offsets[cell], offsets[cell + 1]):
                if starts[j]:
                    numerator += group_pos * (total_neg + .5 * group_neg)
                    total_neg += group_neg
                    total_pos += group_pos
                    group_pos = 0.0
                    group_neg = 0.0
                w = weights[b, indices[j]]
                if positive[j]:
                    group_pos += w
                else:
                    group_neg += w
            numerator += group_pos * (total_neg + .5 * group_neg)
            total_neg += group_neg
            total_pos += group_pos
            if total_pos == 0 or total_neg == 0:
                raise ValueError('Bootstrap draw has an absent OVR class; no redraw allowed')
            out[b, arms[cell]] += numerator / (total_pos * total_neg) / divisor
    return out


def components(point, draws):
    covariance = np.cov(draws, rowvar=False, ddof=1)
    within = float(np.trace(covariance) / len(point))
    common = float(covariance.mean())
    noise = within - common
    observed = float(np.var(point))
    corrected = observed - noise
    return covariance, dict(observed_variance=observed, within_variance=within,
        common_shift_variance=common, spread_noise_variance=noise,
        corrected_reference_variance_raw=corrected,
        observed_sd=float(np.sqrt(observed)), within_se_rms=float(np.sqrt(within)),
        corrected_reference_sd=float(np.sqrt(max(0, corrected))),
        reference_sd_to_within_se=float(np.sqrt(max(0, corrected) / within)) if within > 0 else None,
        noise_fraction_of_observed_spread=noise / observed if observed > 0 else None)


def self_test():
    rng = np.random.default_rng(144)
    for classes in (2, 4):
        labels = np.tile(np.arange(classes), 20)
        raw = rng.integers(1, 5, size=(3, len(labels), classes)).astype(float)
        probs = raw / raw.sum(axis=2, keepdims=True)
        positions = [np.arange(len(labels)), np.arange(0, len(labels) - classes)]
        weights = rng.exponential(1.0, size=(7, len(labels)))
        weights[0] = rng.integers(1, 5, size=len(labels))
        actual = weighted_aucs(weights, *prepare_scores(labels, probs, positions))
        expected = np.zeros_like(actual)
        for b, w in enumerate(weights):
            for arm in range(3):
                for pos in positions:
                    p = probs[arm, pos]
                    expected[b, arm] += roc_auc_score(labels[pos], p[:, 1] if classes == 2 else p,
                        sample_weight=w[pos], multi_class='ovr', average='macro') / len(positions)
        np.testing.assert_allclose(actual, expected, atol=1e-14, rtol=0)
        if classes == 2:
            duplicated = np.repeat(np.arange(len(labels)), weights[0].astype(int))
            duplicate_auc = roc_auc_score(labels[duplicated], probs[0, duplicated, 1])
            single = weighted_aucs(weights[:1], *prepare_scores(labels, probs, [positions[0]]))
            np.testing.assert_allclose(single[0, 0], duplicate_auc, atol=1e-14)
    point = np.linspace(-.1, .1, 24)
    common = rng.normal(size=(5000, 1))
    _, result = components(point, point + common)
    assert abs(result['spread_noise_variance']) < 1e-12
    _, result = components(point, point + rng.normal(size=(5000, 24)))
    assert .9 < result['spread_noise_variance'] < 1.02
    assert result['corrected_reference_variance_raw'] < 0
    assert result['corrected_reference_sd'] == 0
    print('PASS: weighted binary/multiclass AUROC, ties, integer duplication, common-noise cancellation, negative correction', flush=True)


def load_dataset(dataset):
    evidence = ROOT / 'experiments/tabllm_reference_space_v1'
    old = read_json(evidence / 'summary_v1/SUMMARY_V1.json')
    artifact = read_json(evidence / 'summary_v1/ARTIFACT_MANIFEST_V1.json')['files']
    manifest_path = evidence / 'REFERENCE_MANIFEST_V1.json'
    manifest = read_json(manifest_path)
    splits_path = ROOT / 'experiments/tabllm_retrospective_split_manifest_v1.json'
    splits = read_json(splits_path)['datasets'][dataset]['test_row_ids']
    paths = [ROOT / 'experiments/tabllm_retrospective_audit_v1/list_template' / dataset]
    paths += [evidence / 'evidence_v1' / f'ref_{r:02d}' / dataset for r in range(24)]
    all_probs, metrics, inputs = [], [], {str(manifest_path.relative_to(ROOT)): sha(manifest_path),
        str(splits_path.relative_to(ROOT)): sha(splits_path)}
    row_ids = labels = None
    for arm, path in enumerate(paths):
        mp, pp = path / 'metrics.json', path / 'predictions.jsonl.gz'
        metric = read_json(mp)
        assert metric['dataset'] == dataset
        assert sha(pp) == metric['predictions_sha256'], str(pp)
        if arm:
            ref = f'ref_{arm-1:02d}'
            for f in (mp, pp):
                assert sha(f) == artifact[f'{ref}/{dataset}/{f.name}']
            assert metric['reference_manifest_sha256'] == sha(manifest_path)
            assert metric['reference_id'] == ref
            assert metric['template_sha256'] == manifest['datasets'][dataset]['candidates'][ref]['template_sha256']
        for f in (mp, pp):
            inputs[str(f.relative_to(ROOT))] = sha(f)
        with gzip.open(pp, 'rt') as handle:
            records = [json.loads(line) for line in handle]
        ids = np.asarray([r['row_id'] for r in records], dtype=np.int64)
        y = np.asarray([r['label'] for r in records], dtype=np.int64)
        assert len(set(ids)) == len(ids)
        assert all(r['dataset'] == dataset for r in records)
        if arm:
            assert all(r['reference_id'] == ref for r in records)
        order = np.argsort(ids)
        ids, y = ids[order], y[order]
        prob = np.asarray([r['class_probabilities'] for r in records], dtype=float)[order]
        assert np.isfinite(prob).all() and (prob >= 0).all() and (prob <= 1).all()
        np.testing.assert_allclose(prob.sum(axis=1), 1, atol=1e-6)
        if row_ids is None:
            row_ids, labels = ids, y
        else:
            np.testing.assert_array_equal(ids, row_ids)
            np.testing.assert_array_equal(y, labels)
        all_probs.append(prob)
        metrics.append(metric)
    union = sorted(set().union(*(set(v) for v in splits.values())))
    np.testing.assert_array_equal(row_ids, union)
    positions = []
    split_utilities = []
    max_error = 0.0
    for seed in SEEDS:
        members = np.asarray(splits[str(seed)], dtype=np.int64)
        digest = hashlib.sha256(members.tobytes()).hexdigest()
        assert digest == manifest['datasets'][dataset]['test_row_ids_sha256'][str(seed)]
        pos = np.searchsorted(row_ids, members)
        positions.append(pos)
        aucs = []
        for prob, metric in zip(all_probs, metrics):
            assert metric['metrics'][str(seed)]['test_row_ids_sha256'] == digest
            auc = roc_auc_score(labels[pos], prob[pos, 1] if prob.shape[1] == 2 else prob[pos],
                                multi_class='ovr', average='macro')
            error = abs(auc - metric['metrics'][str(seed)]['auc'])
            max_error = max(max_error, error)
            assert error <= 1e-12
            aucs.append(auc)
        split_utilities.append(np.asarray(aucs)[0] - np.asarray(aucs)[1:])
    point = np.mean(split_utilities, axis=0)
    with (evidence / 'summary_v1/reference_utilities.csv').open() as handle:
        old_rows = sorted([r for r in csv.DictReader(handle) if r['dataset'] == dataset], key=lambda x: x['reference_id'])
    np.testing.assert_allclose(point, [float(r['utility']) for r in old_rows], rtol=0, atol=1e-12)
    assert len(old_rows) == 24 and old['reference_count'] == 24
    return labels, np.asarray(all_probs), positions, point, np.asarray(split_utilities), inputs, max_error


def run_dataset(task):
    dataset, out_dir, draws = task
    start = time.perf_counter()
    out_dir = Path(out_dir)
    labels, probs, positions, point, split_utilities, inputs, error = load_dataset(dataset)
    prepared = prepare_scores(labels, probs, positions)
    ones = weighted_aucs(np.ones((1, len(labels)), dtype=np.int64), *prepared)[0]
    np.testing.assert_allclose(ones[0] - ones[1:], point, rtol=0, atol=1e-12)
    seed = int.from_bytes(hashlib.sha256(f'tabllm-paired-reference-v2/{dataset}'.encode()).digest()[:8], 'little')
    rng = np.random.default_rng(seed)
    groups = [np.flatnonzero(labels == cls) for cls in np.unique(labels)]
    boot = np.empty((draws, 24))
    for offset in range(0, draws, 50):
        n = min(50, draws - offset)
        weights = np.zeros((n, len(labels)), dtype=np.float64)
        for group in groups:
            exp_weights = rng.exponential(1.0, size=(n, len(group)))
            assert (exp_weights > 0).all()
            weights[:, group] = exp_weights * (len(group) / exp_weights.sum(axis=1, keepdims=True))
        aucs = weighted_aucs(weights, *prepared)
        boot[offset:offset+n] = aucs[:, :1] - aucs[:, 1:]
        if offset == 0:
            print(f'{dataset}: validated; n_union={len(labels)}; first batch done in {time.perf_counter()-start:.1f}s', flush=True)
    covariance, result = components(point, boot)
    centered = boot - boot.mean(axis=0)
    null_spread = centered.var(axis=1)
    p = (1 + np.count_nonzero(null_spread >= result['observed_variance'])) / (draws + 1)
    se = np.sqrt(np.diag(covariance))
    assert (se > 0).all()
    maxima = np.max(np.abs(centered / se), axis=1)
    q = float(np.quantile(maxima, .95))
    lo, hi = point - q * se, point + q * se
    result.update(dataset=dataset, n_unique_rows=len(labels), n_split_occurrences=sum(map(len, positions)),
        draw_count=draws, seed=seed, min_utility=float(point.min()), max_utility=float(point.max()),
        observed_range=float(np.ptp(point)), point_sign_crossing=bool(point.min() < 0 < point.max()),
        bootstrap_sign_crossing_frequency=float(np.mean((boot.min(axis=1)<0) & (boot.max(axis=1)>0))),
        within_dataset_max_t_critical=q,
        resolved_crossing_within_dataset=bool((lo > 0).any() and (hi < 0).any()),
        heterogeneity_centered_bootstrap_p=float(p), heterogeneity_bonferroni_9_p=float(min(1, 9*p)),
        max_original_auc_error=error, wall_seconds=time.perf_counter()-start,
        split_utility_sd_rms=float(np.sqrt(np.var(split_utilities, axis=0, ddof=1).mean())))
    np.savez_compressed(out_dir / f'{dataset}_draws.npz', utility=point, bootstrap=boot,
        covariance=covariance, split_utilities=split_utilities, max_t=maxima)
    write_json(out_dir / f'{dataset}.json', result)
    write_json(out_dir / f'{dataset}_inputs.json', inputs)
    print(f'{dataset}: complete in {result["wall_seconds"]:.1f}s', flush=True)
    return result


def summarize(out_dir, records, start):
    loaded = [np.load(out_dir / f'{d}_draws.npz') for d in DATASETS]
    global_q = float(np.quantile(np.max([v['max_t'] for v in loaded], axis=0), .95))
    interval_rows = []
    for record, values in zip(records, loaded):
        point, boot = values['utility'], values['bootstrap']
        se = np.sqrt(np.diag(values['covariance']))
        plo, phi = np.quantile(boot, [.025, .975], axis=0)
        glo, ghi = point - global_q * se, point + global_q * se
        q = record['within_dataset_max_t_critical']
        record['resolved_crossing_global_216'] = bool((glo > 0).any() and (ghi < 0).any())
        record['positive_refs_global_216'] = int(np.sum(glo > 0))
        record['negative_refs_global_216'] = int(np.sum(ghi < 0))
        record['resolved_crossing_pointwise'] = bool((plo > 0).any() and (phi < 0).any())
        for r in range(24):
            interval_rows.append(dict(dataset=record['dataset'], reference_id=f'ref_{r:02d}',
                utility=point[r], bootstrap_se=se[r], percentile_lower=plo[r], percentile_upper=phi[r],
                simultaneous_24_lower=point[r]-q*se[r], simultaneous_24_upper=point[r]+q*se[r],
                simultaneous_216_lower=glo[r], simultaneous_216_upper=ghi[r]))
    summary = dict(analysis_status='complete_post_result_paired_reference_decomposition',
        protocol_sha256=sha(PROTOCOL), runner_sha256=sha(__file__), dataset_count=9, reference_count=24,
        draw_count=records[0]['draw_count'], gpu_used=False, bootstrap_unit='unique evaluation row, class-stratified exponential weights; shared across arms and overlapping splits',
        global_max_t_critical=global_q, point_crossing_count=sum(r['point_sign_crossing'] for r in records),
        pointwise_resolved_crossing_count=sum(r['resolved_crossing_pointwise'] for r in records),
        simultaneous_24_resolved_crossing_count=sum(r['resolved_crossing_within_dataset'] for r in records),
        simultaneous_216_resolved_crossing_count=sum(r['resolved_crossing_global_216'] for r in records),
        heterogeneity_bonferroni_9_count=sum(r['heterogeneity_bonferroni_9_p'] < .05 for r in records),
        wall_seconds=time.perf_counter()-start, datasets={r['dataset']:r for r in records},
        limitations=['Fixed released model and reference library; no retraining uncertainty.',
            'Fixed nine-dataset panel; no population-of-datasets inference.',
            'Bootstrap moment correction and centered-bootstrap tests are approximate.',
            'Corrected SD ratios and noise fractions are point summaries without confidence intervals.',
            'Observed ranges are descriptive, not confidence intervals.'])
    write_csv(out_dir / 'decomposition.csv', records)
    write_csv(out_dir / 'utility_intervals.csv', interval_rows)
    write_json(out_dir / 'SUMMARY_V1.json', summary)
    inputs = {}
    for dataset in DATASETS:
        inputs.update(read_json(out_dir / f'{dataset}_inputs.json'))
    write_json(out_dir / 'INPUT_MANIFEST_V1.json', inputs)
    report = ['# W3 paired reference decomposition', '',
        f'Original point ranges cross zero in {summary["point_crossing_count"]}/9 datasets. Resolved sign crossings: '
        f'{summary["pointwise_resolved_crossing_count"]}/9 with pointwise percentile intervals; '
        f'{summary["simultaneous_24_resolved_crossing_count"]}/9 with simultaneous 24-reference bands; '
        f'{summary["simultaneous_216_resolved_crossing_count"]}/9 with simultaneous 216-utility bands.', '',
        f'Reference heterogeneity survives Bonferroni adjustment over nine datasets in {summary["heterogeneity_bonferroni_9_count"]}/9.', '',
        '| Dataset | Observed SD | Corrected ref SD | Evaluation SE (RMS) | SD ratio | Spread noise % | Resolved crossing (24 / 216) | Heterogeneity adjusted p |',
        '|---|---:|---:|---:|---:|---:|---|---:|']
    for r in records:
        report.append(f'| {r["dataset"]} | {r["observed_sd"]:.5f} | {r["corrected_reference_sd"]:.5f} | '
            f'{r["within_se_rms"]:.5f} | {r["reference_sd_to_within_se"]:.2f} | '
            f'{100*r["noise_fraction_of_observed_spread"]:.2f} | {r["resolved_crossing_within_dataset"]} / '
            f'{r["resolved_crossing_global_216"]} | {r["heterogeneity_bonferroni_9_p"]:.5f} |')
    report += ['', 'SD ratio compares corrected finite-library reference SD with RMS within-reference utility SE. '
        'Spread noise % uses the covariance projected across references, not the full within-reference variance. '
        'All variance/ratio summaries are point estimates.', '',
        'The simultaneous bands protect reference selection when asserting opposite utility signs. '
        'Unequal reference utilities and resolved opposite signs are different claims.', '',
        'The 5,000 paired exponential-weight draws preserve overlapping-row and shared-intended-score dependence. '
        'Class-stratified positive-weight union resampling conditions on the released checkpoint and evaluation memberships. '
        'It does not assess training randomness. The centered-bootstrap heterogeneity p-values are approximate, '
        'with minimum Monte Carlo p = 1/5001. No reference or dataset was dropped. '
        'The v1 multinomial bootstrap stopped on an absent Car class; v2 uses normalized exponential weights for all nine datasets.', '',
        f'Protocol SHA256: `{sha(PROTOCOL)}`. Runner SHA256: `{sha(__file__)}`.', '',
        'Methodological background: correlated AUROC estimates require covariance-aware comparison '
        '([DeLong et al., 1988](https://pubmed.ncbi.nlm.nih.gov/3203132/)); this analysis uses exact paired '
        'resampling rather than fitting a random-effects reference population.', '',
        f'Elapsed analysis time: {summary["wall_seconds"]:.1f} seconds; GPU use: none.']
    (out_dir / 'RESULTS_V1.md').write_text('\n'.join(report)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('datasets','limitations')}, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-root', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--draws', type=int, default=5000)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--pilot', action='store_true', help='inadmissible timing run, first dataset only')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.draws != 5000 and not args.pilot:
        parser.error('Evidence requires the frozen 5000 draws')
    if args.out_root.exists():
        parser.error('Output directory exists; preserve prior evidence')
    args.out_root.mkdir(parents=True)
    start = time.perf_counter()
    write_json(args.out_root / 'RUN_LOCK_V1.json', dict(protocol_sha256=sha(PROTOCOL),
        runner_sha256=sha(__file__), draws=args.draws, pilot=args.pilot, gpu_used=False,
        started_utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        numpy_version=np.__version__, workers=args.workers))
    datasets = DATASETS[:1] if args.pilot else DATASETS
    tasks = [(d, str(args.out_root), args.draws) for d in datasets]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(run_dataset, tasks))
    if not args.pilot:
        summarize(args.out_root, records, start)


if __name__ == '__main__':
    main()
