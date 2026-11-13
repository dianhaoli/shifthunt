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
| 2026-11-10T22:58Z | 3989045eba3e | bb64 | gpt | ep411 | ok | 0.295 | 43.122 | 49.399 |
| 2026-11-10T23:07Z | f35851679ee4 | open8 | haiku | ep474 | ok | 1.238 | 43.122 | 50.637 |
| 2026-11-10T23:14Z | 8349c713359b | bb8 | haiku | ep474 | ok | 1.545 | 43.122 | 52.182 |
| 2026-11-10T23:16Z | 123f6463f065 | bb8 | gpt | ep411 | ok | 0.581 | 43.703 | 52.182 |
| 2026-11-10T23:22Z | 543d2b1f9971 | bb64 | gpt | ep415 | ok | 0.239 | 43.942 | 52.182 |
| 2026-11-10T23:30Z | 3b966026b482 | bb64 | gpt | ep415 | ok | 0.426 | 44.368 | 52.182 |
| 2026-11-10T23:32Z | 64d3c125c0f6 | bb8 | gpt | ep472 | ok | 0.947 | 45.315 | 52.182 |
| 2026-11-10T23:47Z | f35702cc1aab | bb64 | haiku | ep415 | ok | 1.104 | 45.315 | 53.286 |
| 2026-11-10T23:51Z | a468b55a4fd0 | bb8 | gpt | ep411 | ok | 0.666 | 45.981 | 53.286 |
| 2026-11-10T23:52Z | b74ca474a35d | open8 | haiku | ep411 | ok | 0.926 | 45.981 | 54.212 |
| 2026-11-10T23:55Z | exp_f (400 calls) | exp_f | gpt-6.1-terra ×100, claude-opus-5-5 ×100, claude-sonnet-5-5 ×100, claude-haiku-5-5 ×100 | - | ok 400/400 (openai 2.736619, anthropic 20.575487) | 23.312 | 48.718 | 74.787 |
| 2026-11-10T23:59Z | 3da4a92a3de9 | bb64 | gpt | ep411 | ok | 0.214 | 48.932 | 74.787 |
| 2026-11-11T00:14Z | bb8a1da45524 | bb8 | gpt | ep413 | ok | 0.979 | 49.911 | 74.787 |
| 2026-11-11T00:15Z | 30fd403d01a1 | bb8 | haiku | ep476 | ok | 1.084 | 49.911 | 75.871 |
| 2026-11-11T00:21Z | 926a7563fe66 | bb64 | gpt | ep413 | ok | 0.230 | 50.141 | 75.871 |
| 2026-11-11T00:29Z | d12b5b6bfba1 | bb64 | gpt | ep474 | ok | 0.304 | 50.445 | 75.871 |
| 2026-11-11T00:33Z | cc2e85fb2979 | bb8 | gpt | ep474 | ok | 1.401 | 51.846 | 75.871 |
| 2026-11-11T00:35Z | 47f8a94ff0e4 | open8 | gpt | ep415 | ok | 0.718 | 52.564 | 75.871 |
| 2026-11-11T00:55Z | 966058d8d8f8 | bb8 | haiku | ep411 | ok | 0.610 | 52.564 | 76.481 |
| 2026-11-11T01:02Z | 69158ac330ad | bb8 | gpt | ep415 | ok | 1.124 | 53.688 | 76.481 |
| 2026-11-11T01:12Z | 61b772d162d3 | bb8 | gpt | ep411 | ok | 1.610 | 55.298 | 76.481 |
| 2026-11-11T01:13Z | d8b7bc9faea9 | bb64 | haiku | ep415 | ok | 0.723 | 55.298 | 77.204 |
| 2026-11-11T01:28Z | 916724dfde63 | bb64 | haiku | ep474 | ok | 1.199 | 55.298 | 78.403 |
| 2026-11-11T06:20Z | coders pilot (4 calls, results/private_1112/followup/coders/raw_pilot) | coders | gpt-6.1-terra ×4 | - | ok 4/4 (openai 0.294355) | 0.294 | 55.592 | 78.403 |
| 2026-11-11T06:51Z | 0277bb9f04c1 | bb16 (pilot) | gpt | ep472 | ok | 0.451 | 56.043 | 78.403 |
| 2026-11-11T06:52Z | coders full (212 calls, 106 transcripts × coders A and B; two client processes, results/private_1112/followup/coders/raw_full_1 and raw_full_2; sent 06:23Z–06:52Z) | coders | gpt-6.1-terra ×212 | - | ok 212/212 (openai 12.514541) | 12.515 | 68.558 | 78.403 |
| 2026-11-11T16:20Z | 2d2840009fb0 | bb16 | gpt | ep411 | ok | 0.338 | 68.896 | 78.403 |
| 2026-11-11T16:21Z | f9150bc3af9c | bb16 | gpt | ep415 | ok | 0.395 | 69.291 | 78.403 |
| 2026-11-11T16:23Z | cf64d7be2df6 | bb16 | gpt | ep474 | ok | 0.540 | 69.831 | 78.403 |
| 2026-11-11T16:34Z | 4fb3617abfe1 | bb16 | gpt | ep415 | ok | 0.343 | 70.174 | 78.403 |
| 2026-11-11T16:41Z | 46f7d45ee738 | bb16 | gpt | ep472 | ok | 0.491 | 70.665 | 78.403 |
| 2026-11-11T16:50Z | 591de34af6d5 | bb16 | gpt | ep411 | ok | 0.420 | 71.085 | 78.403 |
| 2026-11-11T16:50Z | 9073a29241d8 | bb16 | gpt | ep474 | ok | 0.764 | 71.849 | 78.403 |
| 2026-11-11T16:54Z | 90b9780383df | bb16 | gpt | ep411 | ok | 0.327 | 72.176 | 78.403 |
| 2026-11-11T17:07Z | 2884fc96169a | bb16 | gpt | ep415 | ok | 0.372 | 72.548 | 78.403 |
| 2026-11-11T17:13Z | 8de64a6023d4 | bb16 | gpt | ep411 | ok | 0.668 | 73.216 | 78.403 |
| 2026-11-11T17:24Z | 8bc002901f82 | bb16 | gpt | ep476 | ok | 0.468 | 73.684 | 78.403 |
| 2026-11-11T17:26Z | ad6ff8e3bc80 | bb16 | gpt | ep476 | ok | 1.038 | 74.722 | 78.403 |
| 2026-11-11T17:39Z | 6932f10e5a5c | bb16 | gpt | ep474 | ok | 0.881 | 75.603 | 78.403 |
| 2026-11-11T17:41Z | fb8fa636880f | bb16 | gpt | ep472 | ok | 0.385 | 75.988 | 78.403 |
| 2026-11-11T17:47Z | 15debef4127d | bb16 | gpt | ep413 | ok | 0.715 | 76.703 | 78.403 |
| 2026-11-11T17:52Z | 2bf9915858a2 | bb16 | gpt | ep413 | ok | 0.307 | 77.010 | 78.403 |
| 2026-11-11T18:05Z | 2954ca37e57b | bb16 | gpt | ep413 | ok | 0.808 | 77.818 | 78.403 |
| 2026-11-11T18:06Z | 693b522057b1 | bb16 | gpt | ep415 | ok | 0.514 | 78.332 | 78.403 |
| 2026-11-11T18:07Z | 5432e6763c13 | bb16 | gpt | ep474 | ok | 0.399 | 78.731 | 78.403 |
| 2026-11-11T18:25Z | 5086bb5662f3 | bb16 | gpt | ep413 | ok | 0.523 | 79.254 | 78.403 |
| 2026-11-11T18:30Z | 5ab2ff1fb342 | bb16 | gpt | ep472 | ok | 0.740 | 79.994 | 78.403 |
| 2026-11-11T18:33Z | 19480c0694e9 | bb16 | gpt | ep472 | ok | 0.734 | 80.728 | 78.403 |
| 2026-11-11T18:50Z | accf0206823a | bb16 | gpt | ep476 | ok | 0.644 | 81.372 | 78.403 |
| 2026-11-11T19:03Z | 2cbf3801f213 | bb16 | gpt | ep476 | ok | 1.375 | 82.747 | 78.403 |
| 2026-11-12T06:16Z | 1a2e60748088 | open8 (pilot) | luna | ep472 | ok | 0.136 | 82.883 | 78.403 |
| 2026-11-12T06:32Z | aafe30e6b917 | open8 | luna | ep411 | ok | 0.080 | 82.963 | 78.403 |
| 2026-11-12T06:36Z | d5ca2d73574f | open8 | luna | ep474 | ok | 0.126 | 83.089 | 78.403 |
| 2026-11-12T06:40Z | 3074fd6b54a7 | bb8 | luna | ep474 | ok | 0.099 | 83.188 | 78.403 |
| 2026-11-12T06:50Z | 170a4883879a | bb8 | luna | ep474 | ok | 0.095 | 83.283 | 78.403 |
| 2026-11-12T06:50Z | fc08bd7d3e4d | bb8 | luna | ep472 | ok | 0.060 | 83.343 | 78.403 |
| 2026-11-12T06:53Z | dd92406c704d | bb8 | luna | ep413 | ok | 0.056 | 83.399 | 78.403 |
| 2026-11-12T07:01Z | 6eb1a2494353 | open8 | luna | ep476 | ok | 0.061 | 83.460 | 78.403 |
| 2026-11-12T07:07Z | 5a74b25a6ae5 | open8 | luna | ep413 | ok | 0.090 | 83.550 | 78.403 |
| 2026-11-12T07:07Z | e5436084a831 | bb8 | luna | ep413 | ok | 0.062 | 83.612 | 78.403 |
| 2026-11-12T07:24Z | bdbc4557a278 | open8 | luna | ep476 | ok | 0.158 | 83.770 | 78.403 |
| 2026-11-12T07:26Z | b7a765aa6444 | bb8 | luna | ep415 | ok | 0.087 | 83.857 | 78.403 |
| 2026-11-12T07:26Z | 3dade161b74e | open8 | luna | ep411 | ok | 0.101 | 83.958 | 78.403 |
| 2026-11-12T07:42Z | 1d92471fd649 | open8 | luna | ep413 | ok | 0.102 | 84.060 | 78.403 |
| 2026-11-12T07:42Z | fbdc8b2802d9 | open8 | luna | ep472 | ok | 0.113 | 84.173 | 78.403 |
| 2026-11-12T07:44Z | d811befcd40f | open8 | luna | ep415 | ok | 0.103 | 84.276 | 78.403 |
| 2026-11-12T07:50Z | judge (214 calls; results/private_1112/judge/raw) | judge | gpt-6.1-terra x214 | - | ok 214/214 | 1.970 | 86.246 | 78.403 |
| 2026-11-12T07:51Z | f9de33387f54 | bb8 | luna | ep415 | ok | 0.040 | 86.286 | 78.403 |
| 2026-11-12T07:57Z | a0ba410d8d79 | bb8 | luna | ep411 | ok | 0.062 | 86.348 | 78.403 |
| 2026-11-12T08:03Z | 058c5dfce786 | bb8 | luna | ep476 | ok | 0.097 | 86.445 | 78.403 |
| 2026-11-12T08:04Z | cdff161c3af5 | open8 | luna | ep474 | ok | 0.072 | 86.517 | 78.403 |
| 2026-11-12T08:10Z | 747a7939118c | bb8 | luna | ep472 | ok | 0.057 | 86.574 | 78.403 |
| 2026-11-12T08:18Z | 183f5b9aac7a | bb8 | luna | ep411 | ok | 0.036 | 86.610 | 78.403 |
| 2026-11-12T08:20Z | 04f09e6c9989 | bb8 | luna | ep413 | ok | 0.080 | 86.690 | 78.403 |
| 2026-11-12T08:23Z | 5f0611b69ae3 | open8 | luna | ep476 | ok | 0.111 | 86.801 | 78.403 |
| 2026-11-12T08:37Z | 105d53df858a | bb8 | luna | ep415 | ok | 0.064 | 86.865 | 78.403 |
| 2026-11-12T08:38Z | 307993f59d93 | open8 | luna | ep472 | ok | 0.117 | 86.982 | 78.403 |
| 2026-11-12T08:51Z | c4ae7f76c5db | open8 | luna | ep411 | ok | 0.226 | 87.208 | 78.403 |
| 2026-11-12T08:51Z | 6bec56cb1367 | open8 | luna | ep415 | ok | 0.079 | 87.287 | 78.403 |
| 2026-11-12T08:55Z | 0c28a907f741 | open8 | luna | ep476 | ok | 0.100 | 87.387 | 78.403 |
| 2026-11-12T09:10Z | c97ac11305dd | open8 | luna | ep474 | ok | 0.120 | 87.507 | 78.403 |
| 2026-11-12T09:16Z | e9a5478a5321 | bb8 | luna | ep474 | ok | 0.136 | 87.643 | 78.403 |
| 2026-11-12T09:19Z | e91d814988c2 | open8 | luna | ep476 | ok | 0.161 | 87.804 | 78.403 |
| 2026-11-12T09:25Z | d92856577e95 | open8 | luna | ep474 | ok | 0.108 | 87.912 | 78.403 |
| 2026-11-12T09:32Z | 889bb520a836 | bb8 | luna | ep476 | ok | 0.080 | 87.992 | 78.403 |
| 2026-11-12T09:45Z | 5a5d83e129f0 | open8 | luna | ep415 | ok | 0.120 | 88.112 | 78.403 |
| 2026-11-12T09:46Z | 358c75b674b4 | open8 | luna | ep415 | ok | 0.082 | 88.194 | 78.403 |
| 2026-11-12T09:49Z | 51b77d657229 | bb8 | luna | ep472 | ok | 0.154 | 88.348 | 78.403 |
| 2026-11-12T09:57Z | 4047a4793b6c | bb8 | luna | ep413 | ok | 0.051 | 88.399 | 78.403 |
| 2026-11-12T10:04Z | bf434a3433d2 | open8 | luna | ep472 | ok | 0.119 | 88.518 | 78.403 |
| 2026-11-12T10:11Z | e1a574ef4204 | bb8 | luna | ep472 | ok | 0.105 | 88.623 | 78.403 |
| 2026-11-12T10:11Z | 5f699070c6b1 | open8 | luna | ep413 | ok | 0.078 | 88.701 | 78.403 |
| 2026-11-12T10:19Z | 36a57c0b216e | open8 | luna | ep413 | ok | 0.082 | 88.783 | 78.403 |
| 2026-11-12T10:30Z | 90d415ce9d41 | open8 | luna | ep411 | ok | 0.124 | 88.907 | 78.403 |
| 2026-11-12T10:32Z | 9284dc3daded | open8 | luna | ep415 | ok | 0.074 | 88.981 | 78.403 |
| 2026-11-12T10:38Z | 977f4926f5df | open8 | luna | ep472 | ok | 0.185 | 89.166 | 78.403 |
| 2026-11-12T10:47Z | 7a28c3a6a7ac | bb8 | luna | ep411 | ok | 0.069 | 89.235 | 78.403 |
| 2026-11-12T10:52Z | 3b17a6fd9d15 | bb8 | luna | ep476 | ok | 0.122 | 89.357 | 78.403 |
| 2026-11-12T10:57Z | b8b8936f19e3 | bb8 | luna | ep476 | ok | 0.082 | 89.439 | 78.403 |
| 2026-11-12T11:14Z | 081da9afbd2c | open8 | luna | ep413 | ok | 0.101 | 89.540 | 78.403 |
| 2026-11-12T11:15Z | 44b7acddd762 | open8 | luna | ep474 | ok | 0.152 | 89.692 | 78.403 |
| 2026-11-12T11:19Z | 100072279af7 | open8 | luna | ep472 | ok | 0.209 | 89.901 | 78.403 |
| 2026-11-12T11:27Z | c095aca2c51e | open8 | luna | ep472 | ok | 0.079 | 89.980 | 78.403 |
| 2026-11-12T11:31Z | bafd82dade1e | bb8 | luna | ep474 | ok | 0.070 | 90.050 | 78.403 |
| 2026-11-12T11:34Z | 6d1b9c70fd61 | bb8 | luna | ep411 | ok | 0.065 | 90.115 | 78.403 |
| 2026-11-12T11:45Z | f3b7c20ed529 | open8 | luna | ep474 | ok | 0.109 | 90.224 | 78.403 |
| 2026-11-12T11:47Z | 1bf0a5c14342 | open8 | luna | ep413 | ok | 0.095 | 90.319 | 78.403 |
| 2026-11-12T11:50Z | fe6b1a8f2fdb | open8 | luna | ep411 | ok | 0.103 | 90.422 | 78.403 |
| 2026-11-12T11:57Z | 04273e0e4a58 | bb8 | luna | ep415 | ok | 0.054 | 90.476 | 78.403 |
| 2026-11-12T12:03Z | e9e42c0b00e8 | open8 | luna | ep411 | ok | 0.088 | 90.564 | 78.403 |
| 2026-11-12T12:07Z | 6ab46ca3cf7c | open8 | luna | ep476 | ok | 0.104 | 90.668 | 78.403 |
| 2026-11-12T12:14Z | ef28174a51b0 | open8 | luna | ep415 | ok | 0.087 | 90.755 | 78.403 |
| 2026-11-13T07:26Z | gpuplan S0: Step 0 gate (gpuplan/STEP0.md; image check 101/101, substrate gate pass; R6 cancelled: 1 source, checker not clean) | gpuplan | cpu/gpu only | - | ok | 0.000 | 90.755 | 78.403 |
| 2026-11-13T07:26Z | gpuplan X1: scripted policies x budgets x trap ranks (gpuplan/xr_curves.json; scripts/xr_scripted_curves.py) | gpuplan | cpu/gpu only | - | ok | 0.000 | 90.755 | 78.403 |
| 2026-11-13T07:26Z | gpuplan X2: edit-effect SD across base notes (gpuplan/xr_noise.json; scripts/xr_edit_noise.py) | gpuplan | cpu/gpu only | - | ok | 0.000 | 90.755 | 78.403 |
| 2026-11-13T07:26Z | gpuplan X4: one-burst and allocation from logs, 13 agent x arm cells (gpuplan/xr_alloc.json; scripts/xr_alloc.py) | gpuplan | cpu/gpu only | - | ok | 0.000 | 90.755 | 78.403 |
| 2026-11-13T07:26Z | gpuplan C19: judge vs certified leaderboard, L9 tau_b 0.23 (gpuplan/c19_reorder.json; scripts/c19_leaderboard.py) | gpuplan | cpu/gpu only | - | ok | 0.000 | 90.755 | 78.403 |
| 2026-11-13T07:26Z | gpuplan C21: audit-order curves and PPI line (gpuplan/c21_audit.json; scripts/c21_audit.py) | gpuplan | cpu/gpu only | - | ok | 0.000 | 90.755 | 78.403 |
| 2026-11-13T07:43Z | 07975ccc1081 | open4 (pilot) | gpt | ep472 | ok | 0.686 | 91.441 | 78.403 |
| 2026-11-13T08:00Z | gpuplan C8: frozen L0 judge on Luna 60 + Terra 24 re-sent (84 calls; results/private_1112/judge_luna/raw; gpuplan/c8) | judge | gpt-6.1-terra x84 | - | ok 84/84 | 0.665 | 92.106 | 78.403 |
| 2026-11-13T08:15Z | 0fd2915bdbfc | open4 (pilot) | luna | ep472 | ok | 0.193 | 92.299 | 78.403 |
| 2026-11-13T08:25Z | 9ddc6d011d4c | open8 (pilot) | luna | ep801 | ok | 0.049 | 92.348 | 78.403 |
| 2026-11-13T08:36Z | 1e558a7628c9 | open8 (pilot) | luna | ep802 | ok | 0.139 | 92.487 | 78.403 |
| 2026-11-13T08:52Z | 72facb01d194 | open8 | gpt | ep415 | ok | 0.560 | 93.047 | 78.403 |
| 2026-11-13T08:58Z | 7016eb8b7478 | open8 | gpt | ep801 | ok | 0.757 | 93.804 | 78.403 |
| 2026-11-13T09:01Z | 654f3fc3a899 | open8 | gpt | ep802 | ok | 0.775 | 94.579 | 78.403 |
| 2026-11-13T09:13Z | 251a1c557786 | open8 | gpt | ep411 | ok | 0.537 | 95.116 | 78.403 |
| 2026-11-13T09:18Z | dfd59fcba69f | open8 | gpt | ep413 | ok | 1.037 | 96.153 | 78.403 |
| 2026-11-13T09:23Z | 66cf5c41f212 | open8 | gpt | ep802 | ok | 0.835 | 96.988 | 78.403 |
| 2026-11-13T09:30Z | 181d5cfa1ac3 | open8 | gpt | ep801 | ok | 0.659 | 97.647 | 78.403 |
| 2026-11-13T09:33Z | 689047b5cca9 | open8 | gpt | ep801 | ok | 0.581 | 98.228 | 78.403 |
| 2026-11-13T09:47Z | d843fd21ca63 | open8 | gpt | ep802 | ok | 0.944 | 99.172 | 78.403 |
| 2026-11-13T09:48Z | 2eec974c6d05 | open8 | gpt | ep802 | ok | 0.585 | 99.757 | 78.403 |
| 2026-11-13T09:49Z | none-c14_gpt-o12a1 | open8 | gpt | ep801 | infra:no_container (runner_exit_1) | 0.000 | 99.757 | 78.403 |
| 2026-11-13T09:50Z | 2705d5f46142 | open8 | gpt | ep801 | ok | 0.716 | 100.473 | 78.403 |
| 2026-11-13T10:04Z | bebb41a44543 | open8 | gpt | ep802 | ok | 0.520 | 100.993 | 78.403 |
| 2026-11-13T10:21Z | b7f67a91ca91 | open8 | gpt | ep801 | ok | 1.247 | 102.240 | 78.403 |
| 2026-11-13T10:22Z | none-open4_gpt-o1a1 | open4 | gpt | ep474 | infra:no_container (runner_exit_1) | 0.000 | 102.240 | 78.403 |
| 2026-11-13T10:23Z | none-open4_gpt-o2a1 | open4 | gpt | ep474 | infra:no_container (runner_exit_1) | 0.000 | 102.240 | 78.403 |
| 2026-11-13T10:39Z | f7de6c21160b | open4 | gpt | ep472 | ok | 0.590 | 102.830 | 78.403 |
| 2026-11-13T10:45Z | b139d663a0d0 | open4 | gpt | ep411 | ok | 0.733 | 103.563 | 78.403 |
| 2026-11-13T10:46Z | 0314870c2fa3 | open4 | gpt | ep413 | ok | 0.832 | 104.395 | 78.403 |
| 2026-11-13T10:55Z | f35d436707ae | open4 | gpt | ep476 | ok | 0.598 | 104.993 | 78.403 |
| 2026-11-13T11:05Z | 464971dfe65c | open4 | gpt | ep415 | ok | 0.749 | 105.742 | 78.403 |
| 2026-11-13T11:07Z | 14d394b5ee82 | open4 | gpt | ep415 | ok | 0.749 | 106.491 | 78.403 |
| 2026-11-13T11:09Z | b39873953a68 | open4 | gpt | ep472 | ok | 0.544 | 107.035 | 78.403 |
| 2026-11-13T11:23Z | a1941090735f | open4 | gpt | ep411 | ok | 0.498 | 107.533 | 78.403 |
| 2026-11-13T11:23Z | ace726fc7bcd | open4 | gpt | ep413 | ok | 0.670 | 108.203 | 78.403 |
| 2026-11-13T11:27Z | 767e0d44346d | open4 | gpt | ep476 | ok | 0.589 | 108.792 | 78.403 |
| 2026-11-13T11:38Z | ebc8e4da6935 | open4 | gpt | ep474 | ok | 0.592 | 109.384 | 78.403 |
| 2026-11-13T11:44Z | 5cdcc8496b2e | open4 | gpt | ep474 | ok | 0.774 | 110.158 | 78.403 |
| 2026-11-13T12:02Z | 8e74c5c9ad63 | open8 | luna | ep801 | ok | 0.103 | 110.261 | 78.403 |
| 2026-11-13T12:04Z | 98bf684a7817 | open8 | luna | ep802 | ok | 0.105 | 110.366 | 78.403 |
| 2026-11-13T12:07Z | 4e6af31e71ca | open8 | luna | ep801 | ok | 0.116 | 110.482 | 78.403 |
| 2026-11-13T12:23Z | 8584927c01cd | open8 | luna | ep802 | ok | 0.096 | 110.578 | 78.403 |
| 2026-11-13T12:28Z | 7491783aac79 | open8 | luna | ep802 | ok | 0.133 | 110.711 | 78.403 |
| 2026-11-13T12:28Z | 9f43162c766c | open8 | luna | ep801 | ok | 0.127 | 110.838 | 78.403 |
| 2026-11-13T12:38Z | ca34c0141593 | open8 | luna | ep802 | ok | 0.098 | 110.936 | 78.403 |
| 2026-11-13T12:42Z | ebd4fa982c94 | open8 | luna | ep801 | ok | 0.091 | 111.027 | 78.403 |
| 2026-11-13T12:50Z | 5c70d307e1c7 | open8 | luna | ep801 | ok | 0.137 | 111.164 | 78.403 |
| 2026-11-13T12:51Z | cfd11cf81b47 | open8 | luna | ep802 | ok | 0.083 | 111.247 | 78.403 |
| 2026-11-13T12:53Z | none-open4_luna-o1a1 | open4 | luna | ep474 | infra:no_container (runner_exit_1) | 0.000 | 111.247 | 78.403 |
| 2026-11-13T12:54Z | none-open4_luna-o2a1 | open4 | luna | ep413 | infra:no_container (runner_exit_1) | 0.000 | 111.247 | 78.403 |
| 2026-11-13T13:11Z | f393714787da | open4 | luna | ep415 | ok | 0.081 | 111.328 | 78.403 |
| 2026-11-13T13:16Z | 12470244ec90 | open4 | luna | ep472 | ok | 0.154 | 111.482 | 78.403 |
| 2026-11-13T13:23Z | eb737fb3f128 | open4 | luna | ep411 | ok | 0.063 | 111.545 | 78.403 |
| 2026-11-13T13:27Z | 4eddcb3c1db5 | open4 | luna | ep413 | ok | 0.056 | 111.601 | 78.403 |
| 2026-11-13T13:32Z | 6ff7c0bb19cf | open4 | luna | ep476 | ok | 0.234 | 111.835 | 78.403 |
| 2026-11-13T13:51Z | 9a9b628e690f | open4 | luna | ep411 | ok | 0.104 | 111.939 | 78.403 |
| 2026-11-13T13:52Z | e2d438a51c68 | open4 | luna | ep415 | ok | 0.138 | 112.077 | 78.403 |
| 2026-11-13T14:06Z | b3d100b3d3f2 | open4 | luna | ep474 | ok | 0.078 | 112.155 | 78.403 |
| 2026-11-13T14:07Z | 4cfa91e9e0db | open4 | luna | ep476 | ok | 0.256 | 112.411 | 78.403 |
| 2026-11-13T14:07Z | f0045a8b10c0 | open4 | luna | ep472 | ok | 0.080 | 112.491 | 78.403 |
| 2026-11-13T14:25Z | 56fc0a4dcaf4 | open4 | luna | ep413 | ok | 0.107 | 112.598 | 78.403 |
| 2026-11-13T14:27Z | d176c1b44788 | open4 | luna | ep474 | ok | 0.152 | 112.750 | 78.403 |
| 2026-11-13T14:46Z | 618a19daaaa0 | open8 | gpt | ep801 | ok | 0.566 | 113.316 | 78.403 |
| 2026-11-13T14:50Z | 5883255492d1 | open8 | gpt | ep802 | ok | 0.851 | 114.167 | 78.403 |
| 2026-11-13T14:50Z | 98c9b0fc641a | open8 | gpt | ep802 | ok | 0.746 | 114.913 | 78.403 |
| 2026-11-13T15:02Z | 5a7684990f1a | open8 | gpt | ep801 | ok | 0.545 | 115.458 | 78.403 |
| 2026-11-13T17:07Z | gpuplan C6: judge evidence ladder, set A 132 runs x L0r/L1/L1r (Terra) + H0/H1/H1r (Haiku), Luna L1 (852 calls, 850 ok, 2 http_503 not re-sent; results/private_1112/judge_ladder/raw; gpuplan/c6); Haiku spend 0.645 in cum_anthropic | judge | gpt-6.1-terra x456, claude-haiku-5-5 x396 | - | ok 850/852 | 6.137 | 121.595 | 79.048 |
| 2026-11-13T17:07Z | gpuplan X3: Terra Open-4, 12 counted runs (spend in the run rows above; gpuplan/open4) | gpuplan | runs | - | ok | 0.000 | 121.595 | 79.048 |
| 2026-11-13T17:07Z | gpuplan X3b: Luna Open-4, 12 counted runs (spend in the run rows above; gpuplan/open4) | gpuplan | runs | - | ok | 0.000 | 121.595 | 79.048 |
| 2026-11-13T17:07Z | gpuplan C14: Terra 13 + stage 2 4 runs, Luna 10 runs on image r1114c (spend in the run rows above; gpuplan/c14) | gpuplan | runs | - | ok | 0.000 | 121.595 | 79.048 |
| 2026-11-13T17:20Z | gpuplan C14 H5: frozen L0 judge on the 27 counted C14 runs (results/private_1112/judge_c14/raw; gpuplan/c14/judge.json) | judge | gpt-6.1-terra x27 | - | ok 27/27 | 0.239 | 121.834 | 79.048 |
| 2026-11-13T17:32Z | gpuplan C12 lean: frozen judge on scripted answers with no report, P0/P7/P1/P6, shipped x2 + 27 bank episodes (204 calls; results/private_1112/judge_cheaters/raw; gpuplan/c12); Haiku 0.062 in cum_anthropic | judge | gpt-6.1-terra x102, claude-haiku-5-5 x102 | - | ok 204/204 | 0.546 | 122.380 | 79.110 |
