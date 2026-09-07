#!/usr/bin/env python3
"""Independent checks for source integrity, causal timing, and numerical claims."""
import hashlib
import json
import math
from pathlib import Path
import unittest

import numpy as np
from run_analysis import causal_predictions

ROOT = Path(__file__).resolve().parents[1]


class PaperChecks(unittest.TestCase):
    def test_upstream_integrity(self):
        for row in json.loads((ROOT/'sources/manifest.json').read_text())['files']:
            self.assertEqual(hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest(), row['sha256'], row['path'])

    def test_causal_predictions_do_not_use_current_or_future_outcomes(self):
        rng = np.random.default_rng(817)
        a = rng.choice([-1., 1.], size=100)
        y = rng.normal(size=100)
        baseline = causal_predictions(a, y, .05)
        for cut in (0, 1, 17, 99):
            changed = y.copy()
            changed[cut:] = 100 + rng.normal(size=100-cut)
            np.testing.assert_array_equal(causal_predictions(a, changed, .05)[:cut+1], baseline[:cut+1])

    def test_common_descent_bound_against_independent_direction_grid(self):
        # Numerically maximize the lesser decrease, without using the bisector formula.
        directions = np.stack([np.cos(np.linspace(0,2*np.pi,200001)),
                               np.sin(np.linspace(0,2*np.pi,200001))], axis=1)
        for deg in (20., 75., 130., 179.8):
            q1 = np.array([1.,0.])
            q2 = np.array([math.cos(math.radians(deg)), math.sin(math.radians(deg))])
            measured = np.minimum(-directions@q1, -directions@q2).max()
            self.assertAlmostEqual(measured, math.cos(math.radians(deg/2)), delta=2e-5)

    def test_receipts_match_exact_risks(self):
        data = json.loads((ROOT/'results/diagnostics.json').read_text())
        raw = (ROOT/'results/jellobrain_cross_write.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),data['cross_write_file_sha256'])
        for row in data['timing']:
            for key, theory in row['exact_expected_mse'].items():
                # A conservative numerical check, not a claim of exact finite-sample equality.
                self.assertLess(abs(row['metrics'][key]['mean']-theory), .025)
        self.assertEqual(data['cross_write']['separated_max_abs_off_diagonal'], 0.)
        self.assertGreater(data['cross_write']['off_over_diag'], .99)
        self.assertLess(data['cross_write']['off_over_diag'], 1.02)


if __name__ == '__main__':
    unittest.main(verbosity=2)
