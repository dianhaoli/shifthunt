# Exp F: commands

One entry per run of `scripts/exp_f_listing.py` that sends calls or writes tracked results (UTC time, working
directory, command). `run`, `roundtrip`, `score` and `table` append their own entries below. Environment for
every command (the black-box study runs on the same box): `nice -n 19`, `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1`, `PY` = the study venv python,
`SHIFTHUNT_BANK` = the private bank (read-only).

Run before any call (no API call; the private outputs are under results/private_1112/exp_f/):

- 2026-11-10 cwd=`/home/ec2-user/shifthunt-public`: `$PY scripts/exp_f_listing.py build` (first build; superseded by the rebuild below after the review)
- 2026-11-10 cwd=`/home/ec2-user/shifthunt-public`: `$PY scripts/exp_f_listing.py build` (after the review fixes: 420 calls = 105 prompts x 4 models; calls.jsonl sha256 3681533ec6399d157d11112b6d8ebef9cd6ecc2e0de03670b085398fa4cdc54d; template sha256 fa25f12bd920692451c392460be3e9b66a47e9add0b6f691472d507f44c4faad; estimate 23.55 USD; no stress cue dropped)
- 2026-11-10 cwd=`/home/ec2-user/shifthunt-public`: `$PY scripts/exp_f_listing.py validate` (VALIDATION_RESULT; VALIDATION.md)
- 2026-11-10 cwd=`/home/ec2-user/shifthunt-public`: `$PY scripts/exp_f_listing.py estimate` (23.55 USD expected: Anthropic 21.29, OpenAI 2.21, round trip 0.05; DESIGN.md §6)

Planned, in this order (the user's): the round trip and the pilot run BEFORE the commit; the package (prompt,
scoring rule, cue list with reference regexes, predictions, pilot results) goes to the user; the user approves;
the design is committed; then the full run (not run yet):

```
$PY scripts/exp_f_listing.py roundtrip --budget-usd anthropic=25 --budget-usd openai=5                # 4 tiny calls
$PY scripts/exp_f_listing.py run --pilot --budget-usd anthropic=25 --budget-usd openai=5 --only 'F_ep472_*'   # 20 calls
$PY scripts/exp_f_listing.py score
$PY scripts/exp_f_listing.py table --pilot 'F_ep472_*'                 # private PILOT.md and pilot.json
#   -> send the package to the user; after approval: git commit (prompt_template.txt, DESIGN.md, ...)
$PY scripts/exp_f_listing.py run --budget-usd anthropic=25 --budget-usd openai=5                       # the rest
$PY scripts/exp_f_listing.py score
$PY scripts/exp_f_listing.py table --main-plain 128/128 --main-nested 23/32 --main-trap 22/32 \
    --main-source "scripts/score_naming.py --main-study (main study, commit c80c82f)"
$PY scripts/exp_f_listing.py runlog-sync          # only if a run died before it could log its spend
```
- 2026-11-10T22:51:27Z cwd=`/home/ec2-user/shifthunt-public`: `/home/ec2-user/onsite/grader-wt/.venv/bin/python scripts/exp_f_listing.py roundtrip --budget-usd anthropic=25 --budget-usd openai=5`
  - round trip: 4 tiny calls
- 2026-11-10T22:51:39Z cwd=`/home/ec2-user/shifthunt-public`: `/home/ec2-user/onsite/grader-wt/.venv/bin/python scripts/exp_f_listing.py run --pilot --budget-usd anthropic=25 --budget-usd openai=5 --only 'F_ep472_*'`
  - PILOT, before the user's approval: prompt_template.txt and DESIGN.md NOT committed (uncommitted state)
  - prompt_template.txt sha256=fa25f12bd920692451c392460be3e9b66a47e9add0b6f691472d507f44c4faad commit=None
  - DESIGN.md sha256=8b1e4e1cf3278d366cca6c0d99b39536b6ca14817cd9c61ac89fbb3e5fdc562e commit=None
  - calls.jsonl sha256=3681533ec6399d157d11112b6d8ebef9cd6ecc2e0de03670b085398fa4cdc54d (420 built, 20 selected, 20 to send)
- 2026-11-10T22:53:43Z cwd=`/home/ec2-user/shifthunt-public`: `/home/ec2-user/onsite/grader-wt/.venv/bin/python scripts/exp_f_listing.py score`
- 2026-11-10T22:56:44Z cwd=`/home/ec2-user/shifthunt-public`: `/home/ec2-user/onsite/grader-wt/.venv/bin/python scripts/exp_f_listing.py run --budget-usd anthropic=25 --budget-usd openai=5 --workers 2`
  - prompt_template.txt sha256=fa25f12bd920692451c392460be3e9b66a47e9add0b6f691472d507f44c4faad commit=ccdb1b1e7944ab3123875c24573009b14a62ef4c
  - DESIGN.md sha256=c691875366ed56e09acbb9bcbbf7a6b9b33d120d7d09ff67c6772a51ca433bc3 commit=ccdb1b1e7944ab3123875c24573009b14a62ef4c
  - calls.jsonl sha256=3681533ec6399d157d11112b6d8ebef9cd6ecc2e0de03670b085398fa4cdc54d (420 built, 420 selected, 400 to send)
- 2026-11-10T23:19:29Z cwd=`/home/ec2-user/shifthunt-public`: `/home/ec2-user/onsite/grader-wt/.venv/bin/python scripts/exp_f_listing.py score`
- 2026-11-10T23:55:50Z cwd=`/home/ec2-user/shifthunt-public`: `/home/ec2-user/onsite/grader-wt/.venv/bin/python scripts/exp_f_listing.py score`
- 2026-11-11T00:00:12Z cwd=`/home/ec2-user/shifthunt-public`: `/home/ec2-user/onsite/grader-wt/.venv/bin/python scripts/exp_f_listing.py table --main-plain 128/128 --main-nested 23/32 --main-trap 22/32 --main-source 'scripts/score_naming.py --main-study (main study, commit c80c82f)'`
