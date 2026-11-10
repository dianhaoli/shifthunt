# Exp F: round trip of curly apostrophes and double spaces

Written by `scripts/exp_f_listing.py roundtrip`. One tiny call per model, no tools. The prompt holds a note with curly apostrophes (U+2019) and two spaces after each period:

```
It’s a calm day.  He’s out on the water early.  The boat’s sails are up.
```

Checks: the stored request bytes hold U+2019 and the note's bytes exactly (double spaces included); each returned regex, run with `shifthunt.regex_sandbox.run_regex`, matches the note and not its copy with straight apostrophes (curly) or single spaces (double_space). Regexes are shown with non-ASCII characters escaped.

| model | status | request: U+2019 | request: note bytes exact | curly regex | curly pass | double-space regex | double-space pass | USD |
|---|---|---|---|---|---|---|---|---|
| gpt-6.1-terra | ok | True | True | `\u2019` | True | `\.  ` | True | 0.0005 |
| claude-opus-5-5 | ok | True | True | `\u2019` | True | `\. {2}` | True | 0.0064 |
| claude-sonnet-5-5 | ok | True | True | `\u2019` | True | `\. {2}` | True | 0.0041 |
| claude-haiku-5-5 | ok | True | True | `\u2019` | True | `\.  ` | True | 0.0002 |

Overall: **PASS**.
