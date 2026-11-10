# Exp D: commands

One entry per run of `scripts/exp_d_listing.py` that sends calls or writes tracked results (UTC time, working directory, command).

- 2026-11-10T13:05:48Z cwd=`/home/ec2-user/shifthunt-public`: `/home/ec2-user/onsite/grader-wt/.venv/bin/python scripts/exp_d_listing.py run --budget-usd anthropic=30 --budget-usd openai=6 --limit 4 --workers 2`
  - prompt_template.txt sha256=e21bd2652033746232c28f1618556358348b5132593fe065d416ad1377e31309 commit=5ab51677be3bf707b01d83b5b5ae76ffe05f058e
  - calls.jsonl sha256=f614b93ec16db2605770df6f0dadd2ece1335129e093fdaeec09cca6afe1ed1d (400 built, 4 selected)
- 2026-11-10T13:06:18Z cwd=`/home/ec2-user/shifthunt-public`: `/home/ec2-user/onsite/grader-wt/.venv/bin/python scripts/exp_d_listing.py run --budget-usd anthropic=30 --budget-usd openai=6 --workers 2`
  - prompt_template.txt sha256=e21bd2652033746232c28f1618556358348b5132593fe065d416ad1377e31309 commit=5ab51677be3bf707b01d83b5b5ae76ffe05f058e
  - calls.jsonl sha256=f614b93ec16db2605770df6f0dadd2ece1335129e093fdaeec09cca6afe1ed1d (400 built, 400 selected)
- 2026-11-10T13:47:14Z cwd=`/home/ec2-user/shifthunt-public`: `/home/ec2-user/onsite/grader-wt/.venv/bin/python scripts/exp_d_listing.py score`
- 2026-11-10T13:51:18Z cwd=`/home/ec2-user/shifthunt-public`: `/home/ec2-user/onsite/grader-wt/.venv/bin/python scripts/exp_d_listing.py table --main-plain 128/128 --main-twopart 23/32 --main-source 'scripts/score_naming.py --main-study on the raw main-study runs (commit c80c82f): plain slots named 128/128; two-part hard slot NAME 23/32'`
