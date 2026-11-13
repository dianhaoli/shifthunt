# Prompt to paste to the GPU agent

Fetch branch `claude/nifty-wozniak-vunb6z` (`git fetch origin claude/nifty-wozniak-vunb6z`) and read
`paper_loop/gpu_plan/GPU_PLAN.md`. It links:
- the portfolio designs in `paper_loop/brainstorm/`;
- the exchange-rate analysis: `paper_loop/exchange_rate/SUMMARY_PLAIN.md`, `00_ANSWER.md`, `referee.md` and
  `calc/fig2/`.

Execute the plan on your own branch, `claude/serene-fermi-pog4k7`.

**Approved.** I approve every item in the plan's §2 table:
- the $0 items: Step 0, X1, X2, X4, C19, C21, X5;
- the API items: C8, C6 (including the Haiku judge), C14 (including stage 2), X3 Terra Open-4 and X3b Luna Open-4;
- the if-time items: C12 lean, C17 R2, C7 slim.

**Spend.**
- Set each item's cap as listed and pre-register before any counted run.
- Total new spend for this plan: at most $45 OpenAI and $5 Anthropic.
- Run in the plan's priority order: Step 0 and the $0 items first, then C14, C6, X3/X3b, C8, then the if-time items
  only while under the total.
- Stop and ask me before exceeding any cap.

**Rules.**
- Never commit a probe or episode id next to its cue property. Use [main]/[decoy], and run the leak scan in §7 before
  every commit.
- Keep the fresh C14 trap builds and cues private until after submission.
- Never edit `scripts/blackbox_schedule.py`. Add new arms through wrappers, as `bb16_schedule.py` and
  `luna_schedule.py` do.
- If budget 4 needs an image rebuild, stop X3 and tell me.
- Where the plan disagrees with what is on the box, the box wins. Log the deviation in that item's README.

**Deadline and reporting.**
- Hard stop for new data: 17 Nov 23:59 UTC.
- Log each finished item as one line in `results/blackbox_1112/RUNLOG.md` and push.
- At the end, fill `results/blackbox_1112/gpuplan/RESULTS_FOR_PAPER.md`, push, and tell me the commit hash.
