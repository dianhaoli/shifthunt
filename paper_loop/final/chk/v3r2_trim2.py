"""V3 polish round 2, pass 3: intro claims, glossary and limitation de-duplication (in place)."""
D = '/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/paperloop/final/'
s = open(D + 'PAPER_V3_r2.md').read()
R = []
def r(o, n): R.append((o, n))

r("""**Terms used throughout.** *Hard probe*: the probe that gates the score, a trap or a two-part (nested) cue. *[decoy]*, *[main]*: the proxy's wrong favourite and the true cue on a trap. *Isolate*: exact-test one candidate by a single-property edit; *widen*: isolate the runner-up too. *First batch*: exact texts sent before any exact result returns. Bracketed tags such as [pre-reg] and [expl] mark evidence status (§4).""",
"""**Terms used throughout.** *Hard probe*: the probe that gates the score, a trap or a two-part (nested) cue. *Isolate*: exact-test one candidate by a single-property edit; *widen*: isolate the runner-up too. *First batch*: exact texts sent before any exact result returns. Tags such as [pre-reg] and [expl] mark evidence status (§4).""")

r("""Without it, Terra matches with 64 queries and falls short with 16 (run level only); a fit puts the match near 36. Claim 1 is established only for Terra: for Luna the pre-registered test was not supported (5/36 vs 1/24; the point estimate favours the proxy). [pre-reg]""",
"""Without it, Terra matches with 64 queries and falls short with 16 (run level only). Claim 1 is established only for Terra: for Luna the pre-registered test was not supported (5/36 vs 1/24; the point estimate favours the proxy). [pre-reg]""")

r("""The four larger agents read exact results correctly but often skip the decisive test: they commit their exact queries to the proxy's top candidates in one batch before any result returns, so on a trap the runner-up must be in that batch. Within one harness, Terra widens on 11/12 trap runs and the smaller, generally weaker GPT-6 Luna on 0/18; part of this gap is general capability.""",
"""The four larger agents read exact results correctly but commit their exact queries to the proxy's top candidates in one batch before any result returns, so on a trap the runner-up must be in that batch. Within one harness, Terra widens on 11/12 trap runs and the smaller, generally weaker GPT-6 Luna on 0/18, partly a capability gap.""")

r("""**Evidence.** The confirmatory results are the two Block 1 contrasts, J1-J2 and L1-L2. Allocation, widening and routes are exploratory and observational; route and agent are confounded.""",
"""**Evidence.** Allocation, widening and routes are exploratory and observational; route and agent are confounded.""")

r("""At eight queries the score cannot separate targeted from blanket widening, and Terra's trigger (possibly the closeness of the head's and runner-up's proxy readings) is unidentified; a forced-allocation arm would test widening causally.""",
"""At eight queries the score cannot separate targeted from blanket widening, and Terra's trigger is unidentified; a forced-allocation arm would test widening causally.""")

r("""**The proxy concentrates exact tests on its top two candidates.** At a matched eight queries the proxy changes where Terra's tests go, not how many (1.32 vs 1.29 isolations per planted probe). With the proxy, 84 of 95 isolations fall on its top two candidates; without it, 36 of 93 (Table 3). The proxy *raises* rank-2 testing (29% vs 10%): it narrows search to its top two, not to its favourite.""",
"""**The proxy concentrates exact tests on its top two candidates.** At a matched eight queries the proxy changes where Terra's tests go, not how many (1.32 vs 1.29 isolations per planted probe): 84 of 95 isolations fall on its top two candidates, against 36 of 93 without it (Table 3). It *raises* rank-2 testing (29% vs 10%), so it narrows search to its top two, not to its favourite.""")

for o, n in R:
    c = s.count(o); assert c == 1, (c, o[:90])
    s = s.replace(o, n)
open(D + 'PAPER_V3_r2.md', 'w').write(s)
print('applied', len(R))
