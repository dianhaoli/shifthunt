pool: 32 valid of 36 (Counter({'planted': 20, 'null': 12}))

## mode=episodes (100 episodes)
| policy | episode pass | planted pass | null pass | buckets | probe_query texts |
|---|---|---|---|---|---|
| sel_naive_draw0 | 1.00 | 1.00 | 1.00 | {} | 0 |
| sel_careful | 1.00 | 1.00 | 1.00 | {} | 0 |
| sel_interp | 0.77 | 0.88 | 1.00 | {'removal_short': 23} | 0 |
| sel_interp_var | 1.00 | 1.00 | 1.00 | {} | 0 |

## mode=slots (32 episodes)
| policy | episode pass | planted pass | null pass | buckets | probe_query texts |
|---|---|---|---|---|---|
| sel_naive_draw0 | 1.00 | 1.00 | 1.00 | {} | 0 |
| sel_careful | 1.00 | 1.00 | 1.00 | {} | 0 |
| sel_interp | 0.94 | 0.90 | 1.00 | {'removal_short': 2} | 0 |
| sel_interp_var | 1.00 | 1.00 | 1.00 | {} | 0 |

## (e) per planted probe: careful / naive(4 pairs, 8 draws) / interp
| probe | class | tau | careful rem/kept/pass | naive rem/kept/pass-rate | interp rem/kept/pass (dropped) | interp_var rem/kept/pass (dropped) |
|---|---|---|---|---|---|---|
| build_screen/planted_000 | planted | 0.309 | 0.517/0.985/1 | 0.504/0.983/1.00 | 0.517/0.985/1 (0) | 0.496/0.992/1 (3) |
| build_screen/planted_001 | planted | 0.159 | 0.264/1.002/1 | 0.253/1.002/1.00 | 0.262/1.002/1 (1) | 0.255/1.003/1 (1) |
| build_screen/planted_002 | planted | 0.158 | 0.263/0.989/1 | 0.258/0.989/1.00 | 0.259/0.994/1 (2) | 0.258/0.999/1 (2) |
| build_screen/planted_003 | planted | 0.332 | 0.554/0.981/1 | 0.553/0.981/1.00 | 0.551/0.982/1 (1) | 0.552/0.981/1 (1) |
| build_screen/planted_004 | planted | 0.227 | 0.386/1.010/1 | 0.382/1.005/1.00 | 0.386/1.010/1 (0) | 0.386/1.006/1 (1) |
| build_screen/planted_005 | planted | 0.228 | 0.378/0.982/1 | 0.368/0.985/1.00 | 0.377/0.985/1 (1) | 0.374/0.987/1 (2) |
| build_screen/planted_007 | planted | 0.249 | 0.416/1.004/1 | 0.412/1.002/1.00 | 0.416/1.004/1 (0) | 0.416/1.004/1 (0) |
| build_screen/planted_009 | planted | 0.358 | 0.598/0.961/1 | 0.596/0.965/1.00 | 0.195/0.981/0 (4) | 0.598/0.996/1 (10) |
| build_screen2/planted_001 | planted | 0.253 | 0.421/0.979/1 | 0.414/0.969/1.00 | 0.336/0.982/1 (3) | 0.310/0.983/1 (11) |
| build_screen2/planted_002 | planted | 0.223 | 0.370/1.001/1 | 0.366/0.990/1.00 | 0.370/1.001/1 (0) | 0.370/1.001/1 (0) |
| build_screen2/planted_003 | planted | 0.187 | 0.313/0.953/1 | 0.304/0.967/1.00 | 0.306/0.960/1 (1) | 0.297/0.998/1 (5) |
| build_screen2/planted_004 | planted | 0.236 | 0.385/0.992/1 | 0.384/0.994/1.00 | 0.385/0.990/1 (1) | 0.391/0.996/1 (2) |
| build_screen2/planted_005 | planted | 0.388 | 0.648/0.906/1 | 0.645/0.939/1.00 | 0.250/1.007/0 (5) | 0.636/0.979/1 (7) |
| build_screen2/planted_006 | planted | 0.183 | 0.305/0.883/1 | 0.301/0.883/1.00 | 0.294/0.996/1 (2) | 0.298/0.994/1 (1) |
| build_screen2/planted_007 | planted | 0.307 | 0.507/0.959/1 | 0.497/0.963/1.00 | 0.509/0.959/1 (1) | 0.505/0.978/1 (3) |
| build_screen2/planted_008 | planted | 0.208 | 0.345/0.989/1 | 0.351/0.983/1.00 | 0.341/0.989/1 (1) | 0.334/0.996/1 (2) |
| build_screen2/planted_009 | planted | 0.232 | 0.387/0.989/1 | 0.387/0.985/1.00 | 0.389/0.977/1 (1) | 0.369/1.004/1 (2) |
| build_screen2/planted_010 | planted | 0.292 | 0.485/0.872/1 | 0.483/0.891/1.00 | 0.417/0.975/1 (4) | 0.476/0.991/1 (3) |
| build_screen2/planted_012 | planted | 0.150 | 0.229/0.986/1 | 0.219/0.987/1.00 | 0.225/1.000/1 (1) | 0.225/1.000/1 (1) |
| build_screen2/planted_013 | planted | 0.187 | 0.311/0.983/1 | 0.301/0.982/1.00 | 0.274/0.992/1 (4) | 0.311/0.990/1 (1) |
