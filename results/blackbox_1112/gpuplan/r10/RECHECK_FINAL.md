# Final independent recheck (read-only agent, 18 Nov ~09:30 UTC; prompt section 8)

Scope: ROUND10_DIFF rows against the output files (about 150 values, every flagged row), Table 3 / C12 / K0 recomputed
from raw r10 replies, the H1–H6 labels (bootstraps re-run), AD3, AD4 (Terra L2) and AD5 from raw, PROMPT_FIX hashes,
ORIG_HASHES, the round-10 spend, and a leak scan of the tracked r10 files.

**Matched:** every ROUND10_DIFF value checked; the raw recomputes (Terra L2 16/26, 6/17, 6/87; Sol S2 18/26, 9/17,
3/87; K0 0/26; L0 19/26, 9/17, 6/87; C12 Terra 17/39 vs 7/39, p 0.041); H1–H6 labels; AD3 F-b; AD5; AD4 (every credited
`none` now `verified: false`); all 18 r10 calls-file hashes; ORIG_HASHES (15,097 files unchanged); spend OpenAI $168.78
(5,178 calls) and Anthropic $5.93 (1,346 calls).

**Found and changed:**
1. RESULTS_FOR_PAPER Round 10, H1 bullet said Sol's transcript interval includes 50% under r10; it excludes it (18/26
   [0.586, 0.85]). *Corrected*; ROUND10_DIFF section 10 now notes Sol's sub-label change.
2. AD2 bullet: the r10 cluster-robust odds-ratio interval includes 1 at all three Terra levels (the item bootstrap
   excludes 1 at report + log only). *Corrected*, and the paper sentence on report + log softened accordingly.
3. "Failures per batch": C6b-H 2 (not 6) and C7 panel 6 (not 7) unparsed replies. *Corrected.*
4. ROUND10_DIFF: section 5's flags were set by hand although the header described a rule; the report-level wrong-`none`
   row (19/26, below the frozen item interval) was unflagged; the TF2 κ was missing from the header; Table 4's header
   said 40 pairs where report + log has 27; the C8 re-send date; and two changed labels were missing from section 10
   (C6b's "L2 κ < 0.40" prediction, True → False; D's reading). *All corrected* (the header now states that section 5's
   flags are hand-set plus the interval rule).
5. **Leak:** `out/gpuplan/r9/r9_2.json` and `diff/gpuplan__r9__r9_2.json` held redacted judge-reason samples produced by
   the unchanged R9 script on r10 reasons; round 9's hand edits (keyed to the frozen samples) did not apply, so 19 of
   them still contained property paraphrases. They were committed in 7ad7c9a (and copied in e84311e). *Changed:* every
   tracked r10 JSON was re-screened with the strict screen; 19 + 20 excerpts (and 1 in `reason_scan_frozen.json`) are now
   `[withheld]`. The earlier commits remain in the branch history (no history rewrite; no force-push), which the author
   should know. No run or episode id appears next to them.

Not checked by the agent: AD1's support labels, the AD2 fit itself, C17 / J1 / C19 / Tables 4–5 from raw (checked
against the output files only), AD4 for Sol and Terra L0 from raw.
