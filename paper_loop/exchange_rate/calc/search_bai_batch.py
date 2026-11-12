"""Non-adaptive (one batch) noiseless blind designs: per probe, 3 bit-tests (candidate index bits, 8 candidates
coded 0..7, so a null reads 000 like candidate 0) plus an optional 'all 8' screen. Exactly one probe is null; the
hard probe is uniform among the 3 planted. Answer: Bayes-optimal given readings. NAME success by enumeration."""
import itertools, json
res = {}
for n_screen in range(0, 5):  # number of probes given the extra all-8 screen (4th test)
    B = 12 + n_screen
    tot = 0.0; succ = 0.0
    for null in range(4):
        for cues in itertools.product(range(8), repeat=3):
            for hard_k in range(3):
                planted = [i for i in range(4) if i != null]
                t = {null: None}; t.update({p: c for p, c in zip(planted, cues)})
                hard = planted[hard_k]
                w = 1 / (4 * 512 * 3)
                # readings: code (c bits) or 000 for null; screened probes reveal null exactly
                obs = []
                for i in range(4):
                    code = 0 if t[i] is None else t[i]
                    scr = (t[i] is not None) if i < n_screen else None
                    obs.append((code, scr))
                # posterior over which probe is null, given obs: null must read code 0 and screen False/None
                cand_null = [i for i in range(4) if obs[i][0] == 0 and obs[i][1] in (False, None)]
                if any(obs[i][1] is False for i in range(4)):
                    cand_null = [i for i in range(4) if obs[i][1] is False]
                # each candidate null equally likely a posteriori (prior symmetric, likelihoods equal: 1/8 for cue 0)
                guess_null = cand_null[0]  # any; success prob = 1/len
                # answer: null->none, others -> their decoded code
                ok = (guess_null == null)
                tot += w; succ += w * ok
    res[B] = round(succ / tot, 4)
print(json.dumps(res))
json.dump(res, open("/home/user/shifthunt/paper_loop/exchange_rate/calc/search_bai_batch.json", "w"))
