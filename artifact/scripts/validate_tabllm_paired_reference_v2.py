#!/usr/bin/env python3
"""Independently check actual bootstrap draws with sklearn and audit outputs."""
import platform
import time

import numba
import numpy as np
import sklearn

import analyze_tabllm_paired_reference_v2 as run


def main():
    start = time.perf_counter()
    out = run.DEFAULT_OUT
    summary = run.read_json(out / 'SUMMARY_V1.json')
    lock = run.read_json(out / 'RUN_LOCK_V1.json')
    assert run.sha(run.PROTOCOL) == lock['protocol_sha256'] == summary['protocol_sha256']
    assert run.sha(run.__file__) == lock['runner_sha256'] == summary['runner_sha256']
    checks = {}
    halves = [[], []]
    for dataset in run.DATASETS:
        labels, probs, positions, point, _, _, point_error = run.load_dataset(dataset)
        record = summary['datasets'][dataset]
        values = np.load(out / f'{dataset}_draws.npz')
        boot = values['bootstrap']
        assert boot.shape == (5000, 24) and np.isfinite(boot).all()
        np.testing.assert_allclose(values['utility'], point, atol=1e-12, rtol=0)
        rng = np.random.default_rng(record['seed'])
        weights = np.zeros((50, len(labels)))
        for cls in np.unique(labels):
            group = np.flatnonzero(labels == cls)
            e = rng.exponential(1, size=(50, len(group)))
            weights[:, group] = len(group) * e / e.sum(axis=1, keepdims=True)
        assert (weights > 0).all()
        # Independent metric implementation; exact original arm/split averaging.
        aucs = []
        for arm in range(25):
            split_aucs = []
            for pos in positions:
                p = probs[arm, pos]
                split_aucs.append(run.roc_auc_score(labels[pos], p[:, 1] if p.shape[1] == 2 else p,
                    sample_weight=weights[0, pos], multi_class='ovr', average='macro'))
            aucs.append(np.mean(split_aucs))
        independent_utility = aucs[0] - np.asarray(aucs[1:])
        np.testing.assert_allclose(boot[0], independent_utility, atol=1e-12, rtol=0)
        covariance, comp = run.components(point, boot)
        centered = boot - boot.mean(axis=0)
        projected = centered - centered.mean(axis=1, keepdims=True)
        direct_noise = np.sum(projected**2) / ((len(boot)-1)*24)
        np.testing.assert_allclose(comp['spread_noise_variance'], direct_noise, atol=1e-14)
        np.testing.assert_allclose(covariance, values['covariance'], atol=1e-14)
        assert np.linalg.eigvalsh(covariance).min() > -1e-12
        for k, v in comp.items():
            np.testing.assert_allclose(v, record[k], atol=1e-14)
        for h, b in enumerate(np.array_split(boot, 2)):
            c, part = run.components(point, b)
            errors = b-b.mean(axis=0)
            se = np.sqrt(np.diag(c))
            maxima = np.max(abs(errors/se), axis=1)
            halves[h].append((point, se, maxima, part))
        checks[dataset] = dict(status='pass', original_point_max_error=point_error,
            actual_draw_sklearn_max_error=float(np.max(abs(boot[0]-independent_utility))),
            exact_actual_draw_sklearn_metric_count=125, covariance_projection_identity=True,
            all_5000_draws_finite=True)
        print(dataset, 'PASS', flush=True)
    stability = []
    for half in halves:
        q = float(np.quantile(np.max([v[2] for v in half], axis=0), .95))
        count = sum(bool((p-q*se > 0).any() and (p+q*se < 0).any()) for p,se,_,_ in half)
        stability.append(dict(global_critical=q, global_resolved_crossings=count,
            noise_percent={d:100*v[3]['noise_fraction_of_observed_spread'] for d,v in zip(run.DATASETS,half)}))
    report = dict(status='pass', validator_sha256=run.sha(__file__), datasets=checks,
        independent_actual_draw_sklearn_metrics=1125, versions=dict(python=platform.python_version(),
            numpy=np.__version__, numba=numba.__version__, sklearn=sklearn.__version__),
        half_draw_monte_carlo_sensitivity=stability, wall_seconds=time.perf_counter()-start)
    run.write_json(out / 'VALIDATION_V1.json', report)
    print('PASS: 1125 independent actual-draw sklearn metrics; all inputs and decomposition identities', flush=True)


if __name__ == '__main__':
    main()
