# Black-box study run log (append-only)

Spend is tracked per provider against two caps: OpenAI ≈ $800, Anthropic ≈ $130 (plan §0, rule 3).
`cum_openai` and `cum_anthropic` are cumulative USD after the row. Times are UTC.
Run id = first 12 characters of the container id (agent runs) or the request batch name (text-only calls).

| time | run id | arm | agent | item | status | usd | cum_openai | cum_anthropic |
|---|---|---|---|---|---|---|---|---|
| 2026-11-10T06:55Z | setup-keycheck | setup | all four models | - | ok (3 Claude 8-token replies, 1 OpenAI model lookup) | 0.00 | 0.00 | 0.00 |
