import sys
p='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/paperloop/final/PAPER_V2_r1.md'
s=open(p).read(); R=[
(" The judge study uses one report-only judge and one prompt. A forced-allocation", " A forced-allocation"),
("Following the proxy is a positive test strategy (Klayman and Ha 1987): usually good, systematically wrong when the prior is biased.",
 "This is a positive test strategy (Klayman and Ha 1987), usually good and wrong when the prior is biased."),
("interpret exact measurements correctly once they make them, as near-noiseless measurements allow, but often do not make the decisive one.",
 "interpret exact measurements correctly once made (they are near-noiseless) but often do not make the decisive one."),
("Exploratory sections report uncorrected p-values from frozen scripts; they are descriptive and support no confirmatory claim.",
 "Exploratory p-values are uncorrected and descriptive."),
(", and a ledger records spend, image digest and pre-registration hash per launch. Random streams", ". Random streams"),
]
for a,b in R:
    if s.count(a)!=1: print('MISS',a[:80]); sys.exit(1)
    s=s.replace(a,b)
open(p,'w').write(s); print('ok')
