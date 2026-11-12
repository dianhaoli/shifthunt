"""V3 polish round 1, final wording fixes after read-through."""
D='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/paperloop/final/'
s=open(D+'PAPER_V3_r1.md').read()
R=[
("**Failures are failures to acquire evidence, not to read it; search narrows to the proxy's top candidates.**",
 "**For the four larger agents, failures are failures to acquire evidence, not to read it; search narrows to the proxy's top candidates.**"),
("(better on all six items); matching the tools takes it 16 to 64 exact measurements.",
 "(better on all six items); without them it needs 16 to 64 exact measurements to match."),
("*First batch*: exact texts sent before any exact result returns.",
 "*First batch*: exact texts sent before any exact result returns. Bracketed tags such as [pre-reg] and [expl] mark evidence status (§4)."),
]
for o,n in R:
    assert s.count(o)==1,o[:60]
    s=s.replace(o,n)
open(D+'PAPER_V3_r1.md','w').write(s)
print('ok')
# applied inline afterwards: Limitations clause 'pre-registered once Terra's results were known' added to the Luna sentence.
