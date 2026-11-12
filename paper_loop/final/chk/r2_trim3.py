# Polish round 2, third pass: consistency with C11 and the GPT-only judge bound, plus length.
import sys
F='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/paperloop/final/PAPER_V2_r2.md'
s=open(F).read(); E=[]
def e(o,n): E.append((o,n))
e("where the head is wrong the first batch's width decides, and on nested cues",
  "where the head is wrong, passing needs the runner-up tested, and agents differ in whether the first batch includes it; on nested cues")
e("and a report-only judge in its place would have erased most of the budget effect and reversed a comparison between arms.",
  "and a report-only judge in its place would have shrunk the budget effect and, pooled over agents, reversed a comparison between arms.")
e(" AstaBench reports judge-expert agreement at system level; J1-J4 measure it on decisive slots against executed ground truth.", "")
e("Episode reward equals the hard-slot indicator in 64/64 main-study runs and the other probes passed 192/192, so evaluation budget",
  "The hard slot decides episode reward (64/64 main-study runs), so evaluation budget")
e("This is not debiasing: on traps τ is 0.15-0.22 and most of the cue's effect sits in the SAE error term, so a passing probe keeps most of its reliance on the cue.",
  "This is not debiasing: on traps τ is 0.15-0.22, so a passing probe keeps most of its reliance on the cue (§2.4).")
e("The recipe does not depend on SAEs; we applied it to the SAE tools and to an LLM judge, and fresh items, deeper traps and a second domain are its next tests.",
  "The recipe does not depend on SAEs; fresh items, deeper traps and a second domain are its next tests.")
for o,n in E:
    c=s.count(o)
    if c!=1: sys.exit(f'COUNT {c}: {o[:80]}')
    s=s.replace(o,n)
open(F,'w').write(s); print('applied',len(E))
