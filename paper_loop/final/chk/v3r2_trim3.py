"""V3 polish round 2, pass 4: small cuts (in place)."""
D = '/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/paperloop/final/'
s = open(D + 'PAPER_V3_r2.md').read()
R = []
def r(o, n): R.append((o, n))
r("""**The primary trend.** For the four larger agents, the shortfall comes before any exact result: tests go to the proxy's head in one batch, and where the head is wrong, passing needs the runner-up in that batch. On nested cues the decisive hypothesis is often never formed, although models asked in text only list the nested cue as often as plain cues (Appendix M; cf. GX-Chen et al. 2025). The strongest evidence not built into the design: 26 of 30 errors left the true cue untested, and the proxy made Terra commit its whole budget at once (24/24 vs 0/24 runs).""",
"""**The primary trend.** For the four larger agents the shortfall comes before any exact result. The strongest evidence not built into the design: 26 of 30 errors left the true cue untested, and the proxy made Terra commit its whole budget at once (24/24 vs 0/24 runs). On nested cues the decisive hypothesis is often never written down, although models asked in text only list it as often as plain cues (Appendix M; cf. GX-Chen et al. 2025).""")
r(""" Nusrat and Nusrat (2026) grade naming and repair exactly on small clinical networks.""", "")
r("""- Nusrat, Nusrat. Weight-space programming for auditing clinical decision networks. arXiv 2611.05341, 2026.
""", "")
r("""; we recommend reporting tool ablations as budget curves with this break-even price.""", """, the price to report beside a budget curve.""")
r("""The trigger is unidentified; on traps the runner-up's proxy reading is close to the head's, which may prompt widening (Appendix M).""",
"""The trigger is unidentified; on traps the runner-up's proxy reading is close to the head's (Appendix M).""")
for o, n in R:
    c = s.count(o); assert c == 1, (c, o[:90])
    s = s.replace(o, n)
open(D + 'PAPER_V3_r2.md', 'w').write(s)
print('applied', len(R))
# Two further inline cuts applied after this script (recorded here): removed " Exact results are near-noiseless by design,
# so this part is easy." from Section 5.3 (the point stays in Section 9), and "They know the candidates, edits and signs and
# were written after" -> "They are privileged and were written after" in Section 3.
