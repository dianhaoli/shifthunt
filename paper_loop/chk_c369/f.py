import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/paperloop/ledger/calc')
from stats_lib import fisher2 as F, fisher_one as F1
from math import comb
def T(k,n,k2,n2): return F(k,n-k,k2,n2-k2)
print('203/207 vs 156/163', T(203,207,156,163))
print('mixed table: GPT',T(23,24,16,96),'Opus',T(6,9,1,38),'Sonnet',T(6,11,2,37),'Haiku',T(5,16,7,70))
print('main+O8: GPT',T(17,18,16,96),'Opus',T(4,7,1,38),'Sonnet',T(5,8,2,37),'Haiku',T(5,14,7,70))
print('GPT 23/24 vs 5/88',T(23,24,5,88))
print('Haiku width 5/16 vs 12/20',T(5,16,12,20),' 5/14 vs 9/15', T(5,14,9,15))
print('trap pass 3/14 vs 12/16',T(3,14,12,16),' 3/8 vs 12/16',T(3,8,12,16), '3/16 vs 15/21',T(3,16,15,21))
print('GPT vs Claude 23/24 vs 17/36',T(23,24,17,36))
print('commission',T(1,98,24,75),' per slot',T(1,108,24,108))
print('omission 10/108 vs 33/108',T(10,108,33,108))
def s2(k,n): return min(1,2*sum(comb(n,i) for i in range(k+1))/2**n)
# adversarial placements: trap runs 24, 23 isolated, 1 not; 5 ordinary isolations, each run has 2 ordinary probes
best=0
for a in range(0,3):  # isolations placed in the non-isolating trap run (makes it 'against' if >=1)
  for rest in range(0,6-a):  # isolations placed into isolating trap runs (each neutralizes 1 run if one per run)
    if a+rest>5: continue
    fav=23-rest; ag=1 if a>=1 else 0
    p=s2(min(fav,ag),fav+ag); best=max(best,p); 
print('max sign p',best, s2(1,20), s2(0,18))
