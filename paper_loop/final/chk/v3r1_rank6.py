"""V3 polish round 1: bank already holds deep traps (exp_c.json, trap/by_pool/knob_trap_s/fixed/top_candidate/
distinct_instances/main_rank_counts = {1: 4, 2: 1, 6: 3}; whole bank {1: 11, 2: 10, 6: 3}; shipped {2: 3})."""
D='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/paperloop/final/'
s=open(D+'PAPER_V3_r1.md').read()
R=[
("Fresh items and a rank-3 trap are the decisive next runs.",
 "Fresh items and deeper traps are the decisive next runs; the bank already holds three trap probes with the [main] at proxy rank 6, not yet run with agents."),
("With the [main] moved to proxy rank 3-8, the top-two policy scores 0.00 and the hedge 0.46-0.56; such an item needs a newly trained two-decoy trap.",
 "With the [main] moved to proxy rank 3-8, the top-two policy scores 0.00 and the hedge 0.46-0.56. The bank already contains such items: of its 24 distinct trap probes, the [main] is at proxy rank 1 on 11, rank 2 on 10 and rank 6 on 3 (one pool; `exp_c.json`), so a deep-trap agent run needs no new training [design]."),
]
for o,n in R:
    assert s.count(o)==1,o[:60]
    s=s.replace(o,n)
open(D+'PAPER_V3_r1.md','w').write(s)
print('ok')
# second pass (length)
s=open(D+'PAPER_V3_r1.md').read()
R=[
("Fresh items and deeper traps are the decisive next runs; the bank already holds three trap probes with the [main] at proxy rank 6, not yet run with agents.",
 "Fresh items and deeper traps (the bank holds three with the [main] at proxy rank 6, never run with agents) are the decisive next runs."),
(" A pre-registered harder variant did not lower Terra's score (Appendix D).", ""),
]
for o,n in R:
    assert s.count(o)==1,o[:60]
    s=s.replace(o,n)
open(D+'PAPER_V3_r1.md','w').write(s)
print('ok2')
