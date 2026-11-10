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
| 2026-11-10T13:19Z | b67b0bf1c8ef | bb64 | gpt | ep472 | ok | 0.386 | 2.069 | 1.509 |
| 2026-11-10T13:22Z | 29a9c5a59d82 | bb64 | haiku | ep413 | ok | 0.630 | 2.069 | 2.139 |
| 2026-11-10T13:30Z | 54f9ad91611c | bb64 | gpt | ep472 | ok | 0.812 | 2.881 | 2.139 |
| 2026-11-10T13:36Z | b4ec220ca7e3 | bb64 | gpt | ep476 | ok | 0.415 | 3.296 | 2.139 |
| 2026-11-10T13:45Z | exp_d (400 calls) | exp_d | gpt-6.1-terra ×100, claude-opus-5-5 ×100, claude-sonnet-5-5 ×100, claude-haiku-5-5 ×100 | - | ok 400/400 (openai 2.375, anthropic 18.373) | 20.748 | 5.671 | 20.512 |
| 2026-11-10T13:49Z | cb3eae38f5ce | open8 | gpt | ep476 | ok | 0.644 | 6.315 | 20.512 |
| 2026-11-10T13:53Z | afe465b9df76 | bb8 | gpt | ep474 | ok (codex_error_recovered) | 1.344 | 7.659 | 20.512 |
| 2026-11-10T13:54Z | e0e706576849 | open8 | gpt | ep472 | ok | 0.725 | 8.384 | 20.512 |
| 2026-11-10T13:58Z | 6362226b6a3a | bb64 | gpt | ep413 | ok | 0.293 | 8.677 | 20.512 |
| 2026-11-10T14:15Z | 67bc5b41db84 | open8 | gpt | ep413 | ok | 0.710 | 9.387 | 20.512 |
| 2026-11-10T14:17Z | 97950b6d8f57 | bb64 | haiku | ep413 | ok | 0.726 | 9.387 | 21.238 |
| 2026-11-10T14:22Z | 2c9ae4c7e30f | bb8 | haiku | ep474 | ok | 1.303 | 9.387 | 22.541 |
| 2026-11-10T14:32Z | 9d7ae27fd4f0 | bb64 | haiku | ep411 | ok | 0.689 | 9.387 | 23.230 |
| 2026-11-10T14:40Z | 8f6e5ae1ea30 | open8 | gpt | ep476 | ok | 0.602 | 9.989 | 23.230 |
| 2026-11-10T14:43Z | f41997827cd0 | bb64 | gpt | ep476 | ok | 0.947 | 10.936 | 23.230 |
| 2026-11-10T14:58Z | bbf1157679c3 | open8 | gpt | ep411 | ok | 0.612 | 11.548 | 23.230 |
| 2026-11-10T15:00Z | 392f5629f318 | bb8 | gpt | ep413 | ok | 0.826 | 12.374 | 23.230 |
| 2026-11-10T15:00Z | 67a30a8da8f4 | bb64 | gpt | ep474 | ok | 0.490 | 12.864 | 23.230 |
| 2026-11-10T15:17Z | 6a5e5ccb30b7 | open8 | gpt | ep472 | ok | 0.549 | 13.413 | 23.230 |
| 2026-11-10T15:19Z | e62427fcbcf9 | open8 | haiku | ep474 | ok | 1.040 | 13.413 | 24.270 |
| 2026-11-10T15:34Z | c87bc1c4b1a9 | bb8 | haiku | ep472 | ok | 1.624 | 13.413 | 25.894 |
| 2026-11-10T15:42Z | b41b2272ec5d | open8 | gpt | ep413 | ok | 0.937 | 14.350 | 25.894 |
| 2026-11-10T15:44Z | 2727265002d4 | bb8 | gpt | ep476 | ok | 0.862 | 15.212 | 25.894 |
| 2026-11-10T16:00Z | 580745f7c7ea | open8 | gpt | ep411 | ok | 0.716 | 15.928 | 25.894 |
| 2026-11-10T16:02Z | d38ee7ebab09 | bb8 | gpt | ep415 | ok | 0.992 | 16.920 | 25.894 |
| 2026-11-10T16:15Z | d4e66a5ae8b2 | bb8 | haiku | ep415 | ok | 1.544 | 16.920 | 27.438 |
| 2026-11-10T16:21Z | 4a5ae56dd044 | bb64 | haiku | ep472 | ok | 0.759 | 16.920 | 28.197 |
| 2026-11-10T16:23Z | 3bc764e5d5b9 | bb64 | gpt | ep411 | ok | 0.223 | 17.143 | 28.197 |
| 2026-11-10T16:27Z | 72f1fbc42c93 | bb8 | gpt | ep413 | ok | 0.892 | 18.035 | 28.197 |
| 2026-11-10T16:34Z | dca067d7dea8 | bb64 | gpt | ep413 | ok | 0.200 | 18.235 | 28.197 |
| 2026-11-10T16:35Z | 04b5aca1258a | open8 | gpt | ep476 | ok | 0.614 | 18.849 | 28.197 |
| 2026-11-10T16:45Z | e9389bdb4578 | bb8 | gpt | ep476 | ok | 0.835 | 19.684 | 28.197 |
| 2026-11-10T16:56Z | e9df3deb75fb | open8 | gpt | ep476 | ok (codex_error_recovered) | 0.825 | 20.509 | 28.197 |
| 2026-11-10T17:02Z | 73065c82846e | bb8 | gpt | ep474 | ok (codex_error_recovered) | 1.111 | 21.620 | 28.197 |
| 2026-11-10T17:05Z | 7ee5a16535ee | open8 | gpt | ep413 | ok | 0.782 | 22.402 | 28.197 |
| 2026-11-10T17:19Z | f21d6894141f | bb64 | gpt | ep472 | ok | 0.418 | 22.820 | 28.197 |
| 2026-11-10T17:23Z | 9e94f125b517 | bb8 | haiku | ep476 | ok | 0.853 | 22.820 | 29.050 |
| 2026-11-10T17:35Z | abb8a9636286 | bb8 | gpt | ep474 | ok | 1.531 | 24.351 | 29.050 |
| 2026-11-10T17:40Z | db9446d3e746 | open8 | haiku | ep415 | ok | 0.914 | 24.351 | 29.964 |
| 2026-11-10T17:49Z | d25aca1b6db0 | open8 | haiku | ep472 | ok | 1.316 | 24.351 | 31.280 |
| 2026-11-10T18:03Z | 32eeb80ce0e4 | open8 | gpt | ep474 | ok | 0.489 | 24.840 | 31.280 |
| 2026-11-10T18:05Z | e0ca038acf56 | open8 | haiku | ep415 | ok | 1.056 | 24.840 | 32.336 |
| 2026-11-10T18:11Z | 5c7b64a24477 | bb8 | haiku | ep413 | ok | 1.753 | 24.840 | 34.089 |
| 2026-11-10T18:21Z | 6fc6e9d5bb30 | open8 | gpt | ep474 | ok | 0.711 | 25.551 | 34.089 |
| 2026-11-10T18:27Z | 90d4251352b5 | bb8 | gpt | ep472 | ok | 0.676 | 26.227 | 34.089 |
| 2026-11-10T18:34Z | e615c5938f9e | bb8 | gpt | ep472 | ok | 0.831 | 27.058 | 34.089 |
| 2026-11-10T18:45Z | a4aa52644854 | bb64 | gpt | ep476 | ok | 0.383 | 27.441 | 34.089 |
| 2026-11-10T18:46Z | 620c2c1948fe | open8 | gpt | ep411 | ok | 0.767 | 28.208 | 34.089 |
| 2026-11-10T18:48Z | ec4d97a1786d | open8 | haiku | ep413 | ok | 1.049 | 28.208 | 35.138 |
| 2026-11-10T18:59Z | 8ed93887adeb | bb64 | gpt | ep476 | ok | 0.423 | 28.631 | 35.138 |
| 2026-11-10T19:02Z | 13e8a939b242 | open8 | gpt | ep413 | ok | 0.720 | 29.351 | 35.138 |
| 2026-11-10T19:06Z | 744e297e57b1 | open8 | gpt | ep415 | ok | 0.660 | 30.011 | 35.138 |
| 2026-11-10T19:08Z | 61b5c00fb404 | bb64 | gpt | ep415 | ok | 0.294 | 30.305 | 35.138 |
| 2026-11-10T19:11Z | b24bb04016d1 | bb64 | gpt | ep413 | ok | 0.289 | 30.594 | 35.138 |
| 2026-11-10T19:17Z | 0cf158e42e8e | bb64 | gpt | ep474 | ok | 0.409 | 31.003 | 35.138 |
| 2026-11-10T19:26Z | 92a9ac6d040b | open8 | haiku | ep476 | ok | 0.772 | 31.003 | 35.910 |
| 2026-11-10T19:26Z | 5c4cf391ea5f | bb64 | gpt | ep411 | ok | 0.270 | 31.273 | 35.910 |
| 2026-11-10T19:34Z | c4bbedfd9003 | bb64 | haiku | ep476 | ok | 0.903 | 31.273 | 36.813 |
| 2026-11-10T19:41Z | 8b0e4174b700 | open8 | gpt | ep474 | ok | 0.612 | 31.885 | 36.813 |
| 2026-11-10T19:47Z | 26e27553ea1c | open8 | haiku | ep411 | ok | 0.892 | 31.885 | 37.705 |
| 2026-11-10T20:00Z | 91b051a1f95d | bb8 | gpt | ep415 | ok | 0.842 | 32.727 | 37.705 |
| 2026-11-10T20:01Z | e5db687fdd6a | open8 | gpt | ep415 | ok | 0.776 | 33.503 | 37.705 |
| 2026-11-10T20:07Z | a340351d2934 | open8 | haiku | ep413 | ok | 0.795 | 33.503 | 38.500 |
| 2026-11-10T20:17Z | 479239b4c83f | bb64 | haiku | ep472 | ok | 0.668 | 33.503 | 39.168 |
| 2026-11-10T20:30Z | 8cac292d7ed4 | bb8 | haiku | ep472 | ok | 1.178 | 33.503 | 40.346 |
| 2026-11-10T20:30Z | dbb2d25647f0 | bb8 | gpt | ep476 | ok | 0.809 | 34.312 | 40.346 |
| 2026-11-10T20:39Z | 271a02492f8c | bb64 | gpt | ep415 | ok | 0.235 | 34.547 | 40.346 |
| 2026-11-10T20:41Z | 4b0762a0c53f | bb8 | gpt | ep472 | ok | 0.994 | 35.541 | 40.346 |
| 2026-11-10T20:51Z | cfff9c96bb16 | bb8 | gpt | ep415 | ok | 0.720 | 36.261 | 40.346 |
| 2026-11-10T20:58Z | f6c824ac7985 | open8 | gpt | ep472 | ok | 0.724 | 36.985 | 40.346 |
| 2026-11-10T20:59Z | df7a956cf9ab | open8 | haiku | ep472 | ok | 0.909 | 36.985 | 41.255 |
| 2026-11-10T21:05Z | 833d9ef52bf7 | bb64 | gpt | ep474 | ok | 0.446 | 37.431 | 41.255 |
| 2026-11-10T21:20Z | e746a5f0618d | bb64 | haiku | ep474 | ok | 0.943 | 37.431 | 42.198 |
| 2026-11-10T21:25Z | ce83d0006947 | bb8 | haiku | ep415 | ok | 1.150 | 37.431 | 43.348 |
| 2026-11-10T21:27Z | d2bf3a202415 | bb8 | gpt | ep413 | ok | 0.718 | 38.149 | 43.348 |
| 2026-11-10T21:34Z | bec8b4b6a49c | bb64 | gpt | ep472 | ok | 0.294 | 38.443 | 43.348 |
| 2026-11-10T21:39Z | d738ab6b8ac3 | open8 | gpt | ep415 | ok | 0.758 | 39.201 | 43.348 |
| 2026-11-10T21:51Z | d8fe8cb5529c | open8 | gpt | ep411 | ok | 0.394 | 39.595 | 43.348 |
| 2026-11-10T21:52Z | 4d99181566cf | bb8 | gpt | ep411 | ok | 0.819 | 40.414 | 43.348 |
| 2026-11-10T21:57Z | 8be7adb42a1a | bb64 | haiku | ep476 | ok | 1.168 | 40.414 | 44.516 |
| 2026-11-10T22:13Z | 32a550d6c62d | open8 | gpt | ep474 | ok | 0.714 | 41.128 | 44.516 |
| 2026-11-10T22:20Z | a4a64154cd9b | bb8 | haiku | ep413 | ok | 1.247 | 41.128 | 45.763 |
| 2026-11-10T22:27Z | ee1521588124 | bb8 | gpt | ep476 | ok | 1.076 | 42.204 | 45.763 |
| 2026-11-10T22:31Z | 6f3f6903885e | bb64 | haiku | ep411 | ok | 0.743 | 42.204 | 46.506 |
| 2026-11-10T22:43Z | 910e77f71e2c | bb8 | haiku | ep411 | ok | 0.917 | 42.204 | 47.423 |
| 2026-11-10T22:44Z | c5b434233252 | open8 | gpt | ep472 | ok | 0.509 | 42.713 | 47.423 |
| 2026-11-10T22:49Z | 4b5bbd16d149 | open8 | haiku | ep476 | ok | 1.003 | 42.713 | 48.426 |
| 2026-11-10T22:51Z | exp_f roundtrip (4 calls) | exp_f | gpt-6.1-terra ×1, claude-opus-5-5 ×1, claude-sonnet-5-5 ×1, claude-haiku-5-5 ×1 | - | ok 4/4 (openai 0.000543, anthropic 0.010737) | 0.011 | 42.714 | 48.437 |
| 2026-11-10T22:53Z | exp_f pilot (20 calls) | exp_f | gpt-6.1-terra ×5, claude-opus-5-5 ×5, claude-sonnet-5-5 ×5, claude-haiku-5-5 ×5 | - | ok 20/20 (openai 0.111778, anthropic 0.949502) | 1.061 | 42.826 | 49.387 |
| 2026-11-10T22:56Z | exp_f manual round trip (4 calls, results/private_1112/exp_f_roundtrip) | exp_f | gpt-6.1-terra ×1, claude-opus-5-5 ×1, claude-sonnet-5-5 ×1, claude-haiku-5-5 ×1 | - | ok 4/4 (openai 0.0006, anthropic 0.0119; sent 21:4xZ, logged late) | 0.012 | 42.827 | 49.399 |
