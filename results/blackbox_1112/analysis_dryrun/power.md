# Power of a C1-type contrast (within-item permutation test, two-sided)

Design: 6 items x 4 runs per item and arm (n = 24 per arm). 2000 simulated data sets per row; 2000 permutation resamples per test inside the loop (the analysis itself uses 10000); Monte Carlo standard error of each power at most 0.011.
Generating model: item difficulty u_i ~ Normal(0, sd^2) on the logit scale, shared by both arms; a run succeeds with probability expit(c_arm + u_i); c_arm is set so that the arm's rate averaged over items is the nominal rate. sd = 0 is no between-item heterogeneity.
alpha = 0.05 is the level of a single test (and of the larger p in the Holm family); alpha = 0.025 is the level the smaller p of the two-test Holm family must meet, so the Holm-adjusted power of C1 lies between the two columns.

| gap | rate A | rate B | item sd (logit) | power at alpha 0.05 | power at alpha 0.025 | mean T |
|---|---|---|---|---|---|---|
| 0.35 | 0.85 | 0.50 | 0.0 | 0.669 | 0.555 | +0.354 |
| 0.35 | 0.80 | 0.45 | 0.0 | 0.612 | 0.489 | +0.346 |
| 0.35 | 0.75 | 0.40 | 0.0 | 0.610 | 0.506 | +0.353 |
| 0.35 | 0.85 | 0.50 | 1.0 | 0.725 | 0.616 | +0.352 |
| 0.35 | 0.80 | 0.45 | 1.0 | 0.697 | 0.582 | +0.352 |
| 0.35 | 0.75 | 0.40 | 1.0 | 0.681 | 0.579 | +0.354 |
| 0.45 | 0.90 | 0.45 | 0.0 | 0.898 | 0.836 | +0.447 |
| 0.45 | 0.85 | 0.40 | 0.0 | 0.886 | 0.812 | +0.452 |
| 0.45 | 0.80 | 0.35 | 0.0 | 0.842 | 0.762 | +0.449 |
| 0.45 | 0.90 | 0.45 | 1.0 | 0.922 | 0.874 | +0.451 |
| 0.45 | 0.85 | 0.40 | 1.0 | 0.903 | 0.840 | +0.444 |
| 0.45 | 0.80 | 0.35 | 1.0 | 0.900 | 0.833 | +0.451 |
| 0.00 | 0.60 | 0.60 | 0.0 | 0.026 | 0.009 | -0.001 |
| 0.00 | 0.60 | 0.60 | 1.0 | 0.026 | 0.011 | -0.006 |

| gap | mean power at alpha 0.05 | mean power at alpha 0.025 | plan §5 |
|---|---|---|---|
| 0.45 | 0.892 | 0.826 | about 0.8 |
| 0.35 | 0.666 | 0.554 | about 0.6 |
| 0.00 | 0.026 | 0.010 | size (should be at most alpha) |

Seed 20261112, numpy 2.4.6, bit generator PCG64 (numpy.random.default_rng).
