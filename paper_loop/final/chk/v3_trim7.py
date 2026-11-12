import re
f='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/paperloop/final/v3/body.md'
s=open(f).read()
R=[
("With the proxy, Terra sent all eight exact texts within 60 s in 24 of 24 runs; without it, at the same budget, in 0 of 24 (4/4 vs 0/4 on every item, sign test p = 0.031). The agent thus decides which hypotheses earn an exact test before any result exists, a non-adaptive design like Pando's (Zhong et al. 2026).",
 "With the proxy, Terra sent all eight exact texts within 60 s in 24 of 24 runs; without it, in 0 of 24 (4/4 vs 0/4 on every item, sign test p = 0.031). It thus picks which hypotheses earn an exact test before any result exists, a non-adaptive design like Pando's (Zhong et al. 2026)."),
("Luna failed 17 of its 18 trap runs: in 10 it named the proxy's favourite, the [decoy], and in 7 it answered `none`. In 7 of the 10 [decoy] answers, Luna had itself isolated the [decoy] on exact logits in a clean pair before submitting, and that test showed no effect. The larger agents never kept the proxy's answer against their own clean exact test. This count was defined after the pre-registered tests and rests on the clean-pair flag.",
 "Luna failed 17 of 18 trap runs, naming the proxy's favourite, the [decoy], in 10 and answering `none` in 7. In 7 of the 10 [decoy] answers, Luna had itself isolated the [decoy] on exact logits in a clean pair, and that test showed no effect. The larger agents never kept the proxy's answer against their own clean exact test. This count was defined after the pre-registered tests and rests on the clean-pair flag."),
("Repeated runs of one item are replicates, so run-level p-values are conditional on the items. With three trap items no two-sided item-level test can go below 0.25; with six the floor is 0.031.",
 "Runs of one item are replicates, so run-level p-values are conditional on the items; with three trap items no two-sided item-level test can go below 0.25 (six items: 0.031)."),
("Every run of the larger agents with the proxy encoded its own texts with the SAE (100/100), and reading latent meanings was optional: Terra used corpus search by latent in 15 of 16 main-study runs, Opus in 0 of 16, and Opus still passed 11 of 16. Among Claude runs, a latent-reading tool was not associated with passing (10/16 vs 21/32, p = 1.0; descriptive).",
 "All 100 runs of the larger agents with the proxy encoded their own texts with the SAE, while reading latent meanings was optional: Terra used corpus search by latent in 15 of 16 main-study runs, Opus in 0 of 16 (and passed 11 of 16). Among Claude runs it was not associated with passing (10/16 vs 21/32, p = 1.0)."),
("The scope is narrow: one report-only judge and prompt (Circuit Oracle's grading setting, §8), the same model as the main agent, and no query log. Report-only judging fails here; a judge given the exact-query log is the natural next arm.",
 "Scope: one report-only judge and prompt (Circuit Oracle's grading setting, §8), the same model as the main agent, no query log. A judge given the exact-query log is the natural next arm."),
("**Once they have exact evidence, the larger agents read it correctly.** Exact results are near-noiseless by design, so this part is easy. With the proxy, a hard probe whose true cue was exact-tested passed 53 of 57 times in the development set (trap 27/31, two-part 26/26), and after a proxy-versus-exact contradiction the larger agents kept the proxy's reading in 0 of 11 cases.",
 "**Once they have exact evidence, the larger agents read it correctly.** Exact results are near-noiseless by design, so this part is easy. A hard probe whose true cue was exact-tested passed 53 of 57 times (trap 27/31, two-part 26/26), and after a proxy-versus-exact contradiction the larger agents kept the proxy's reading in 0 of 11 cases."),
]
for a,b in R:
    if s.count(a)!=1: print('MISS',a[:70]); continue
    s=s.replace(a,b)
open(f,'w').write(s)
toks=lambda t:[x for x in t.split() if re.search(r'[A-Za-z0-9]',x)]
print('body all',len(toks(s)))
prose='\n'.join(l for l in s.split('\n') if not l.startswith('|') and not l.startswith('>'))
print('prose',len(toks(prose)))
