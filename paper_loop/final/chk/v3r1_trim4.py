"""V3 polish round 1, fourth trim (the five small cuts before it were applied inline: Claude-widening sentence order,
Limitations trap/prompt clauses, independent pass rule, Circuit Oracle 'asks whether' clause)."""
D='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/paperloop/final/'
s=open(D+'PAPER_V3_r1.md').read()
R=[
("The judge, GPT 6.1 Terra with one call per run, read the task contract, the agent's messages and its final answer,",
 "The judge, GPT 6.1 Terra, read the task contract, the agent's messages and its final answer,"),
("In plain terms, the trap edit routes the cue's effect through the part of the activation the SAE does not reconstruct and adds a direction that the SAE reads as a strong [decoy] but the probe barely uses; what the probe truly depends on is unchanged (Appendix M; cf. the SAE \"dark matter\" of Engels et al. 2025).",
 "In plain terms, the trap edit hides the cue's effect where the SAE cannot see it and adds a [decoy] direction that the SAE reads strongly but the probe barely uses; the probe's true dependence is unchanged (Appendix M; cf. SAE \"dark matter\", Engels et al. 2025)."),
("Its closed-form grader held against scripted exploits, and a report-only judge in its place would have shrunk the budget effect. On these six items, the larger agents read exact evidence correctly and reach a SHIFT-like removal route that the prompt does not prescribe. Their shortfall comes before any exact result: whether the proxy's runner-up enters the first batch, which within one harness depends on the model, and whether a nested hypothesis is written down. The recipe does not depend on SAEs; fresh items, deeper traps and a second domain are its next tests.",
 "Its closed-form grader held against scripted exploits; a report-only judge in its place would have shrunk the budget effect. On these six items, the larger agents read exact evidence correctly and reach a SHIFT-like removal route unprompted. Their shortfall comes before any exact result: whether the runner-up enters the first batch, which within one harness depends on the model, and whether a nested hypothesis is written down. The recipe does not depend on SAEs; fresh items, deeper traps and a second domain are its next tests."),
]
for o,n in R:
    assert s.count(o)==1,o[:60]
    s=s.replace(o,n)
open(D+'PAPER_V3_r1.md','w').write(s)
print('ok')
