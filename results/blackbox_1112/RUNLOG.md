# Black-box study run log (append-only)

Spend is tracked per provider against two caps: OpenAI ≈ $800, Anthropic ≈ $130 (plan §0, rule 3).
`cum_openai` and `cum_anthropic` are cumulative USD after the row. Times are UTC.
Run id = first 12 characters of the container id (agent runs) or the request batch name (text-only calls).

| time | run id | arm | agent | item | status | usd | cum_openai | cum_anthropic |
|---|---|---|---|---|---|---|---|---|
| 2026-11-10T06:55Z | setup-keycheck | setup | all four models | - | ok (3 Claude 8-token replies, 1 OpenAI model lookup) | 0.00 | 0.00 | 0.00 |
| 2026-11-10T07:35Z | exp_e (24 calls) | exp_e | gpt-6.1-terra ×6, claude-opus-5-5 ×6, claude-sonnet-5-5 ×6, claude-haiku-5-5 ×6 | - | ok 24/24 (openai 0.017, anthropic 0.500) | 0.52 | 0.02 | 0.50 |
