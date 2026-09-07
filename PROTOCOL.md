# Prospective growth experiment

Status: specified on 7 September 2026; **not implemented or executed in this paper**. This is a prospective protocol, not a claim of external preregistration. The executable measurements in `results/` belong to the diagnostic study described in the manuscript, not to this protocol.

## Question and primary comparison

Does admitting a new module using subsequent predictive evidence produce a better error/resource trade-off than continuing to adapt one model, or creating modules in response to prediction error alone?

The strongest interpretation would concern a fixed family of small linear experts. A nonlinear or recurrent model can represent the same environmental distinctions without assigning one expert to each generating map. The environment's number of maps is therefore not a universal target module count.

## World and legal observations

Each trial has an unobserved mode `z`, an issued probe `u` in two dimensions, a chosen readout `s` in `{0,1}`, and a scalar consequence:

```
y = (A[z] @ u)[s] + noise
```

Legal probes are `(+/-1,0)`, `(0,+/-1)`, and the four vectors `( +/-1, +/-1 ) / sqrt(2)`. The chosen probe, readout, and observed scalar enter the evidence history. A forecast must be logged before `y` is released. The generator's mode, map arrays, random-generator state, block boundary, future noise, and future outcomes are inaccessible to all learners.

At the beginning of each decision, the learner may buy zero to eight additional probe/readout outcomes before predicting a final scored probe. Those diagnostic probes are recorded and charged. The scored probe is chosen independently by the evaluator from the legal set and revealed before its forecast; its result arrives afterward. This prevents a learner from obtaining a good prediction score only by asking questions it can already answer. An adaptive agent may select its own diagnostic actions but not the evaluator's scored action.

## Environment families

Generate three matrices per world by drawing each entry uniformly from `[-1,1]`, rejecting a draw only if its Frobenius distance from an earlier matrix is less than 0.6. Record rejection counts. Use noise standard deviation 0.05 in the base experiment. Draw block lengths independently and uniformly from 80 to 160 decisions. The unannounced base sequence is `A, B, A, C, B, A`. Mode labels are for scoring only.

Required control families:

1. **Stationary noise:** only A exists; observation noise varies independently. Run standard deviations 0.05, 0.15, and 0.30. Births can model uncertainty, but do not count as recovered new contexts; their forecast value and cost are still scored.
2. **Return of familiar conditions:** the base sequence. Record the evidence needed to recover a previous map's predictive performance.
3. **Smooth drift:** replace abrupt transitions with 60-decision interpolation between matrices. Splitting a continuous path into many experts must earn its resource cost.
4. **Richer single-model control:** one stationary environment uses `y = (A @ u)[s] + 0.5*u[0]*u[1] + noise`. Compare adding a quadratic feature to one predictor with adding experts. All learners get the same permitted feature-expansion option and its charged state.
5. **Noise bursts:** in a stationary A world, insert intervals of high observation noise with unchanged conditional mean. Detecting uncertainty must be distinguished from inferring a new response map.
6. **Module-label permutation:** permute anonymous expert labels and their associated state consistently. Predictions and structural decisions should be unchanged, up to declared random tie-breaking.

This first experiment tests response-map inference; it does not establish attribution between body changes and environmental changes. Such attribution needs a later world with independently identifiable intervention signatures and a matched nonidentifiability control.

## Resource accounting

The proposed primary memory ceiling is 1,024 float64-equivalent scalar slots. Count model parameters, covariance parameters, routing/transition state, optimizer accumulators, retained records, candidate copies, and scratch arrays that persist across calls. Report transient peak storage separately. Integers, Booleans, timestamps, and addresses must also be counted in bytes, not treated as free. Immutable algorithm code and the same fixed legal-action list may be excluded for every method.

A retained event can include decision time, trial time, two action coordinates, readout, outcome, pre-outcome prediction, and model-generation identifier. Eight float64-equivalent slots per event is a conservative accounting convention, not a requirement to store each field as float64. A 64-event reserve would therefore use 512 of the proposed slots. Each model must document its actual layout and remaining budget.

Charge all probe calls, all predictive model evaluations, all candidate update evaluations, and all replay evaluations. Report both these hardware-independent counts and measured wall time. Evaluate fixed-bank and growing-bank alternatives at the same total memory ceiling. A full-history or known-mode model may be displayed only as a separately labeled oracle.

## Learners and causal timing

Implement the following before examining the held-out seeds:

- A single online linear predictor with fixed memory, plus a matched quadratic-feature alternative.
- A fixed bank of small experts with causal responsibility and the same resource ceiling.
- A growing bank whose nomination rule uses persistent poor likelihood.
- A growing bank whose nomination rule also measures harmful updates on scoped replay evidence.
- A compact recurrent predictor with its weights, state, and optimizer charged to the same ceiling.

Both growing banks must use the same candidate initialization, maximum candidate budget, candidate evaluation windows, and prospective admission score. This isolates the incremental value of the conflict nomination rule. Also run a nomination-without-prospective-admission ablation to test whether poor-likelihood or conflict signals alone overgrow on noise.

Keep the decision sequence explicit:

1. Form a prior over existing models using completed evidence.
2. Optionally purchase diagnostic observations; update beliefs and charge the observations.
3. Log the forecast for the scored action before observing its consequence.
4. Release and score that consequence using the logged forecast.
5. Compute posterior responsibility and update models for future decisions.
6. Evaluate eligible structural candidates using only the declared training/audit boundary.

Posterior routing using the scored outcome is an invalid control, never a performance row eligible to win.

## Candidate training and admission

Use a bounded training segment to fit a candidate. Evaluate the candidate and its nonsplitting competitor on a subsequent 32-decision window, scoring each decision before updating on it. The evidence window and all candidate computation count against the resource budget. If the context changes during the window, retain and score that event rather than silently restarting until a favorable segment appears.

At most one new candidate may begin per 64 decisions. Set the candidate fitting budget and a finite grid of complexity penalties on development seeds. Fix them before held-out evaluation. The common structural score is future log predictive advantage minus a penalty for additional persistent state and computation. Record rejected as well as accepted proposals. A rejection is an informative result.

No significance level is asserted for this engineering admission score. Any later probabilistic false-admission guarantee must specify a separate sequential test and account for repeated proposals and adaptive evidence collection.

## Scoring and stopping

Use 20 development world seeds, numbered 0-19, and 100 held-out world seeds, numbered 1000-1099. Save generator versions and parameters before running held-out evaluation. Pair exogenous matrices, noise draws, and block schedules across methods. Count independent worlds, not individual time steps, as the units for confidence intervals.

Primary outcomes are pre-outcome squared error and proper predictive log loss against total paid probe calls and peak memory. Report Pareto curves; do not hide the trade-off in an uncalibrated aggregate score. Secondary outcomes include births, rejections, memory evictions, return-to-context recovery, retained conditional error, and measured collateral effects. Recovery counts from the first observation after a hidden switch, with uncertainty visible; no method is expected to know a silent switch before evidence arrives.

The proposed growth rule has failed to earn an architectural advantage if a matched fixed or single recurrent model dominates it, if gains disappear after charging copies or memory, if noisy single-world controls cause unchecked expansion, or if performance depends on post-outcome routing. A negative result should retain these verdicts rather than changing thresholds on the held-out seeds.

## Later spatial translation

Only after the abstract contract is working should a native spatial medium replace the expert arrays. The same observations, future scoring, and accounting remain in force. The location of learned partition and selector state must be inspectable. A body-only fast-state wipe tests storage in material; it is not the same evaluation as running a complete agent with legitimate context state. Neither test should be substituted for the other.
