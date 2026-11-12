"""E3: allocation by proxy rank, rank-prefix testing, one-burst, and 'adaptive width' (rank 2 isolated when it is
vs is not the true cue). Inputs: followup/failure_modes/failure_modes.json (A, G), failure_modes_mech.json (P2),
followup/failure_modes_heldout/failure_modes_heldout.json. With instrument = main study + Open-8 (NOV)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from stats_lib import fmt, fisher2
G = '/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/gpu/results/blackbox_1112/followup'
fm = json.load(open(f'{G}/failure_modes/failure_modes.json')); mech = json.load(open(f'{G}/failure_modes/failure_modes_mech.json'))
fr = lambda s: tuple(map(int, s.split('/')))
A = fm['A_allocation_by_proxy_rank']; out = ['## Rank-2 isolation: probes where rank 2 is the true cue (traps) vs probes where rank 1 is (with instrument, NOV)']
tot = [0, 0, 0, 0]
for ag in ['gpt', 'opus', 'sonnet', 'haiku', 'all']:
    a = A[f'with instrument|{ag}']; r2k, n = fr(a['rank 2']); tk, tn = fr(a['true cue at rank 2'])
    r1k, r1n = fr(a['true cue at rank 1'])
    ok, on = r2k - tk, n - tn
    out.append(f"- {ag}: rank 2 isolated when it is the true cue {fmt(tk, tn)}; when rank 1 is the true cue {fmt(ok, on)}; ratio {((tk/tn)/(ok/on)) if ok else float('inf'):.1f}x; "
               f"Fisher p = {fisher2(tk, tn-tk, ok, on-ok):.2g}; rank 1 isolated when it is the true cue {a['true cue at rank 1']}; rank 3 {a['rank 3']}; rank 4+ {a['rank 4+']}; median candidates tested per probe {a['candidates tested per probe, median']}")
out.append("  (the 'rank 1 is the true cue' set includes two-part hard probes, where rank 2 is often the parent; ordinary-only figure from rebuttal §1 over 124 runs incl. 11 [OCT]: GPT 5/88, Claude 6/151)")
for ag in ['gpt', 'haiku', 'all']:
    a = A[f'no instrument|{ag}']
    out.append(f"- no instrument {ag}: rank1 {a['rank 1']}, rank2 {a['rank 2']}, rank3 {a['rank 3']}, rank4+ {a['rank 4+']}, true cue at rank 2 tested {a['true cue at rank 2']}, median candidates/probe {a['candidates tested per probe, median']}")
out.append('## Rank-prefix testing (P2): tested set == proxy top-k')
for k, v in mech['P2_rank_prefix'].items():
    out.append(f"- {k}: {v['rank_prefix_observed']}/{v['slots']} = {v['rank_prefix_observed']/v['slots']:.2f} vs {v['expected_if_rank_blind']:.1f} expected rank-blind ({v['rank_prefix_observed']/v['expected_if_rank_blind']:.1f}x)")
out.append('## One-burst querying (G): all exact queries within 60 s')
for k, v in fm['G_one_burst'].items(): out.append(f'- {k}: {v}')
gk = [fr(fm['G_one_burst'][k]) for k in ['main|gpt', 'open8|gpt']]; bk = fr(fm['G_one_burst']['bb8|gpt'])
out.append(f"- GPT with instrument {sum(a for a,_ in gk)}/{sum(b for _,b in gk)} vs GPT BB-8 {bk[0]}/{bk[1]}: Fisher p = {fisher2(sum(a for a,_ in gk), sum(b-a for a,b in gk), bk[0], bk[1]-bk[0]):.2g}")
out.append('## Where the exact texts went (F)')
for k, v in fm['F_where_exact_texts_went'].items(): out.append(f'- {k}: {v}')
try:
    h = json.load(open(f'{G}/failure_modes_heldout/failure_modes_heldout.json'))
    out.append('## Held-out replication keys (failure_modes_heldout.json): ' + ', '.join(list(h.keys())[:30]))
except Exception as e: out.append(f'heldout json: {e}')
open(os.path.join(os.path.dirname(__file__), '12_width.out.md'), 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
