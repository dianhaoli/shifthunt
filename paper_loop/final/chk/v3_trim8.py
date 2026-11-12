import re
f='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/paperloop/final/PAPER_V3.md'
s=open(f).read()
R=[
("Re-running the grader with each run's own latent shuffle reproduces all 100 stored grades of runs with the proxy (400/400 probe records), and an independently written pass rule agrees on every probe.",
 "Regrading reproduces all 100 stored grades of runs with the proxy, and an independently written pass rule agrees on every probe."),
("A positive control (true regex plus oracle latents) scores 1 on all six; a naive control (true regex plus the 16 latents with the largest attribution on the sample) earns full reward on only one.",
 "A positive control (true regex, oracle latents) scores 1 on all six; a naive control (true regex, the 16 latents most attributed on the sample) earns full reward on one."),
("A bank of 97 episodes (250 distinct probes) has so far been run with scripted policies only, not with agents.",
 "A 97-episode bank has so far been run with scripted policies only."),
("Without the proxy, Terra needs between 16 and 64 queries to match it. [pre-reg]",
 "Without the proxy, Terra needs more than 16 and up to 64 queries to match it. [pre-reg]"),
("Prediction-powered inference and active testing (Angelopoulos et al. 2023; Ashouritaklimi et al. 2026) use proxies for *estimation*; we measure *acquisition* (cf. Ma et al. 2026).",
 "Prediction-powered inference and active testing (Angelopoulos et al. 2023; Ashouritaklimi et al. 2026) use proxies for *estimation*; we measure *acquisition* (cf. Ma et al. 2026)."),
("Karvonen et al. (2024) automate SHIFT with an oracle-normalized score; Nusrat and Nusrat (2026) grade naming and repair exactly on small clinical networks. To our knowledge,",
 "Nusrat and Nusrat (2026) grade naming and repair exactly on small clinical networks. To our knowledge,"),
("**Statistics.** We use Fisher tests and Wilson intervals (Bowyer et al. 2025); confirmatory tests add within-item permutation, Holm correction and an item-clustered bootstrap.",
 "**Statistics.** Fisher tests and Wilson intervals (Bowyer et al. 2025); confirmatory tests add within-item permutation, Holm correction and an item-clustered bootstrap."),
("**Following the proxy two deep is the best reference policy here.** The top-two policy (0.96) beats the top-one policy (0.50) and the hedge (0.68), and Terra ties it.",
 "**Following the proxy two deep is the best reference policy here.** The top-two policy (0.96) beats the top-one policy and the hedge, and Terra ties it."),
("This is not debiasing: on traps the threshold is 0.15-0.22, so a passing probe keeps most of its reliance on the cue (§2.4).",
 "This is not debiasing: on traps the threshold is 0.15-0.22, so a passing probe keeps most of its reliance on the cue."),
("**Generality.** The recipe has been applied to two proxies inside one environment; transfer to other domains is argued, not shown.",
 "**Generality.** The recipe has been applied to two proxies in one environment; transfer is argued, not shown."),
("Random streams and run orders are seeded. Each pre-registration was hash-committed before its first counted run, and a freeze log covers every follow-up definition and script.",
 "Random streams and run orders are seeded; each pre-registration was hash-committed before its first counted run, and a freeze log covers every follow-up script."),
("The agent must decide which hypotheses earn a scarce test after a cheap signal has ranked them, and widen its search when that ranking may be wrong.",
 "The agent must decide which hypotheses earn a scarce test after a cheap signal has ranked them, and widen its search when the ranking may be wrong."),
("On the surface it is a model-auditing task from mechanistic interpretability. A linear probe on Gemma-2-2B sorts short notes by topic, but it also relies on a hidden text property, its *cue*.",
 "On the surface it is a model-auditing task: a linear probe on Gemma-2-2B sorts short notes by topic but also relies on a hidden text property, its *cue*."),
("Since the hard probe decided","Since the hard probe decided"),
]
for a,b in R:
    if s.count(a)!=1: print('MISS',a[:70]); continue
    s=s.replace(a,b)
open(f,'w').write(s)
