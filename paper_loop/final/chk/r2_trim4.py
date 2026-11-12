# Polish round 2, fourth pass: C11 consistency ("does" -> association) and length.
import sys
F='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/paperloop/final/PAPER_V2_r2.md'
s=open(F).read(); E=[]
def e(o,n): E.append((o,n))
e("Bursting itself does not predict failure (8/10 failing vs 15/22 passing main-study trap runs, p = 0.68); the burst's width on the trap does.",
  "Bursting itself does not predict failure (8/10 failing vs 15/22 passing main-study trap runs, p = 0.68); what goes with outcome is the burst's width on the trap.")
e("With the proxy, the agent fixes which hypotheses earn a gold test before any result exists, choosing for itself a non-adaptive design like Pando's (Zhong et al. 2026); without it, results guide the next test.",
  "With the proxy the agent thus fixes which hypotheses earn a gold test before any result exists, choosing a non-adaptive design like Pando's (Zhong et al. 2026).")
e(" catches 77% of all errors (without the proxy, 55% of errors for 46% of verdicts).", " catches 77% of all errors.")
e("We red-teamed the grader with six scripted cheaters (Appendix C); each scores zero on 6/6 episodes.",
  "Six scripted cheaters each score zero on 6/6 episodes.")
for o,n in E:
    c=s.count(o)
    if c!=1: sys.exit(f'COUNT {c}: {o[:80]}')
    s=s.replace(o,n)
open(F,'w').write(s); print('applied',len(E))
