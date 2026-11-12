"""Value of adaptivity and of noise: one-batch optimum with NOISELESS readings (s=1, f=0) for a calibrated
agent and for a top-1 believer (eps=1e-3), shipped traps. Compare with bayes_voi_run_noiseless.json
(adaptive, noiseless) and bayes_voi_batch_f0.03.json (one batch, noisy)."""
import sys, json
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import bayes_voi_batch as bb
from bayes_voi_core import *
out = {}
for name, pp in [("calibrated", SHIPPED_TRAP), ("believes top-1 (eps=1e-3)", smooth(TOP1, 1e-3))]:
    r = bb.run(SHIPPED_TRAP, pp, [2, 4, 5, 6, 8], s=1.0, f=0.0, ranks=(1, 2, 3))
    out[name] = r
    print(name, {B: (v["true_value"], [tuple(a.values()) for a in v["alloc"]]) for B, v in r.items()}, flush=True)
json.dump(out, open(__file__.replace(".py", ".json"), "w"), indent=1)
