import pickle, math, statistics, itertools
keys,cells,fc,fb=pickle.load(open('sols.pkl','rb')); idx={k:i for i,k in enumerate(keys)}
def taub(x,y):
    c=d=tx=ty=0
    for i in range(len(x)):
        for j in range(i+1,len(x)):
            a=(x[i]>x[j])-(x[i]<x[j]); b=(y[i]>y[j])-(y[i]<y[j])
            if a==0 and b==0: continue
            if a==0: tx+=1; continue
            if b==0: ty+=1; continue
            c+= a==b; d+= a!=b
    den=math.sqrt((c+d+tx)*(c+d+ty)); return (c-d)/den
def jc(c,f,b): return cells[c][0]-b[idx[c]]+f[idx[c]]
L9={'Terra-open':[('main','gpt','open'),('block1','gpt','open8')],'Opus-open':[('main','opus','open')],'Sonnet-open':[('main','sonnet','open')],
    'Haiku-open':[('main','haiku','open'),('block1','haiku','open8')],'Terra-BB8':[('block1','gpt','bb8')],'Terra-BB16':[('bb16','gpt','bb16')],
    'Terra-BB64':[('block1','gpt','bb64')],'Haiku-BB8':[('block1','haiku','bb8')],'Haiku-BB64':[('block1','haiku','bb64')]}
L11={'Terra-main':[('main','gpt','open')],'Opus-main':[('main','opus','open')],'Sonnet-main':[('main','sonnet','open')],'Haiku-main':[('main','haiku','open')],
     'Terra-O8':[('block1','gpt','open8')],'Terra-BB8':[('block1','gpt','bb8')],'Terra-BB16':[('bb16','gpt','bb16')],'Terra-BB64':[('block1','gpt','bb64')],
     'Haiku-O8':[('block1','haiku','open8')],'Haiku-BB8':[('block1','haiku','bb8')],'Haiku-BB64':[('block1','haiku','bb64')]}
MAIN={k:v for k,v in L11.items() if k.endswith('-main')}
B1={k:v for k,v in L11.items() if k in ('Terra-O8','Terra-BB8','Terra-BB64','Haiku-O8','Haiku-BB8','Haiku-BB64')}
cost={'Terra-open':(10.57+16.27)/40,'Opus-open':3.72,'Sonnet-open':3.09,'Haiku-open':(16.29+11.91)/28,'Terra-BB8':23.19/24,'Terra-BB16':14.19/24,'Terra-BB64':8.93/24,'Haiku-BB8':14.81/12,'Haiku-BB64':10.26/12}
def frontier(rate):
    S=list(rate); fr=[]
    for s in S:
        dom=any((cost[t]<=cost[s] and rate[t]>=rate[s]) and (cost[t]<cost[s] or rate[t]>rate[s]) for t in S if t!=s)
        if not dom: fr.append(s)
    return tuple(sorted(fr,key=lambda s:cost[s]))
for name,L in (('L9',L9),('L11',L11),('MAIN',MAIN),('B1',B1)):
    n={s:sum(sum(cells[c]) for c in cs) for s,cs in L.items()}
    cert={s:sum(cells[c][0] for c in cs)/n[s] for s,cs in L.items()}
    S=list(L); taus=[]; rng={s:[9,-9] for s in S}; rev=__import__('collections').Counter(); fronts=__import__('collections').Counter()
    for f in fc:
        for b in fb:
            j={s:sum(jc(c,f,b) for c in cs)/n[s] for s,cs in L.items()}
            for s in S: rng[s][0]=min(rng[s][0],j[s]); rng[s][1]=max(rng[s][1],j[s])
            taus.append(taub([cert[s] for s in S],[j[s] for s in S]))
            for a,bb in itertools.combinations(S,2):
                if (cert[a]-cert[bb])*(j[a]-j[bb])<0: rev[(a,bb)]+=1
            if name=='L9': fronts[frontier(j)]+=1
    N=len(taus)
    print(f'== {name}: {len(S)} systems, joint splits {N}')
    print(' certified:', {s:f'{round(cert[s]*n[s])}/{n[s]}={cert[s]:.3f}' for s in S})
    print(' judge-implied ranges:', {s:f'{round(a*n[s])}-{round(b*n[s])}/{n[s]}' for s,(a,b) in rng.items()})
    print(f' tau-b range {min(taus):.3f} .. {max(taus):.3f}; median {statistics.median(taus):.3f}; share <0.467 {sum(t<0.467 for t in taus)/N:.2f}')
    print(' pairs reversed in ALL splits:', [p for p,c in rev.items() if c==N])
    print(' pairs reversed in some split:', len(rev), 'of', len(S)*(len(S)-1)//2)
    if name=='L9':
        print(' certified frontier', frontier(cert))
        for fr,c in fronts.most_common(8): print('  judge frontier', fr, round(c/N,3))
# Terra-Haiku gaps
gm=[];gb=[];gmb=[]
for f in fc:
    for b in fb:
        tm=jc(('main','gpt','open'),f,b); hm=jc(('main','haiku','open'),f,b)
        tb=sum(jc(('block1','gpt',a),f,b) for a in ('open8','bb8','bb64')); hb=sum(jc(('block1','haiku',a),f,b) for a in ('open8','bb8','bb64'))
        gm.append((tm-hm)/16); gb.append(tb/72-hb/36); gmb.append((tm+tb)/88-(hm+hb)/52)
print('Terra-Haiku gap main: cert', 6/16, 'judge range', min(gm), max(gm))
print('Terra-Haiku gap B1: cert', round(55/72-16/36,3), 'judge range', round(min(gb),3), round(max(gb),3))
print('Terra-Haiku gap main+B1: cert', round(69/88-24/52,3), 'judge range', round(min(gmb),3), round(max(gmb),3))
