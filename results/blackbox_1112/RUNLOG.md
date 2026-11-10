# Black-box study run log (append-only)

Spend is tracked per provider against two caps: OpenAI ≈ $800, Anthropic ≈ $130 (plan §0, rule 3).
`cum_openai` and `cum_anthropic` are cumulative USD after the row. Times are UTC.
Run id = first 12 characters of the container id (agent runs) or the request batch name (text-only calls).

| time | run id | arm | agent | item | status | usd | cum_openai | cum_anthropic |
|---|---|---|---|---|---|---|---|---|
| 2026-11-10T06:55Z | setup-keycheck | setup | all four models | - | ok (3 Claude 8-token replies, 1 OpenAI model lookup) | 0.00 | 0.00 | 0.00 |
| 2026-11-10T07:35Z | exp_e (24 calls) | exp_e | gpt-6.1-terra ×6, claude-opus-5-5 ×6, claude-sonnet-5-5 ×6, claude-haiku-5-5 ×6 | - | ok 24/24 (openai 0.017, anthropic 0.500) | 0.52 | 0.02 | 0.50 |
| 2026-11-10T12:32Z | 2c9ee009bdc8 | bb64 (pilot) | gpt | ep411 | ok | 0.292 | 0.312 | 0.500 |
| 2026-11-10T12:33Z | c1471efa5db5 | open8 (pilot) | gpt | ep411 | ok | 0.496 | 0.808 | 0.500 |
| 2026-11-10T12:45Z | cbf915076e07 | bb8 (pilot) | gpt | ep411 | ok | 0.875 | 1.683 | 0.500 |
| 2026-11-10T12:56Z | d9877b3db3b5 | bb8 (pilot) | haiku | ep472 | ok | 1.009 | 1.683 | 1.509 |
