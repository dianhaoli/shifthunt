# Polish round 2: bounds on GPT-only (and Haiku-only) judge-implied Block 1 hard-slot rates.
# Inputs: committed marginals in judge.json at 1b7468b (copy: paperloop/chk_c8/judge_1b7468b.json):
# hard_by_agent, hard_by_access, hard_by_population; certified per-cell hard-slot counts from
# rows_r1112.csv (Block 1, 'identified') and Table 2 / Appendix C (main, harder variant).
# Per-slot verdicts are private, so we enumerate every integer split consistent with the marginals.
import itertools, json
J=json.load(open('/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/paperloop/chk_c8/judge_1b7468b.json'))
def fr(s): a,b=s.split('/'); return int(a),int(b)
# certified (passes, fails) per cell, hard slot
cert={('b1','gpt','bb8'):(8,16),('b1','gpt','open8'):(23,1),('b1','gpt','bb64'):(24,0),
      ('b1','haiku','bb8'):(3,9),('b1','haiku','open8'):(5,7),('b1','haiku','bb64'):(8,4),
      ('bb16','gpt','bb16'):(18,6),
      ('main','gpt','open'):(14,2),('main','haiku','open'):(8,8),('main','opus','open'):(11,5),('main','sonnet','open'):(12,4),
      ('hv','gpt','open'):(7,1),('hv','haiku','open'):(1,2),('hv','opus','open'):(3,1),('hv','sonnet','open'):(1,2)}
# sanity vs judge.json marginals
def agg(keyf):
    out={}
    for k,(p,f) in cert.items():
        g=keyf(k); a=out.setdefault(g,[0,0]); a[0]+=p; a[1]+=f
    return out
print('cert by agent',agg(lambda k:k[1])); print('cert by access',agg(lambda k:k[2]))
cells=list(cert)
# marginal constraints: (group function, group value, FC, FB)
cons=[]
for a,v in J['hard_by_agent'].items(): cons.append((lambda k,a=a:k[1]==a, fr(v['false_credit'])[0], fr(v['false_blame'])[0]))
amap={'blackbox_bb8':'bb8','blackbox_bb64':'bb64','blackbox_bb16':'bb16','open_open8':'open8','open':'open'}
for a,v in J['hard_by_access'].items(): cons.append((lambda k,a=amap[a]:k[2]==a, fr(v['false_credit'])[0], fr(v['false_blame'])[0]))
pmap={'block1':'b1','bb16':'bb16','main':'main','harder_variant':'hv'}
for a,v in J['hard_by_population'].items(): cons.append((lambda k,a=pmap[a]:k[0]==a, fr(v['false_credit'])[0], fr(v['false_blame'])[0]))
# FC and FB are separable problems. Enumerate each with simple backtracking.
def solve(idx):  # idx 1 = fails (FC), 0 = passes (FB)
    tgt=[c[1+idx] if False else (c[1] if idx==1 else c[2]) for c in cons]
    sols=[]; x={}
    order=cells
    def rec(i):
        # prune: partial sums cannot exceed targets; remaining capacity must reach targets
        for (f,_,_),t in zip(cons,tgt):
            s=sum(x[k] for k in x if f(k)); cap=sum(cert[k][idx] for k in order[i:] if f(k))
            if s>t or s+cap<t: return
        if i==len(order): sols.append(dict(x)); return
        k=order[i]
        for v in range(cert[k][idx]+1):
            x[k]=v; rec(i+1)
        del x[k]
    # passes index is 0 in cert tuple, fails index 1
    rec(0); return sols
FC=solve(1); FB=solve(0)
print('feasible FC splits',len(FC),'FB splits',len(FB))
def implied(agent,arm,fc,fb):
    p,f=cert[('b1',agent,arm)]; return p-fb[('b1',agent,arm)]+fc[('b1',agent,arm)]
res={}
for agent,n in [('gpt',24),('haiku',12)]:
    vals=set()
    for fc in FC:
        for fb in FB:
            b8=implied(agent,'bb8',fc,fb); o8=implied(agent,'open8',fc,fb); b64=implied(agent,'bb64',fc,fb)
            vals.add((b8,o8,b64))
    bud=[(b64-b8)/n for b8,o8,b64 in vals]; prox=[(o8-b8)/n for b8,o8,b64 in vals]; d=[(b64-o8)/n for b8,o8,b64 in vals]
    c=[cert[('b1',agent,a)][0] for a in ('bb8','open8','bb64')]
    print(agent,'certified bb8/open8/bb64',c,'budget',round((c[2]-c[0])/n,3),'proxy',round((c[1]-c[0])/n,3),'bb64-open8',round((c[2]-c[1])/n,3))
    print('  judge-implied ranges: bb8',min(v[0] for v in vals),max(v[0] for v in vals),'open8',min(v[1] for v in vals),max(v[1] for v in vals),'bb64',min(v[2] for v in vals),max(v[2] for v in vals))
    print('  budget effect',round(min(bud),3),round(max(bud),3),' proxy effect',round(min(prox),3),round(max(prox),3),' bb64-open8',round(min(d),3),round(max(d),3))
    print('  share of feasible combos with bb64-open8<0:', round(sum(x<0 for x in d)/len(d),3))
