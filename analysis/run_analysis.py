#!/usr/bin/env python3
"""Reproduce elementary diagnostics. This is not a growing-agent benchmark."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]


def estimate(values):
    x = np.asarray(values, dtype=float)
    sem = float(x.std(ddof=1) / np.sqrt(len(x)))
    radius = float(student_t.ppf(0.975, len(x) - 1) * sem)
    mean = float(x.mean())
    return {'mean': mean, 'ci95': [mean-radius, mean+radius], 'seed_values': x.tolist()}


def cosine(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def causal_predictions(actions, observations, hazard):
    """Prediction t uses known action t and completed outcome t-1 only."""
    a, y = np.asarray(actions), np.asarray(observations)
    prediction = np.zeros(len(a), dtype=float)
    prediction[1:] = (1 - 2 * hazard) * (y[:-1] / a[:-1]) * a[1:]
    return prediction


def timing_experiment(seed_count=64, steps=20000):
    rows = []
    for hazard in (0.05, 0.5):
        metrics = {k: [] for k in ('constant_zero', 'causal_mixture', 'last_expert',
                                  'outcome_selected_invalid', 'conflict_rate')}
        for seed in range(seed_count):
            rng = np.random.default_rng(20260907 + seed)
            flips = rng.random(steps) < hazard
            z = np.cumprod(np.where(flips, -1, 1))
            a = rng.choice([-1.0, 1.0], size=steps)
            y = z * a
            p = causal_predictions(a, y, hazard)
            hard = np.r_[0.0, (y[:-1] / a[:-1]) * a[1:]]
            # This retrospective selector sees y_t. Deliberately invalid for prediction.
            candidates = np.stack([-a, a])
            selected = np.argmin((candidates-y)**2, axis=0)
            invalid = candidates[selected, np.arange(steps)]
            metrics['constant_zero'].append(float(np.mean(y[1:]**2)))
            metrics['causal_mixture'].append(float(np.mean((p[1:]-y[1:])**2)))
            metrics['last_expert'].append(float(np.mean((hard[1:]-y[1:])**2)))
            metrics['outcome_selected_invalid'].append(float(np.mean((invalid[1:]-y[1:])**2)))
            # At theta=0, the gradient of 0.5*(theta*a-y)^2 is -a*y=-z.
            metrics['conflict_rate'].append(float(np.mean(z[1:] != z[:-1])))
        rows.append({'hazard': hazard, 'n_seeds': seed_count, 'steps_per_seed': steps,
                     'scored_steps': steps-1,
                     'metrics': {k: estimate(v) for k, v in metrics.items()},
                     'exact_expected_mse': {'constant_zero': 1.0,
                                            'causal_mixture': 4*hazard*(1-hazard),
                                            'last_expert': 4*hazard,
                                            'outcome_selected_invalid': 0.0},
                     'exact_expected_conflict_rate': hazard})
    return rows


def make_figures(receipt):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'savefig.bbox': 'tight'})
    out = ROOT/'figures'
    out.mkdir(exist_ok=True)
    cross = receipt['cross_write']
    C = np.asarray(cross['shared_matrix']) * 1e6
    fig, axes = plt.subplots(1, 2, figsize=(8.7, 3.0), gridspec_kw={'width_ratios': [1, 1.55]})
    ax = axes[0]
    im = ax.imshow(C, cmap='RdBu', vmin=-5, vmax=5)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f'{C[i,j]:+.3f}', ha='center', va='center', color='white', fontsize=12)
    ax.set(xticks=[0, 1], xticklabels=['Write 0', 'Write 1'], yticks=[0, 1],
           yticklabels=['Cue 0', 'Cue 1'], title='A. Measured margin change (x 1e-6)')
    ax.tick_params(length=0)
    ax = axes[1]
    angle = np.linspace(0, 180, 361)
    ax.plot(angle, np.cos(np.deg2rad(angle/2)), color='#1b5c73', lw=2)
    ax.scatter([179.8], [math.cos(math.radians(89.9))], color='#bc4b34', zorder=3)
    ax.annotate('179.8 degrees: 0.00175', xy=(179.8, .001745), xytext=(52, .22),
                arrowprops={'arrowstyle': '->', 'color': '#777777'}, fontsize=9)
    ax.set(xlabel='Angle between unit loss gradients (degrees)',
           ylabel='Best common first-order decrease', xlim=(0, 185), ylim=(-.04, 1.05),
           title='B. A separate, elementary gradient calculation')
    fig.tight_layout(w_pad=2.5)
    for ext in ('png', 'pdf'):
        fig.savefig(out/f'interference.{ext}', dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.7, 3.1))
    x = np.arange(2)
    width = .2
    methods = [('constant_zero', 'One mean predictor', '#9ca9ad'),
               ('causal_mixture', 'Causal, known-model mixture', '#1b5c73'),
               ('last_expert', 'Previous-context expert', '#55a6a6'),
               ('outcome_selected_invalid', 'Outcome-selected (invalid)', '#bc4b34')]
    for j, (key, label, color) in enumerate(methods):
        vals = [r['metrics'][key]['mean'] for r in receipt['timing']]
        errors = [r['metrics'][key]['ci95'][1]-r['metrics'][key]['mean'] for r in receipt['timing']]
        ax.bar(x+(j-1.5)*width, vals, width, color=color, label=label, yerr=errors, capsize=3)
    ax.set(xticks=x, xticklabels=['Persistent context (h=0.05)', 'Independent context (h=0.50)'],
           ylabel='Pre-outcome squared prediction error', ylim=(0, 2.5))
    ax.legend(loc='upper left', frameon=False, ncols=2, fontsize=8)
    fig.tight_layout()
    for ext in ('png', 'pdf'):
        fig.savefig(out/f'causal_timing.{ext}', dpi=200)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=64)
    parser.add_argument('--steps', type=int, default=20000)
    args = parser.parse_args()
    cross_path = ROOT/'results/jellobrain_cross_write.json'
    cross = json.loads(cross_path.read_text())
    C = np.array(cross['shared_sheet']['mean_cross_write_matrix'])
    angle = math.degrees(math.acos(np.clip(cosine(C[:, 0], C[:, 1]), -1, 1)))
    g1, g2 = np.array([1., 2.]), np.array([1., -2.])
    D = np.diag([3., 1.])
    receipt = {
        'schema': 'paper/diagnostics-v1',
        'date_utc': '2026-09-07',
        'python': platform.python_version(), 'numpy': np.__version__,
        'description': 'Reproduced upstream write diagnostic and analytic-control simulations; no growing learner is evaluated.',
        'upstream_sha': '0141b091f7efda638feede6e9a4d8b15003e7af6',
        'cross_write_file_sha256': hashlib.sha256(cross_path.read_bytes()).hexdigest(),
        'cross_write': {'n_seeds': cross['n_seeds'], 'shared_matrix': C.tolist(),
                        'shared_margin': cross['shared_sheet']['mean_before_margin'],
                        'separated_margin': cross['separated_bands']['mean_before_margin'],
                        'off_over_diag': cross['shared_sheet']['off_over_diag'],
                        'separated_max_abs_off_diagonal': float(np.max(np.abs(np.asarray(cross['separated_bands']['per_seed_matrices'])[:, [0,1], [1,0]]))),
                        'angle_between_columns_of_mean_matrix_degrees': angle},
        'coordinate_counterexample': {'original_gradients': [g1.tolist(), g2.tolist()],
                                      'coordinate_scale': D.tolist(),
                                      'original_cosine': cosine(g1,g2),
                                      'reparameterized_cosine': cosine(D.T@g1,D.T@g2)},
        'noise_counterexample': {'sample_gradient_cosine': -1.0,
                                 'optimal_single_mean': 0.0, 'optimal_preoutcome_mse': 1.0},
        'relative_responsibility_counterexample': {
            'residuals': [100., 101.], 'gaussian_variance': 1.,
            'best_model_responsibility': float(1/(1+math.exp(-100.5))),
            'best_model_negative_log_likelihood': float(5000+0.5*math.log(2*math.pi))},
        'common_descent': {'angle_degrees': [0,90,179.8,180],
                           'optimal_values': [math.cos(math.radians(x/2)) for x in [0,90,179.8,180]]},
        'timing': timing_experiment(args.seeds, args.steps)}
    (ROOT/'results/diagnostics.json').write_text(json.dumps(receipt, indent=2)+'\n')
    make_figures(receipt)
    compact = {k:v for k,v in receipt.items() if k!='timing'}
    compact['timing'] = [{**r, 'metrics': {k:{x:y for x,y in v.items() if x!='seed_values'} for k,v in r['metrics'].items()}} for r in receipt['timing']]
    print(json.dumps(compact, indent=2))


if __name__ == '__main__':
    main()
