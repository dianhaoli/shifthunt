# Polish round 2, second length pass (in place; exact-match, each once).
import sys
F='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/paperloop/final/PAPER_V2_r2.md'
s=open(F).read(); E=[]
def e(o,n): E.append((o,n))
e("Without it the task is easy: with 64 exact queries and no SAE, GPT 6.1 Terra names every hard cue (24/24).",
  "Without it the task is easy (§5.1).")
e("(trap 27/31, two-part 26/26; the exceptions are two threshold misreads and two untested extra cues)",
  "(trap 27/31, two-part 26/26)")
e(" In every probe's sample, several properties of the text […] agree exactly with the label […], so the sample alone does not tell you what a probe relies on.", "")
e("; the hard slot differs from NAME only in BB-8, 11/36 vs 9/36, where two GPT runs named the hard cue but also claimed a cue on the null probe].**",
  "; BB-8 is 11/36 on the hard slot but 9/36 on NAME because two GPT runs also claimed a cue on the null probe].**")
for o,n in E:
    c=s.count(o)
    if c!=1: sys.exit(f'COUNT {c}: {o[:80]}')
    s=s.replace(o,n)
open(F,'w').write(s); print('applied',len(E))
