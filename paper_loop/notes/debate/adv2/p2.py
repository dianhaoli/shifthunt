import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/debate/stat')
from power import power, p_bound
for ns in [(8,8),(9,9),(6,6)]:
  for p0 in [(0.0,0.2),(0.1,0.25),(0.2,0.35)]:
    out=[]
    for p1 in [(0.9,0.9),(p0[0]+.3,p0[1]+.3),(p0[0]+.5,p0[1]+.5)]:
      out.append(round(power(ns,p1,p0),2))
    out.append(round(p_bound(ns,p0,p0),2)); out.append(round(p_bound(ns,(p0[0]+.1,p0[1]+.1),p0),2))
    print(ns,p0,'pow ceil.9, +.3, +.5 | P(UB<.3|null), P(UB<.3|+.1):',out)
